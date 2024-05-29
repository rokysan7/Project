import openai
import os
from datetime import datetime
import streamlit as st
from utils import print_messages, StreamHandler
from langchain_core.messages import ChatMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models.ollama import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
import os
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

PROMPT_TEMPLATE = """
Role:
너는 심리 상담을 해주는 행복 AI이다.

Instructions:
- 답변은 항상 한글로 작성해야함.
- 상황과 감정에 공감하는 표현을 하고, 최대한 짧게 대답해야함.
- 애매한 내용은 질문하여 고민의 문제를 명확해야 하며 질문은 핵심적인 질문 하나를 선정하여 개방적인 질문을 해야함.
- 고민이 명확해지면 사용자가 공유한 고민을 요약 및 정리를 해줘야함.

Context:
- 대화의 맥락: 너는 처음에는 내담자의 감정을 파악하여 공감적인 대화를 5회 이상 지속해야함.
- 개입 시기: 공감을 충분히 했고 고민의 내용이 파악되었다면 심리적 개입을 사용자가 기분상하지 않게 실시함.

Question:
{question}
"""

# OpenAI API 키 설정
openai.api_key = st.secrets["general"]["openai_api_key"]

# 로그 파일 경로 설정
LOG_FILE_PATH = 'chat_logs/'

# 로그 파일을 관리하는 함수
def manage_log_file(session_id):
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f'{LOG_FILE_PATH}{session_id}_{today}.txt'
    
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as file:
            conversation = file.read()
    else:
        conversation = ""
    
    return log_file, conversation

# 대화 내용을 파일에 저장하는 함수
def save_conversation(log_file, conversation):
    with open(log_file, 'w', encoding='utf-8') as file:
        file.write(conversation)

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_id: str):
    if session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = []
    return st.session_state["store"][session_id]

# 기존 대화 내용을 불러오는 함수
def load_conversation(session_id: str):
    log_file, conversation = manage_log_file(session_id)
    if conversation:
        conversation_lines = conversation.strip().split('\n')
        for line in conversation_lines:
            if line.startswith("User:"):
                st.session_state["messages"].append({"role": "user", "content": line[len("User: "):]})
            elif line.startswith("AI:"):
                st.session_state["messages"].append({"role": "assistant", "content": line[len("AI: "):]})

# Streamlit 애플리케이션 설정
st.set_page_config(page_title="Happy bot", page_icon="😃")
st.title("Happy AI")
st.info("Test alpha ver 1.0")

# 대화기록이 없으면 리스트 생성
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 채팅 대화기록을 저장하는 store 세션 상태 변수
if "store" not in st.session_state:
    st.session_state["store"] = dict()

with st.sidebar:
    session_id = st.text_input("Session ID", value="w001")

    clear_btn = st.button("대화기록 초기화")
    if clear_btn:
        st.session_state["messages"] = []
        st.session_state["store"] = dict()
        st.rerun()

# 기존 대화 내용 불러오기
load_conversation(session_id)

# 메시지 출력 함수
def print_messages():
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.chat_message("human").write(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("ai").write(message["content"])

print_messages()

if user_input := st.chat_input("메시지를 입력해주세요."):
    st.chat_message("human").write(f"{user_input}")
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    with st.chat_message("ai"):
        prompt = [{"role": "system", "content": "You are a helpful assistant."}]
        history = get_session_history(session_id)
        
        for message in history:
            prompt.append(message)
        
        prompt.append({"role": "user", "content": user_input})
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-2024-05-13",
            messages=prompt
        )
        
        ai_response = response.choices[0].message['content']
        st.session_state["messages"].append({"role": "assistant", "content": ai_response})
        st.write(ai_response)

    # 대화 내용을 로그 파일에 저장
    conversation = ""
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            conversation += f"User: {message['content']}\n"
        elif message["role"] == "assistant":
            conversation += f"AI: {message['content']}\n"
    log_file, _ = manage_log_file(session_id)
    save_conversation(log_file, conversation)

'''
    ver1.0:
    1. 다이얼로그 형식의 챗봇 생성
    2. 아이디 입력에 따른 로그파일 생성 확인
    
    개선점:
    1. 로그 로드에 문제가 아주 많음
        1-1. 한번 대화를 입력할 때 마다 모든 로그파일을 다시 불러들임(무한 저장)
        1-2. 아이디를 바꿔서 대화를 시작하면 새로운 창으로 시작하는것이 아닌 기존 대화를 새로운 아이디로 저장해서 불러들임
            ex) w1 아이디로 대화 함 -> w2 아이디로 새로 대화 하려하면 w1의 내용을 그대로 다 저장함
    
    2. 앱을 실행할 때는 초기화가 되어있고(빈 대화내용), 아이디 입력후 로그파일을 불러와야 기존 대화를 불러와야 하는데 그게아님,
      그냥 불러들임

    3. prompt template을 따르지 아니함.
        3-1. 문제는 app.py는 ChatPromptTemplate.from_messages() 모듈을 사용하고 있지만, 1.0버전은 openai.ChatCompletion.create()
        버전을 사용하고 있기에 prompt template을 불러오는 구간이 없음
'''    