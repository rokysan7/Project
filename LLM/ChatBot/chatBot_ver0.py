import streamlit as st
import openai
import os
from datetime import datetime

# OpenAI API 키 설정
openai.api_key = st.secrets["general"]["openai_api_key"]

# 로그 파일 경로 설정
LOG_FILE_PATH = 'chat_logs/'

# 로그 파일을 관리하는 함수
def manage_log_file(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f'{LOG_FILE_PATH}{user_id}_{today}.txt'
    
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

# GPT-4 API를 사용하여 응답을 생성하는 함수
def get_gpt_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages
    )
    return response.choices[0].message['content']

# 대화 함수
def chat_with_bot(user_id, user_input):
    log_file, conversation = manage_log_file(user_id)
    
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    
    if conversation:
        # 이전 대화를 메시지로 변환
        conversation_lines = conversation.strip().split('\n')
        for line in conversation_lines:
            if line.startswith("User:"):
                messages.append({"role": "user", "content": line[len("User: "):]})
            elif line.startswith("AI:"):
                messages.append({"role": "assistant", "content": line[len("AI: "):]})
    
    messages.append({"role": "user", "content": user_input})
    
    gpt_response = get_gpt_response(messages)
    
    conversation += f"\nUser: {user_input}\nAI: {gpt_response}"
    save_conversation(log_file, conversation)

    return gpt_response

# Streamlit 애플리케이션 설정
st.title("Chatbot Application")

user_id = st.text_input("Enter your user ID", "user1")
user_input = st.text_input("Enter your message")

if st.button("Send"):
    if user_input:
        response = chat_with_bot(user_id, user_input)
        print(messages)
        st.text_area("Chat Log", value=f"You: {user_input}\nAI: {response}", height=400)
    else:
        st.write("Please enter a message.")

