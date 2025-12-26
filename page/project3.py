import streamlit as st
from src.utils import project3_desc as pd3
from src.chatbot import process_query
def app():
    st.title("온누리 챗봇")

    if "history" not in st.session_state:
        st.session_state.history = [] 

    for user, bot in st.session_state.history:
        st.markdown(f"**사용자:** {user}")
        st.markdown(f"**챗봇:** {bot}")
        st.markdown("---")

    query = st.text_input("질문을 입력하세요")

    if st.button("전송") and query:
        answer = process_query(query, st.session_state.history)
        st.session_state.history.append((query, answer))    
        
    return 0    