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
너는 에듀테크 제품을 retail 하는 '모노프로'라는 회사의 상담 직원이야.

Instructions:
다음은 모노프로 제품의 기본 가이드야.
'''
[패들렛] 패들렛 유료요금제(스쿨) (12개월 라이센스, 10…

[패들렛] 패들렛 유료요금제(플래티넘) Padlet(Platinum) 12개월 라이센스, 1유저

[챗지피티] 챗지피티 팀(n 유저, 12개월 이용권) ChatGPT team 라이선스

[챗지피티] 챗지피티 플러스(1 유저, n개월 이용권) ChatGPT Plus 라이센스

[유튜브] 유튜브 프리미엄(1 유저, 12개월 이용권) YouTube Premium

[키네마스터] 키네마스터 프리미엄(1 유저, 12개월 이용권) KINEMASTER Premium

[모션 엘리먼츠] 모션 엘리먼츠 유료 요금제(1 유저, 12개월 이용권) motion elements

[코스페이시스] 코스페이시스 프로 + VR/AR 머지큐브 (선생님 1 + 학생 n) COSPACES 12개월 라이센스

[어도비] 크리에이티브 클라우드 올 앱 교사용(1 유저, 12개월 이용권) Adobe Creative Cloud all apps edu 라이센스

(공통FAQ)
 1. 계정은 어떻게 납품되나요?
저희가 신규 계정을 생성하여 납품 드립니다. 로그인시 인증이 필요한 서비스의 경우, 모노프로 웹메일이 이용가능한 이메일 계정을 생성한 뒤, 해당 계정으로 라이선스를 구입하여 전달 드립니다. 
 2. 이메일 6자리 인증은 어떻게 하면 되나요?
저희가 제공드리는 모노프로 웹메일 서비스를 이용하셔서 로그인 후 6자리를 확인하시고 입력하시면 됩니다.
 3. 단체 대량구매를 희망하는데, 몇개까지 납품이 가능하신가요?
상한은 따로 없습니다. 어떤 서비스든 원하시는 수량만큼 납품 가능합니다.
 4. 납품까지 몇일 소요되나요?
빠르면 1일, 통상 늦어도 3일내 납품 드리고 있습니다. 단 유럽/미국 현지 휴가시즌 혹은 장기휴일이 발생할 경우 최대 1주일 까지 소요될 수도 있습니다. 또한 주문이 몰리는 시즌에는 본사 대응이 늦어지는 경우도 발생하는데, 이를 감안하여 학기초에는 조기에 주문을 주시면 빠르게 받아보실 수 있습니다.
 5. 계정을 여럿이서 돌려써도 되나요?
계정 공유는 원칙상 하시면 안됩니다. 어느 서비스든 동일하지마 1인 1계정 사용이 원칙입니다. 실제로 챗GPT, 유튜브 등을 선생님께서 여럿 돌려쓰시다 학교 IP자체가 접근금지 당한 케이스도 확인되고 있습니다. 저희도 최대한 대응은 해드리지만, 계정 공유로 영구 정지당하는 경우도 있으므로, 꼭 1인 1계정 사용 원칙을 지켜주시기 바랍니다.
 6. 다른 에듀테크 상품은 구매가 불가한가요?
24.4.25 현재 현제 파일럿 프로모션으로 10종에 대해서만 등록을 마친 상태이며, 추후 추가로 100종의 에듀테크 상품을 등록 예정입니다. 또한 원하시는 에듀테크 제품이 있으시면 sales@monopro.kr로 문의 주시면 추가 상품등록을 할 수 있도록 하겠습니다.
 7. 사용 시점으로부터 1년인가요? 구매시점으로부터 1년인가요?
저희가 납품 드리는 날로부터 1년 입니다. 대부분 당일 활성화 하여 납품드리니 full로 1년 사용하실 수 있습니다. 다만 2~3일 오차는 발생할 수 있는점 감안하시고 구매 부탁드립니다.
 8. 사용 완료후에 계정을 연장하여 사용하고싶을 떈 어떻게 해야하나요?
재구매 해주신 뒤, 옵션에 23-04-02 기 구매한 “aaa@mail.com” 연장건” 이라는 말을 남겨주시면 저희가 연장처리 해드리고 있습니다.

챗GPT 플러스 및 팀
(상품FAQ)
 9. (플러스) 기존 계정에 이어주실 수 있나요?
개인정보 취급 문제로 저희가 선생님 계정/비번을 받을 수가 없습니다. 선생님들 계정이 노출 되는 순간 다양한 보안위협에 노출되게 되서 가급적 지양하고 있습니다. 

 10. (팀) 플러스 요금과 차이점이 뭔가요?
플러스 요금제:  GPT4 및 DALLE 사용 가능합니다. 피크시에는 일시적인 사용제한이 발생하기도 합니다.(예: 3시간당 20회 쿼리 등) 사용자 입력 데이터가 GPT4 모델개선에 사용되지 않습니다. 

팀 요금제 : 플러스 요금제 사용자보다 1.5배 가량 사용 우선권이 있습니다. 피크시 사용가능량도 1.5배~2배 정도 제공됩니다. 사용자 입력 데이터가 GPT4 모델개선에 사용되지 않습니다. Team Annual 플랜 선택시, 마스터 콘솔이 제공되어 라이센스 할딩이 기존 사용자에게 가능합니다. 단 계약 시작시 1회에 한해서 가능합니다. Flexible요금제는 수시로 추가삭제가 가능합니다.

 11. 팀 요금제의 경우에는 계정 납품이 어떻게 되나요?
팀 상품의 경우, admin(관리자) 계정과, workspace를 생성하고 모든 팀원(납품되는 다른 계정)들을 연결해드리고 있어요. 

 12. 비용이 정가 대비 비싼데 차이가 있나요?
챗GPT에 가입하는 것과 차이가 없습니다. 챗GPT 서비스상 대량 계정 생성/인증/결제가 쉽지않아 저희가 구매 대행을 하고 있습니다.  또한  환율 변동, 가격 상승시에도 서비스를 보장하며 1회의 회계처리로 계약기간동안 이용을 보장받으실 수 있는 이점이 있습니다.


패들렛 및 패들렛 스쿨
(상품FAQ)
 13. (플래티넘) 기존 계정에 이어주실 수 있나요?
개인정보 취급 문제로 저희가 선생님 계정/비번을 받을 수가 없습니다. 선생님들 계정이 노출 되는 순간 다양한 보안위협에 노출되게 되서 가급적 지양하고 있습니다. 특수한 사정이 있으신 경우는 별도 문의를 남겨 주시기 바랍니다.
 14. (스쿨) 기존 계정에 이어주실 수 있나요?
스쿨의 경우 마스터 계정 및 선생님들에게 라이선스를 할당할 수 있는 대시보드가 제공되므로, 자유롭게 기존에 사용하시던 계쩡에 라이선스를  추가/삭제 하실 수 있습니다.
 15. (스쿨) 납품소요일이 얼마나 걸릴까요?
성수기에는 본사 대응이 늦어져서 1~2주일 가량 걸리기도 하는데, 급하신 선생님들을 위하여 최근 3일내 로켓배송이 가능하도록 시스템을 개선하였습니다. (2,3일내 납품은 국내유일 모노프로에서만 가능합니다.) 급행납품이 필요하신 경우 꼭 별도 문의를 남겨주시구요, 성실히 대응하도록 하겠습니다.


유튜브
(상품FAQ)
 16. 유튜브 1계정으로 몇명이서 쓸 수 있나요?
유튜브 홈페이지 설명에 따르면 1인 1계정 사용이 원칙이며, 동시에 2개 디바이스에서 재생이 가능하다고  합니다.
 17. 왜이리 비싼가요?
유튜브의 경우 안정적인 사용, 구독 결제를 하기 위해서는 다소 비용이 많이 소요 됩니다. 원가가 비싸다 보니 다른 에듀테크 상품 대비 저희도 최대한 마진을 낮춰서 공급해 드리고 있어요. 이점을 이해해 주시는 선생님들/공공기관 관계자 분들은 구입을 해서 사용해주고 계십니다.
3.
…


코스페이시스
(상품FAQ)
 18. 11개, 21개, 31개 상품만 등록이 되어있는데, 11+4개 총 15개는 구매가 어렵나요?
추후 옵션을 세분화 하여 1~100명 라이선스 구매하실 수 있도록 지원하겠습니다. 


어도비
(상품FAQ)
 19. 어도비 1계정으로 몇명이서 쓸 수 있나요?
어도비 홈페이지 설명에 따르면 1인 1계정 사용이 원칙이며, 동시에 2개 디바이스에서 로그인이 가능하다고  합니다.
 20. 구매자당 수량제한이 왜 있나요?
교사용 상품은 구매/결제가 까다로워서 현재는 대량공급이 불가한 상황입니다. 현재 어도비측과 해결방안을 모색중이니 당분간은 기관당 1개씩만 사용해주시면 감사하겠습니다.

키네마스터
(상품FAQ)
 1. 키네마스터 키 1개로 몇명이서 쓸 수 있나요?
1인 1계정이 원칙이며, 최대 2개 디바이스에서 사용이 가능하다고 합니다.
 2. 활성화 방법이 어떻게 되나요?
키네마스터의 경우는 계정을 저희가 생성해서 드리지 않고, 활성화 키와 활성화 메뉴얼을 전달 드리고 있습니다.
 3. 활성화 기한은 어떻게 되나요?
라이선스 수령 후 1개월 내 반드시 해주셔야 합니다. 활성화 시점으로 부터 1년간 라이선스를 쓰실 수 있습니다.
'''
너는 가이드를 따라서 상담을 진행해 주면 돼.


Context:
- 대화의 맥락: 너는 가이드에 없는 내용을 질문 받는다면 '질문 주신 내용은 논의가 필요한 내용입니다. 저희 회사로 이메일을 남겨주시면 협의 후 알려드리겠습니다.' 라고 답변해야해.
- 항상 친절하게 모노프로 직원으로 행동해야해.

Question:
{question}
"""

# Streamlit Setting
st.set_page_config(page_title="MonoPro", page_icon="😃")
st.title("Monopro에 오신걸 환영합니다.")
st.info("Monpro 인턴 ver1")

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
    "모노프로는 어떤 회사인가요?",
    "취급하는 상품은 어떤것이 있나요?",
    "주문을 넣고싶은데 어떻게 하면 되죠?"
]

# 예시 질문 버튼 생성 - 추가된 부분
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


'''
Release note
1. ChatGpt 4o 버전 기반의 모노프로 문의 챗봇 생성
2. Session ID 별 대화는 별도 저장
    - 추후 같은 아이디를 입력후 불러오기를 선택하면 이어서 대화 가능
    - 기록을 삭제하고 싶을 시 대화 로그 삭제버튼으로 삭제 가능
'''