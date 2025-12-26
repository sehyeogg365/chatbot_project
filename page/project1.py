import streamlit as st
from src.utils import project1_desc as p1d


def app():
	st.write('''
		### Streamlit 매뉴얼을 작성해 주세요.

		DAS (Data Acquisition System) - 데이터 수집 시스템
		• 다양한 소스(API, DB, 파일, 스트리밍 등)로부터 원시 데이터를 수집
		• 데이터 파이프라인의 첫 번째 단계
		  
		DSS (Data Storage System) - 데이터 저장 시스템
			• 수집된 데이터를 저장하는 레이어
			• Data Lake, Data Warehouse, Object Storage 등
			• 원시 데이터와 처리된 데이터를 보관
		  
		JPS (Job Processing System) - 작업 처리 시스템
			• 데이터 변환, 정제, 집계 등의 ETL/ELT 작업 실행
			• Airflow, Spark, Kafka Streams 같은 처리 엔진
			• 배치/스트리밍 처리 오케스트레이션
				
		WSS (Web Service System) - 웹 서비스 시스템
			• 처리된 데이터를 API나 대시보드로 제공
			• 최종 사용자나 다른 시스템이 데이터에 접근할 수 있는 인터페이스
			BI 툴, REST API, GraphQL 등
				
				'''
				)

	p1d.desc()
