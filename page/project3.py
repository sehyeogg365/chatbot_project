import streamlit as st
from src.chatbot import process_query

def app():
    st.title("🏪 온누리 챗봇")

    if "history" not in st.session_state:
        st.session_state.history = []

    # 1. 기존 대화 내역 표시
    for user_msg, bot_msg in st.session_state.history:
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            st.write(bot_msg)

    # 2. 사용자 입력 받기
    if query := st.chat_input("질문을 입력하세요"):
        # 사용자의 질문을 화면에 즉시 표시 (리런 전이라도 보이게)
        with st.chat_message("user"):
            st.write(query)

        # 3. 답변 생성 및 표시
        with st.chat_message("assistant"):
            with st.spinner("데이터 분석 중..."):
                # 현재 질문을 포함하지 않은 history를 보낼지, 포함해서 보낼지 chatbot.py 로직에 맞춰 결정
                answer = process_query(query, st.session_state.history)
                st.write(answer)
        
        # 4. 세션 상태 업데이트 (화면 표시 후에 저장)
        st.session_state.history.append((query, answer))
        
        # 5. 마지막에 리런을 해주어 다음 입력을 위해 상태를 확정 (필요 시)
        st.rerun()

    return 0