import streamlit as st
from openai import OpenAI
import os
from datetime import datetime
import pandas as pd
import re
import numpy as np



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

# 메시지 출력 함수
def print_messages():
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.chat_message("human").write(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("ai").write(message["content"])

## 견적서################################################################################################## 
from google.oauth2.service_account import Credentials
import gspread

### 구글 sheet api setting
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

service_account_info = {
    "type": st.secrets["google"]["type"],
    "project_id": st.secrets["google"]["project_id"],
    "private_key_id": st.secrets["google"]["private_key_id"],
    "private_key": st.secrets["google"]["private_key"].replace("\\n", "\n"),
    "client_email": st.secrets["google"]["client_email"],
    "client_id": st.secrets["google"]["client_id"],
    "auth_uri": st.secrets["google"]["auth_uri"],
    "token_uri": st.secrets["google"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"]
}

creds = Credentials.from_service_account_info(service_account_info, scopes=scope)

gc = gspread.authorize(creds)

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1bCu29AFSt3c5wS1K2uyQ1kvcppi3DtEvOccESucqiYc/edit?gid=0#gid=0"

doc = gc.open_by_url(spreadsheet_url)

sheet = doc.worksheet("시트1")

# 데이터 가져오기
data = sheet.get_all_values()

# 첫 번째 행을 컬럼 이름으로 사용하여 데이터 프레임 생성
df = pd.DataFrame(data[1:], columns=data[0])
df['가격'] = df['가격'].str.replace(',', '').replace('-', np.nan).astype(float)
df.reset_index(drop=True, inplace=True)
### 구글 끝---------------================================================================================================

# df = pd.read_excel('./quote.xlsx')

### 견적용 함수 3개
def normalize_input(text):

    pattern = re.compile(r"(\S+)\s+(\S+)\s+(\d+)유저\s+(\d+)개월")
    matches = pattern.findall(text)
    
    results = []
    for match in matches:
        product, license_type, user_count, months = match
        results.append((product, license_type, user_count, months))
    
    return results

def read_quote(user_input, df):
    
    unique_licenses = df.groupby('품명')['라이센스'].unique().reset_index()
    df_str = unique_licenses.to_string(index=False)


    PROMPT_TEMPLATE = """
Role:
    - 너는 견적서의 내용을 지정된 형식에 맞춰 반환하는 프로그램이야.

Format:
    - 품명(영어), 라이센스(영어), 유저수, 개월
    - 각 주문은 콤마(,)로 구분해.
    - 각 항목 사이에는 공백을 포함해.
    - 유저수와 개월수의 숫자와 단어 사이에는 공백이 없어야 해.
    - 유저수는 숫자가 먼저 나오고 '유저'가 뒤에 오며, 개월수도 숫자가 먼저 나오고 '개월'이 뒤에 와야 해.

Instructions:
    - 무조건 지정된 형식으로 답을 반환해야 해.
    - 사용자가 '품명'을 한글로 입력하면 Product Information의 품명(영어)으로 번역해.
    - '유저수'와 '개월수'의 기본 값은 '1'이야.
    - '유저수'와 '개월수'가 입력되지 않으면 기본 값을 사용해.
    - '품명'만 존재할 경우, Product Information의 '라이센스' 리스트 첫 번째 값을 사용해.
    - '유저'와 '개월'이라는 단어를 항상 포함해. 유저수와 개월수는 항상 숫자가 먼저 오고, 그 뒤에 '유저'와 '개월'이 와야 해.
    - 각 항목 사이에는 항상 공백을 포함해.
    - Product Information에 없는 품명은 'Null'로, 라이센스도 'Null'로 반환해.
    - Format 외의 다른 대답은 절대 하지 마.

견적 질문:
    - {user_input}

Product Information:
    - {df_str}
"""

    prompt = PROMPT_TEMPLATE.format(user_input = user_input, df_str = df_str)
    
    prompt_messages = [{"role": "system", "content": prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt_messages
    )
    
    data = response.choices[0].message.content
    return data

def answer(quote_data, user_input):
    user_quote = read_quote(user_input, quote_data)
    norm_user_quote = normalize_input(user_quote)
    
    temp = set()
    total_price = 0
    estimate_output = []

    estimate_output.append('\n문의하신 상품:')
    for i in norm_user_quote:
        estimate_output.append(f"- 제품명: {i[0]:<15} 라이센스: {i[1]:<25} 사용자 수: {i[2]:<10} 개월 수: {i[3]:<5}")
    
    estimate_output.append('\n견적:')
    for user_item in norm_user_quote:
        product_info = quote_data[(quote_data['품명'] == str(user_item[0])) & 
                                  (quote_data['라이센스'] == str(user_item[1])) & 
                                  (quote_data['유저수'] == str(user_item[2])) & 
                                  (quote_data['개월수'] == str(user_item[3]))]
        
        if not product_info.empty:
            product_key = (user_item[0], user_item[1], user_item[2], user_item[3])
            if product_key not in temp:
                product_info = product_info.iloc[0]
                product_str = f"{product_info['품명']} {product_info['라이센스']} {product_info['개월수']}개월 {product_info['유저수']}명"
                price = int(product_info['가격'])
                total_price += price
                estimate_output.append(f"- {product_str:35} = {price:,}원")
                temp.add(product_key)
        else:
            estimate_output.append(f"- {user_item[0]:<15} {user_item[1]:<20}: 일치하는 상품이 존재하지 않습니다. 상담을 원하시면 메일을 남겨주세요.")
    
    if total_price > 0:
        estimate_output.append(f"\n총액: {total_price:,}원")

    return "\n".join(estimate_output)

# pdf 다운코드 ========================================================================================================================
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def create_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    
    # 한글 폰트 등록
    pdfmetrics.registerFont(TTFont("맑은고딕", "malgun.ttf"))
    style.fontName = "맑은고딕"
    
    # 제목 추가
    title_style = styles["Title"]
    title_style.fontName = "맑은고딕"
    title = Paragraph("견적서", title_style)
    
    # 문단 생성
    paragraphs = [title, Spacer(1, 0.5 * inch)]
    for line in text.split("\n"):
        para = Paragraph(line, style)
        paragraphs.append(para)
        paragraphs.append(Spacer(1, 0.2 * inch))  # 문단 사이에 간격 추가
    
    # 문서에 문단 추가
    doc.build(paragraphs)
    buffer.seek(0)
    return buffer
########################################################################################################


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

# 예시 질문 리스트
example_questions = [
    "모노프로는 어떤 회사인가요?",
    "취급하는 상품은 어떤것이 있나요?",
    "주문을 넣고싶은데 어떻게 하면 되죠?"
]

# 페이지 전환을 위한 query params 업데이트 제일 중요!@#$ㅕ%()ㅕ#쌰(또허ㅏㅉ띠:후ㅏㅉ)
def set_page(page_name):
    st.query_params.from_dict({"page": page_name})
    st.session_state.page = page_name
    st.rerun()

# 스트림릿 제작 코드--===========================================================================================================================
# st.set_page_config 는 항상 맨 위에 불러와야함
# st.set_page_config(page_title="MonoPro", page_icon="😃") ### layout="centered" 나중에 추가 해보기


# 버전3용 페이지 선택
query_params = st.query_params
if "page" in query_params:
    page = query_params["page"]
else:
    page = "Home"

if "page" not in st.session_state:
    st.session_state.page = "Home"


# 메인 페이지
if st.session_state.page == "Home":
    st.set_page_config(page_title="MonoPro", page_icon="😃")
    st.title("안녕하십니까 모노프로입니다. 무엇을 도와드릴까요?")
    st.write("Choose an option below:") 

    col1, col2 = st.columns(2)
    with col1:
        if st.button("견적서 작성"):
            set_page("quote")
    with col2:
        if st.button("문의하기"):
            set_page("FAQ")

# 견적서 작성 페이지
elif st.session_state.page == "quote":
    # st.set_page_config(page_title="MonoPro", page_icon="😃")

    with st.sidebar:
        home_btn = st.button("뒤로가기")
        if home_btn:
            set_page("Home")

    st.title("견적서 요청")
    # 견적서 작성 코드
    user_input = st.text_input("""견적요청 형식: 상품명 / 라이센스 / 사용자 수 / 개월\n
                               견적요청 예시: 패들렛/스쿨/4명/12개월, 유튜브/프리미엄/1명/7개월, 북크리에이터/프리미엄/1/12 
                               """)
    if st.button("견적 요청"):
        response = answer(df, user_input) # 견적서 작성 코드 변경 요망%^%^&$&*#(^$@#^&*$^@#&*)%@$()&%*#$@%)$#^%&*)@#$%
        st.write(response)

        pdf_buffer = create_pdf(response)
        st.download_button(
            label = '견적서 다운로드',
            data=pdf_buffer,
            file_name= '견적서.pdf',
            mime= 'application/pdf'
        )

        ### 여기에 견적서 PDF 다운로드 코드 추가 필요##################
        # st.success("견적서가 성공적으로 작성되었습니다.")

# 문의하기 페이지 내용
elif st.session_state.page == "FAQ":
    # st.set_page_config(page_title="MonoPro", page_icon="😃")
    # Mark down 필요하다 싶으면 여기에 CSS 추가하면 된다!#@$ㅕ()#ㅛㅕ*(ㅑ#ㅛ*_(#@$(_@#()_@#ㅕ(ㄲ_ㅕ#@()))))
    st.title("Monopro 스마트 챗봇입니다. 무엇을 도와드릴까요?")
    st.info('''모노프로 고객 상담사례 1,000건이 학습된 봇 입니다.
        간단한 질의로 신속한 상담을 받아보세요.
        견적요청: https://monopro.kr/contact
        (챗봇 기반 자동 견적서 발행은 추후 지원 예정입니다. )

        문의하시겠습니까?''')
    
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

        home_btn = st.button("뒤로가기")
        if home_btn:
            set_page("Home")

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
