import streamlit as st
import openai
import os
from datetime import datetime
#from dotenv import load_dotenv

#load_dotenv()

# API 키 설정
# openai.api_key = os.getenv('OPENAI_API_KEY')

openai.api_key = st.secrets['general']['openai_api_key']

# Log 파일 path
LOG_FILE_PATH = 'chat_logs/'

# log file manage
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

# conversation 저장 함수
def save_conversation(log_file, messages):
    conversation = ""
    for message in messages:
        if message["role"] == "user":
            conversation += f"User: {message['content']}\n"
        elif message["role"] == "assistant":
            conversation += f"AI: {message['content']}\n"
    with open(log_file, 'w', encoding='utf-8') as file:
        file.write(conversation)

# Session ID 기록을 가져오는 함수
def get_session_history(session_id: str):
    if session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = []
    return st.session_state["store"][session_id]

# 기존 대화 불러오기 함수
def load_conversation(session_id: str):
    log_file, conversation = manage_log_file(session_id)
    messages = []
    if conversation:
        conversation_lines = conversation.strip().split('\n')
        for line in conversation_lines:
            if line.startswith("User:"):
                messages.append({"role": "user", "content": line[len("User: "):]})
            elif line.startswith("AI:"):
                messages.append({"role": "assistant", "content": line[len("AI: "):]})
    
    return messages

# PROMPT_TEMPLATE 설정
PROMPT_TEMPLATE = """
Role:
너는 심리 상담을 해주는 행복 AI이다.

Instructions:
- 답변은 항상 한글로 작성해야함.
- 상황과 감정에 공감하는 표현을 하고, 최대한 짧게 대답해야함.
- 애매한 내용은 질문하여 고민의 문제를 명확하게 해야 하며, 질문은 핵심적인 질문 하나를 선정하여 개방적인 질문을 해야함.
- 고민이 명확해지면 사용자가 공유한 고민을 요약 및 정리해줘야함.

Context:
- 대화의 맥락: 너는 처음에는 내담자의 감정을 파악하여 공감적인 대화를 5회 이상 지속해야함.
- 개입 시기: 공감을 충분히 했고 고민의 내용이 파악되었다면 심리적 개입을 사용자가 기분 상하지 않게 실시함.

Question:
{question}
"""

# Streamlit Setting
st.set_page_config(page_title="메칸더 B", page_icon="😃")
st.title("심리치료 AI")
st.info("Test alpha ver 1.2")

# message 초기화로 시작
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 대화 기록 저장하는 store session 생성
if "store" not in st.session_state:
    st.session_state["store"] = dict()

with st.sidebar:
    session_id = st.text_input("Session ID", value="user0001")

    load_btn = st.button("이전대화 불러오기")
    if load_btn:
        st.session_state["messages"] = load_conversation(session_id)
        st.session_state["store"][session_id] = st.session_state["messages"]

    clear_btn = st.button("대화기록 지우기")
    if clear_btn:
        st.session_state["messages"] = []
        if session_id in st.session_state["store"]:
            del st.session_state["store"][session_id]
        st.rerun()

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
        history = get_session_history(session_id)

        # PROMPT TEMPLETE 적용
        prompt = [{"role": "system", "content": PROMPT_TEMPLATE.format(question=user_input)}]

        for message in history:
            prompt.append(message)
        
        prompt.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo-16k",
            messages = prompt
        )

        ai_response = response.choices[0].message['content']
        st.session_state["messages"].append({"role": "assistant", "content": ai_response})
        st.write(ai_response)

    # conversation 로그파일에 저장
    log_file, _ = manage_log_file(session_id)
    save_conversation(log_file, st.session_state["messages"])

    '''
    Patch Note
    3. 프롬프트를 따르게 수정
    '''
