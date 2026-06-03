import streamlit as st

def app():
	st.write('''
	### 개발 환경을 구축한 차례에 따라 매뉴얼을 작성해 주세요. 

가상환경 구축 
		  		  
1.conda create --name new_env python=3.11
파이썬 3.11버전이상으로
 
2.pip install pandas sqlalchemy langchain-openai streamlit python-dotenv
필수요소들만 설치
 
3.pip freeze > requirements.txt
requirements.txt에 환경설정 요소들 저장
 
4.pip install -r requirements.txt

		  

	''')
