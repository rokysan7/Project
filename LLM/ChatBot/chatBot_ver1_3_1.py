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
    log_file = f'{LOG_FILE_PATH}{session_id}.txt'

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
- 시키는 것은 최대한 응해줘야함.

Context:
- 대화의 맥락: 너는 내가 비록 이해하지 못할 질문을 하더라도 충실히 응해줘야함.

Question:
{question}
"""

# Streamlit Setting
st.set_page_config(page_title="메칸더 B", page_icon="😃")
st.title("심리치료 AI")
st.info("Test alpha ver 1.3.1")

# CSS 추가 - 입력란을 고정하기 위해
st.markdown("""
    <style>
    .fixed-bottom {
        position: fixed;
        bottom: 0;
        width: 100%;
        background: white;
        padding: 10px;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 예시 질문 리스트 - 추가된 부분
example_questions = [
    "남자 친구한테 차였어",
    "강아지가 키우고 싶은데 부모님이 반대하셔",
    "어제 친구와 절교했어, 그 친구 잘못으로 싸운거야"
]

# 예시 질문 버튼 생성 - 추가된 부분
st.subheader("어떤 고민이 있으신가요?")
for question in example_questions:
    if st.button(question):
        st.session_state["user_input"] = question  

# message 초기화로 시작
if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:
    session_id = st.text_input("Session ID", value="user0001")

    load_btn = st.button("이전대화 불러오기")
    if load_btn:
        st.session_state["messages"] = load_conversation(session_id)

    clear_btn = st.button("대화기록 지우기")
    if clear_btn:
        st.session_state["messages"] = []
        st.rerun()

    # 대화 로그 삭제 버튼 
    delete_log_btn = st.button("대화 로그 삭제하기")
    if delete_log_btn:
        log_file, _ = manage_log_file(session_id)
        if os.path.exists(log_file):
            os.remove(log_file)
            st.success(f"{session_id} 세션의 대화 로그가 삭제되었습니다.")

# 메시지 출력 함수
def print_messages():
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.chat_message("human").write(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("ai").write(message["content"])

print_messages()


# 사용자 입력 받기
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""

# 입력창을 항상 표시하고, 값이 있으면 해당 값을 사용
user_input = st.chat_input("메시지를 입력해주세요.")
if st.session_state["user_input"]:
    user_input = st.session_state["user_input"]
    st.session_state["user_input"] = ""  # 이후에 재사용을 위해 초기화

if user_input:
    st.chat_message("human").write(f"{user_input}")
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("ai"):

        # PROMPT TEMPLATE 적용
        prompt = [{"role": "system", "content": "너는 심리 상담을 해주는 행복 AI이다. 시키는 것은 최대한 응해줘야 하며, 답변은 항상 한글로 작성해야 한다."}]
        for message in st.session_state["messages"]:
            prompt.append({"role": message["role"], "content": message["content"]})
        
        prompt.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model = "gpt-4o",
            messages = prompt
        )

        ai_response = response.choices[0].message['content']
        st.session_state["messages"].append({"role": "assistant", "content": ai_response})
        st.write(ai_response)

    # conversation 로그파일에 저장
    log_file, _ = manage_log_file(session_id)
    save_conversation(log_file, st.session_state["messages"])

# st.session_state

'''
ver 1.3.1 patch note
1. 첫 질문 suggested box 추가
2. 불필요하다 판단되는 st.session_state['store'] 삭제
    - 추후 캐시 메모리가 필요할 떄는 다시 생성해야 할 수 있으나 당장은 메모리 킬러임
'''