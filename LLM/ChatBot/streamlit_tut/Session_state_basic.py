import streamlit as st

st.title("Session State Basic")

#세션 스테이트는 기본적으로 그냥 딕셔너리인가? no, 어기서든 업데이트가 가능하도록 배포 가능한 홈페이지 실시간 업데이트 딕셔너리 즉, 최신 사전!

"st.session_state object:", st.session_state # 이렇게 문자열 뒤에 사용하면 웹상 그대로 등록, 그리고 ***세션에 있는 정보들 보여줌***

if 'a_counter' not in st.session_state:
    st.session_state['a_counter'] = 0 # 원하는 {'key':'values'} 형태로 세션에 추가해줌

if "boolean" not in st.session_state:
    st.session_state.boolean = False

st.write(st.session_state) # 이걸 작성하기 전까진, session_state에는 "st.session_state object:" 만 등록되어 있음

st.write('a_counter is:',st.session_state['a_counter'])
st.write('boolean is:',st.session_state.boolean)

for i in st.session_state.keys():
    st.write(i)

for i in st.session_state.values():
    st.write(i)

for i in st.session_state.items():
    i

button = st.button('Update State') #st.button 자체가 버튼을 만든다는 메소드이기에 세션에는 버튼이 업데이트 된 상태이다.
'버튼 누르기 전', st.session_state

if button:
    st.session_state['a_counter'] += 1
    st.session_state.boolean = not st.session_state.boolean
    '버튼 누른 후', st.session_state

# state 초기화
for key in st.session_state.keys():
    del st.session_state[key]

st.session_state # 모든 값 초기화됨을 확인



    







