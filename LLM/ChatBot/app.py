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

# 제목과 페이지 설정
st.set_page_config(page_title="Happy bot", page_icon="😃")
st.title("Happy AI")
st.info("Test alpha ver 1.0")

# API key 설정
os.environ["OPENAI_API_KEY"] = st.secrets["general"]["openai_api_key"]

# 대화기록이 없으면 리스트 생성
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 채팅 대화기록을 저장하는 store 세션 상태 변수
if "store" not in st.session_state:
    st.session_state["store"] = dict()

# 이전 대화기록을 출력
print_messages()

with st.sidebar:
    session_id = st.text_input("Session ID", value="w001")

    clear_btn = st.button("대화기록 초기화")
    if clear_btn:
        st.session_state["messages"] = []
        st.session_state["store"] = dict()
        st.rerun()
        
# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in st.session_state["store"]: # 세션 ID가 store에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 store에 저장
        st.session_state["store"][session_id] = ChatMessageHistory()
    return st.session_state["store"][session_id] # 해당 세션 ID에 대한 세션 기록 반환


if user_input := st.chat_input("메시지를 입력해주세요."):
    # 사용자가 입력한 내용
    st.chat_message("human").write(f"{user_input}")
    st.session_state["messages"].append(ChatMessage(role="human", content=user_input))
    
    # AI의 답변
    with st.chat_message("ai"):
        stream_handler = StreamHandler(st.empty())
    
        # LLM을 사용하여 AI의 답변 생성
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", PROMPT_TEMPLATE,
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}")
            ]
        )

        # llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True, callbacks=[stream_handler])
        llm = ChatOpenAI(
            model="gpt-4o", 
            streaming=True, 
            callbacks=[stream_handler]
        )
        # llm = ChatOllama(model="EEVE-Korean-10.8B:latest", callbacks=[stream_handler])
        # llm = ChatOllama(model="llama-3-8b-it-ko-chang:latest", callbacks=[stream_handler])
            
        chain = prompt | llm
        
        chain_with_memory = (
            RunnableWithMessageHistory(
                chain,
                get_session_history, # 세션 기록을 가져오는 함수
                input_messages_key="question", # 사용자 질문 키
                history_messages_key="history" # 기록 메시지 키
            )
        )
        response = chain_with_memory.invoke(
            {"question": user_input},
            # 세션ID 설정
            config={"configurable": {"session_id": session_id}}
        )

        st.session_state["messages"].append(
            ChatMessage(role="ai", content=response.content)
        )

