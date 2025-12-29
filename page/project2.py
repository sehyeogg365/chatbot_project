import streamlit as st
from src.utils import project2_desc as p2d


def app():
	col1, col2, col3 = st.columns([1, 2, 1]) # 비율 설정 (좌, 중, 우)

	with col2: # 가운데 컬럼에 이미지 배치
		st.image("docs/DataFlow.png", caption="DataFlow", use_container_width=True, width=300)
	p2d.desc()
