import streamlit as st

st.title("Session State Basic")

"st.session_state object:", st.session_state

##  위젯에 연결하기
number = st.slider("A number", 1, 10, key='slider')

st.write(st.session_state)  #st.session_state 랑 같음

col1, bff, col2 = st.beta_columns([1,0.5,3]) # st.beta_columns가 업뎃이 안된듯, session내 구역 나누기 한거임, if col2는 3 만큼 떨어진 곳에 글을 쓴다는 뜻

option_names = ['a', 'b','c']

# 2. next 버튼으로 자동 다음 옵션 선택하게 하는 방법
next = st.button("Next option")

if next:
    if st.session_state["radio_option"] == 'a':
        st.session_state.radio_option = 'b'
    elif st.session_state["radio_option"] == 'b':
        st.session_state.radio_option = 'c'
    else:
        st.session_state.radio_option = 'a'

# 1. 단추 옵션을 구현하는 방법
option = col1.radio('Pick an option', option_names, key='radio_option')
st.session_state

if option == 'a':
    col2.write("You picked 'a' : smile:")
elif option == 'b':
    col2.write("You picked 'b' : heart:")
else:
    col2.write("You picked 'c' : rocket:")
