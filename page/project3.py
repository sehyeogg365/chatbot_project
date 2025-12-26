import streamlit as st
from src.utils import project3_desc as pd3
from src.chatbot import process_query
def app():
    st.title("온누리 챗봇")
    # 히스토리 초기화
    if "history" not in st.session_state:
        st.session_state.history = [] 

    # 대화 내역 먼저 표시 (채팅창 인터페이스 느낌)
    chat_container = st.container()
    with chat_container:
       for i, (user, bot) in enumerate(st.session_state.history):
            with st.chat_message("user"):
                st.write(user)
            with st.chat_message("assistant"):
                st.write(bot)

    # 질문 입력창 (st.chat_input 사용 권장)
    if query := st.chat_input("질문을 입력하세요"): # 최신 Streamlit 전용 위젯

        # 답변 생성 중 로딩 표시
        with st.spinner("데이터 분석 중..."):
            answer = process_query(query, st.session_state.history)
        
        # 히스토리에 대화내용 저장
        st.session_state.history.append((query, answer))    

        # 방금 생성한 답변을 즉시 화면에 뿌려주기 위해 리런
        st.rerun()

    return 0    