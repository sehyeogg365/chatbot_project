# 온누리상품권 가맹점 안내 챗봇

## 🚀 실행 방법

### 1. 환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 데이터 준비
1. 공공데이터포털에서 다음 데이터 다운로드:
   - 소상공인시장진흥공단_전국_온누리상품권_가맹점_현황
   - 소상공인시장진흥공단_온누리상품권_지역별_회수현황
   - 소상공인시장진흥공단_온누리상품권_지역별_판매현황

2. `/` 폴더에 CSV 파일 저장

### 3. 전처리 및 벡터 DB 구축
```bash
# 노트북 순서대로 실행
jupyter notebook

# 실행 순서:
# 1. notebooks/01_data_exploration.ipynb
# 2. notebooks/02_preprocessing.ipynb
# 3. src/search_engine.ipynb
# 4. src/rag_setup.ipynb  ⚠️ 10-20분 소요, API 비용 약 $0.30

```

### 4. 앱 실행
```bash
streamlit run app.py
```

## ⚠️ 주의사항

### 벡터 DB (vectordb/chroma_db/)
- 용량: 약 500MB~1GB
- Git에 포함되지 않음
- 재구축 필요: `04_rag_setup.ipynb` 실행
- 소요 시간: 10-20분
- API 비용: 약 $0.30

### OpenAI API 키 필요
```bash
# .env 파일 생성
OPENAI_API_KEY=your_api_key_here
```

## 📁 프로젝트 구조
```
onnuri-chatbot/
├── data/
│   ├── raw/                    # ⚠️ Git에 미포함 (직접 다운로드)
│   └── processed/              # ⚠️ Git에 미포함 (전처리 후 생성)
├── notebooks/                  # ✅ Git에 포함
├── vectordb/                   # ⚠️ Git에 미포함 (재구축 필요)
├── app.py                      # ✅ Git에 포함
├── requirements.txt            # ✅ Git에 포함
├── .env.example                # ✅ Git에 포함
└── README.md                   # ✅ Git에 포함
```