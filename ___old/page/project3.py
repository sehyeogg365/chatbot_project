import streamlit as st
from src.chatbot import process_query
from streamlit_js_eval import streamlit_js_eval, get_page_location
import json

def app():
    st.title("🏪 온누리 챗봇")
    # JavaScript를 통해 localStorage 읽기
    # if 'history_loaded' not in st.session_state:
    #     st.session_state.history_loaded = []
    # # localStorage에서 데이터 읽기 (첫 로드 시)
    # if not st.session_state.history_loaded:
    #     # 임시로 빈 리스트로 초기화
    #     if 'history' not in st.session_state:
    #         st.session_state.history = []
    #     st.session_state.history_loaded = True    
    if "history_initialized" not in st.session_state:
        raw = streamlit_js_eval(
            js_expressions="localStorage.getItem('onnuri_history')",
            key="load_history"
        )

        if raw:
            try:
                st.session_state.history = json.loads(raw)
            except:
                st.session_state.history = []
        else:
            st.session_state.history = []

    st.session_state.history_initialized = True
    # 1. 기존 대화 내역 표시
    for user_msg, bot_msg in st.session_state.history:
        with st.chat_message("user", avatar="👤"):
            st.write(user_msg)
        with st.chat_message("assistant", avatar="🏪"):
            st.write(bot_msg)
    # 사이드바에 초기화 버튼
    with st.sidebar:
        st.header("💾 세션 관리")
        
        if st.button("🔄 대화 초기화", use_container_width=True):
            st.session_state.history = []
            streamlit_js_eval(
                js_expressions="localStorage.removeItem('onnuri_history')",
                key="clear_history"
            )
            st.rerun()
        
        st.divider()
        
        # 현재 대화 수
        st.metric("대화 수", len(st.session_state.history))

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
        streamlit_js_eval(
            js_expressions=f"""
            localStorage.setItem(
                'onnuri_history',
                {json.dumps(st.session_state.history)}
            )
            """,
            key="save_history"
        )
        # 5. 마지막에 리런을 해주어 다음 입력을 위해 상태를 확정 (필요 시)
        st.rerun()

    return 0