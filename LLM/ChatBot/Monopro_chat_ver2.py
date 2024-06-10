import streamlit as st
from openai import OpenAI
import os
from datetime import datetime
import pandas as pd
from quote import normalize_input, read_quote, answer_quote, get_products_dataframe

# from dotenv import load_dotenv

# load_dotenv()

# API 키 설정
# OpenAI.api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key = st.secrets['general']['openai_api_key'])

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

# # 견적서 
df = pd.read_excel('Project/LLM/ChatBot/quote.xlsx')

# 데이터를 텍스트로 변환
# quote_text = ""
# for index, row in df.iterrows():
#     quote_text += f"{row['제품명']}의 단가는 {row['단가']}원입니다.\n"

def get_estimate_response(question, quote_dict):
    import re
    match = re.search(r"(\D+)\s*(\d+)\s*개", question)
    if match:
        product_name = match.group(1).strip()
        quantity = int(match.group(2))
        
        # 제품에 해당하는 단가를 찾음
        if product_name in quote_dict:
            unit_price = quote_dict[product_name]
            total_price = unit_price * quantity
            return f"{product_name}의 {quantity}개의 견적은 {total_price}원입니다."
        else:
            return "해당 제품을 찾을 수 없습니다."
    else:
        return "올바른 형식으로 질문을 입력해주세요."

# PROMPT_TEMPLATE 설정
PROMPT_TEMPLATE = """
Role:
너는 에듀테크 제품을 retail 하는 '모노프로'라는 회사의 상담 직원이야.

Instructions:
다음은 모노프로 제품의 기본 가이드야.
'''
[패들렛]
스쿨 유료요금제: 12개월 라이센스, 10 유저
플래티넘: 12개월 라이센스, 1 유저
[챗지피티]
팀: 다수 유저, 12개월 이용권
플러스: 1 유저, n개월 이용권
[유튜브]
프리미엄: 1 유저, 12개월 이용권
[키네마스터]
프리미엄: 1 유저, 12개월 이용권
[모션 엘리먼츠]
유료 요금제: 1 유저, 12개월 이용권
[코스페이시스]
프로 + VR/AR 머지큐브: 선생님 1 + 학생 n, 12개월 라이센스
[어도비]
크리에이티브 클라우드 올 앱 교사용: 1 유저, 12개월 이용권
공통 FAQ
계정 납품: 신규 계정 생성, 모노프로 웹메일 이용
이메일 인증: 모노프로 웹메일로 6자리 확인
대량구매: 상한 없음
납품 소요시간: 1-3일, 최대 1주일
계정 공유: 불가, 1인 1계정 원칙
기타 에듀테크 상품: 현재 10종, 추가 요청 가능
사용 기간: 납품일로부터 1년
계정 연장: 재구매 후 연장 처리
챗GPT FAQ
플러스 계정 연장: 불가, 보안 문제
팀과 플러스 차이: 팀은 우선권, 유연한 추가/삭제 가능
팀 계정 납품: 관리자 계정과 팀원 연결
비용 차이: 대량 구매 대행, 환율 변동 방어
패들렛 FAQ
플래티넘 계정 연장: 불가, 보안 문제
스쿨 계정 연장: 가능, 대시보드 제공
납품 소요시간: 성수기 1-2주, 평시 3일
유튜브 FAQ
사용 인원: 1인 1계정, 2개 디바이스 동시 사용 가능
비용: 안정적 사용을 위한 비용 소요
코스페이시스 FAQ
추가 옵션: 추후 세분화 예정
어도비 FAQ
사용 인원: 1인 1계정, 2개 디바이스 동시 사용 가능
수량 제한: 기관당 1개 제한, 해결 방안 모색 중
키네마스터 FAQ
사용 인원: 1인 1계정, 2개 디바이스 사용 가능
활성화 방법: 활성화 키 및 메뉴얼 제공
활성화 기한: 1개월 내 활성화, 이후 1년 사용
'''
너는 가이드를 따라서 상담을 진행해 주면 돼.


Context:
- 대화의 맥락: 너는 가이드에 없는 내용을 질문 받는다면 '질문 주신 내용은 논의가 필요한 내용입니다. 저희 회사로 이메일을 남겨주시면 협의 후 알려드리겠습니다.' 라고 답변해야해.
- 항상 친절하게 모노프로 직원으로 행동해야해.

Question:
{question}
"""
# st.set_page_config 는 항상 맨 위에 불러와야함
st.set_page_config(page_title="MonoPro", page_icon="😃")
 
# Streamlit 인터페이스 내에서 호출
user_input = st.text_input("견적요청: ")
if st.button("견적 요청"):
    response = answer_quote(user_input, get_products_dataframe(normalize_input(read_quote(user_input, df)), df)) # 견적서
    st.write(response)

# Streamlit Setting

st.title("Monopro 스마트 챗봇입니다. 무엇을 도와드릴까요?")
st.info('''모노프로 고객 상담사례 1,000건이 학습된 봇 입니다.
간단한 질의로 신속한 상담을 받아보세요.
견적요청: https://monopro.kr/contact
(챗봇 기반 자동 견적서 발행은 추후 지원 예정입니다. )

문의하시겠습니까?''')


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

# 예시 질문 리스트
example_questions = [
    "모노프로는 어떤 회사인가요?",
    "취급하는 상품은 어떤것이 있나요?",
    "주문을 넣고싶은데 어떻게 하면 되죠?"
]

# 예시 질문 버튼 생성
st.subheader("문의하시겠습니까?")
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
        prompt = [{"role": "system", "content": PROMPT_TEMPLATE.format(question=user_input)}]

        for message in st.session_state["messages"]:
            prompt.append({"role": message["role"], "content": message["content"]})

        prompt.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model = "gpt-4o",
            messages = prompt,
            stream=True,  # 스트리밍 모드 활성화
        )

        # 스트리밍 없이 대답 생성(정상 작동)
        # ai_response = response.choices[0].message.content
        # st.session_state["messages"].append({"role": "assistant", "content": ai_response})
        # st.write(ai_response)

        # 스트리밍 응답을 받을 자리표시자 생성
        response_placeholder = st.empty()
        full_response = ""
     
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_response += f'{content}'
            response_placeholder.markdown(full_response)   # 이게 핵심. 자릿수를 마크다운 해줘야 한다.       
    
        st.session_state["messages"].append({"role": "assistant", "content": full_response})
    
    # conversation 로그파일에 저장
    log_file, _ = manage_log_file(session_id)
    save_conversation(log_file, st.session_state["messages"])

# st.session_state




# patch note
# 1. streaming 기능 추가
# 2. 견적서 기능 추가
