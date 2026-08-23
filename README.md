> **현재 리팩토링 진행중입니다.**

# 온누리상품권 가맹점 안내 챗봇

전국 온누리상품권 가맹점 데이터를 기반으로 자연어 질문에 답변하는 AI 챗봇 웹 애플리케이션입니다.  
LangGraph ReAct Agent + Gemini 2.5 Flash LLM을 활용하며, React SPA 프론트엔드와 FastAPI 백엔드로 구성됩니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **AI 챗봇** | 지역·업종·디지털/지류 조건 검색, 자연어 유사도 검색, 상품권 정책 FAQ, 창업 입지 경쟁도 분석 |
| **PDF 보고서 생성** | 조건 필터링 후 가맹점 목록과 차트(막대·파이)가 포함된 PDF 다운로드 |
| **데이터 인사이트** | 전국 17개 시도 가맹점 수·판매·회수 통계 대시보드 (Recharts) |
| **아키텍처 뷰어** | 시스템 아키텍처 및 DataFlow 다이어그램 + 요청 처리 흐름 설명 |
| **질문 가이드** | 챗봇에서 사용 가능한 질문 유형 예시 안내 |
| **사용자 매뉴얼** | 서비스 전체 사용 방법 안내 |

---

## 기술 스택

### 프론트엔드
- **React 18** — SPA 구성
- **Vite 5** — 빌드 도구 및 개발 서버
- **Recharts** — 데이터 시각화 (막대·선·파이 차트)
- **CSS Modules** — 컴포넌트별 스코프 스타일링

### 백엔드
- **FastAPI** — REST API 서버
- **Uvicorn** — ASGI 서버
- **Pydantic** — 요청/응답 데이터 검증
- **pandas** - 정형 데이터 검색/필터링

### AI / LLM
- **LangGraph** (`create_react_agent`) — Tool-calling ReAct Agent 구성
- **LangChain** — LLM 추상화, 벡터스토어 연동
- **Google Gemini 2.5 Flash Lite** — LLM (langchain-google-genai)
- **OpenAI text-embedding-3-small** — 가맹점 텍스트 임베딩

### 데이터 / 저장
- **Pandas** — 정형 데이터 필터링 및 통계
- **ChromaDB** — 로컬 벡터 데이터베이스 (MMR 검색)
- **CSV** — 전처리된 온누리 가맹점 원본 데이터

### 보고서
- **fpdf2** — PDF 생성 (한국어 맑은 고딕 폰트)
- **Matplotlib** — 업종별 막대 차트 및 가맹 유형 파이 차트

### 개발 도구
- **Jupyter Notebook** — 데이터 탐색 및 전처리 실험
- **python-dotenv** — 환경 변수 관리

---

## 디렉토리 구조

```
chatbot_project/
├── backend/                    # FastAPI 서버
│   ├── main.py                 # 앱 초기화, CORS, 라우터 등록
│   └── routers/
│       ├── chat.py             # POST /api/chat  — 챗봇 응답
│       └── report.py           # GET  /api/report — PDF 보고서 생성
│
├── frontend/                   # React SPA (Vite)
│   ├── src/
│   │   ├── App.jsx             # 루트 컴포넌트, 페이지 라우팅
│   │   ├── components/
│   │   │   ├── Sidebar.jsx     # 사이드바 내비게이션
│   │   │   └── Chat.jsx        # 챗봇 UI (메시지 버블, 입력창)
│   │   └── pages/
│   │       ├── Manual.jsx          # 사용자 매뉴얼
│   │       ├── QuestionGuide.jsx   # 질문 유형 가이드
│   │       ├── Architecture.jsx    # DataFlow / 시스템 아키텍처
│   │       ├── DataInsights.jsx    # 데이터 인사이트 대시보드
│   │       └── Report.jsx          # 보고서 생성 (PDF 다운로드)
│   ├── index.html
│   └── package.json
│
├── src/                        # 핵심 비즈니스 로직
│   ├── chatbot.py              # LangGraph ReAct Agent + 4개 Tool 정의
│   ├── llm_config.py           # Gemini LLM / OpenAI Embeddings 설정
│   ├── search_engine.py        # 지역·시장명·복합 검색 함수, 통계 함수
│   ├── rag_setup.py            # ChromaDB 벡터DB 구축 스크립트
│   └── utils/
│       ├── project1_desc.py    # 프로젝트 설명 텍스트
│       ├── project2_desc.py
│       └── project3_desc.py
│
├── notebooks/
│   ├── 01_data_exploration.ipynb   # 기본 통계량 확인 및 EDA
│   └── 02_preprocessing.ipynb      # 전처리 및 cleaned_onnuri.csv 생성
│
├── vectordb/chroma_db/         # ChromaDB 벡터 데이터베이스 (git 제외)
├── docs/                       # 아키텍처 다이어그램, 실행 화면 이미지
│
├── cleaned_onnuri.csv          # 전처리 완료 가맹점 데이터 (~15만 건)
├── area_onnuri.csv             # 지역별 가맹점 요약 데이터
├── 가맹점_현황.csv              # 공공데이터 원본
├── 판매_현황.csv                # 지역별 연도별 판매 현황 원본
├── 회수_현황.csv                # 지역별 연도별 회수 현황 원본
│
├── .env                        # API 키 환경 변수 (git 제외)
├── requirements.txt            # Python 패키지 목록
└── README.md
```

---

## 시스템 아키텍처

```
[사용자 브라우저]
      │  React SPA (Vite :5173)
      │
      ▼
[FastAPI 백엔드 (:8000)]
      ├── POST /api/chat   →  src/chatbot.py
      │                        │
      │                   LangGraph ReAct Agent
      │                        ├── Tool 1: pandas_filter
      │                        │     └── cleaned_onnuri.csv (Pandas)
      │                        ├── Tool 2: rag_search
      │                        │     └── vectordb/chroma_db (ChromaDB)
      │                        ├── Tool 3: faq_answer
      │                        │     └── 인라인 FAQ DB
      │                        └── Tool 4: market_analysis
      │                              └── cleaned_onnuri.csv 집계 (Pandas)
      │                   Gemini 2.5 Flash (LLM 최종 응답)
      │
      └── GET  /api/report  →  backend/routers/report.py
                                └── Pandas 필터 + Matplotlib 차트 + fpdf2 PDF
```

### 챗봇 요청 처리 흐름

1. React UI 질문 입력 → `POST /api/chat`
2. LangGraph Agent가 질문 유형 분석 → 적합한 Tool 선택
3. Tool 실행 (Pandas 필터링 / ChromaDB 유사도 검색 / FAQ 매칭 / 입지 경쟁도 분석)
4. Gemini 2.5 Flash가 Tool 결과를 바탕으로 자연어 답변 생성
5. JSON 응답 → React 채팅 버블 렌더링

### Agent Tool 구성

| Tool | 역할 | 사용 시점 |
|------|------|-----------|
| `pandas_filter` | 지역·품목·디지털/지류 조건 정형 필터링, 통계 집계 | 구체적인 조건 검색, 개수 질문 |
| `rag_search` | ChromaDB 벡터 유사도 검색 (MMR) | "분위기 좋은 카페" 등 자연어 묘사 |
| `faq_answer` | 상품권 정책·사용법·규정 FAQ | 유효기간, 환불, 할인율, 구입처 등 |
| `market_analysis` | 지역·업종 입지 경쟁도 분석 (가맹점 수, 전국 평균 대비 포화도, 디지털 비율) | "이 지역에 카페 차리면 어때?", "경쟁이 심한가요?" 등 창업 입지 질문 |

---

## RAG 파라미터 튜닝 실험 결과

> 실험 스크립트: `experiments/chunk_tuning.py` | 결과 데이터: `experiments/chunk_experiment.csv`

### 실험 조건

| 파라미터 | 테스트 값 | 고정값 |
|----------|-----------|--------|
| `chunk_size` | 500 / 1000 / 2000 | — |
| `k` (검색 문서 수) | 5 / 10 | — |
| `lambda_mult` (MMR 다양성) | — | **0.7** |
| 샘플 문서 수 | — | 5,000건 |
| 임베딩 모델 | — | `gemini-embedding-001` |

### 정확도 측정 기준

각 조합마다 고정 질문 5개를 실행하고, 검색된 문서가 해당 기준을 만족하는 비율을 정확도로 계산했습니다.

| 질문 | 정확도 판별 기준 |
|------|-----------------|
| "서울 음식점" | `소재지`에 "서울" 포함 |
| "경기 자전거 매장" | `소재지`에 "경기" 포함 |
| "디지털 가능한 카페" | `디지털형 가맹 여부 == Y` |
| "분위기 좋은 한식집" | `취급품목`에 한식 관련 키워드 포함 |
| "부산 카페" | `소재지`에 "부산" 포함 |

### 실험 결과

| chunk_size | k | 서울 음식점 | 경기 자전거 | 디지털 카페 | 한식집 | 부산 카페 | **평균** |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 500 | **5** | 100% | 80% | 100% | 100% | 80% | **92%** |
| 500 | 10 | 90% | 90% | 100% | 100% | 70% | 90% |
| 1000 | **5** | 100% | 80% | 100% | 100% | 80% | **92%** |
| 1000 | 10 | 90% | 90% | 100% | 100% | 70% | 90% |
| 2000 | **5** | 100% | 80% | 100% | 100% | 80% | **92%** |
| 2000 | 10 | 90% | 90% | 100% | 100% | 70% | 90% |

### 변경 전/후 비교

| 설정 | chunk_size | chunk_overlap | k |
|------|:---:|:---:|:---:|
| **변경 전** (`rag_setup.py` 기존) | 1000 | 200 | 10 |
| **변경 후** (실험 결과 채택) | 500 | 100 | **5** |

| 질문 | 변경 전 (1000/k=10) | 변경 후 (500/k=5) | 변화 |
|------|:---:|:---:|:---:|
| 서울 음식점 | 90% | **100%** | +10% |
| 경기 자전거 매장 | 90% | 80% | -10% |
| 디지털 가능한 카페 | 100% | **100%** | 0% |
| 분위기 좋은 한식집 | 100% | **100%** | 0% |
| 부산 카페 | 70% | **80%** | +10% |
| **평균** | 90% | **92%** | **+2%** |

> **chunk_size 단독 효과 없음**: 가맹점 1건 텍스트가 평균 ~120자로 짧아 500·1000·2000 모두 실질 청킹이 일어나지 않아 chunk_size 변경에 따른 정확도 차이는 없었음.  
> **실질 개선 요인은 k 감소 (10 → 5)**: k가 작을수록 상위 유사도 문서만 반환되어 지역 일치율이 올라감. 서울·부산 쿼리에서 각 +10%p 개선, 평균 +2%p 상승.  
> 경기 자전거는 k=5에서 -10%p이지만, 검색 정밀도와 다양성 간 트레이드오프이며 평균 기준으로는 k=5가 우위.

### 결론 및 채택 파라미터

**채택: `chunk_size=500`, `chunk_overlap=100`, `k=5`, `lambda_mult=0.7`** (평균 정확도 92%, k=10 대비 +2%p)

---

## RAGAS 기반 rag_search Tool 품질 평가

> 평가 스크립트: `experiments/ragas_eval.py` | 결과 데이터: `experiments/ragas_result.csv`

### 왜 RAGAS인가

위 `chunk_tuning.py` 실험은 "검색된 문서의 지역·키워드가 정답 조건을 포함하는가"라는 **규칙 기반 정확도**만 측정할 수 있었습니다. 하지만 `rag_search` Tool은 "분위기 좋은 한식집", "조용히 혼밥하기 좋은 곳"처럼 **정답이 하나로 딱 떨어지지 않는 자연어 질문**을 다루기 때문에, 규칙 기반 채점만으로는 "검색 결과에 실제로 근거해서 답했는가", "질문과 관련 있는 내용을 답했는가" 같은 응답 품질을 판단할 수 없었습니다.

RAGAS를 채택한 이유는 다음과 같습니다.

1. **LLM-as-judge 자동 평가** — 사람이 매 질문·답변을 채점하지 않아도 LLM이 대신 채점하므로, 대량의 자유형 질문에도 정량적 점수를 낼 수 있습니다.
2. **RAG 경로를 단계별로 분리 진단** — "검색이 정확한가(context_precision)", "필요한 정보를 다 가져왔는가(context_recall)", "검색 결과에 없는 내용을 지어내진 않았는가(faithfulness)", "질문과 관련된 답을 했는가(answer_relevancy)"를 각각 따로 측정해, 문제가 **검색 단계**에 있는지 **답변 생성 단계**에 있는지 구분할 수 있습니다.
3. **기존 스택 재사용** — `src/llm_config.py`의 `get_llm()`, `get_embeddings()`(`GoogleGenerativeAIEmbeddings`)를 RAGAS의 `LangchainLLMWrapper` / `LangchainEmbeddingsWrapper`로 그대로 감싸서 채점자로 재사용했습니다. 별도 평가 인프라나 다른 모델을 추가로 붙일 필요가 없습니다. (평가 LLM은 `get_llm()`이 반환하는 모델을 그대로 따라가며, 현재는 `gemini-3.1-flash-lite`입니다.)
4. **chunk_tuning.py 실험을 보완** — chunk_tuning이 "검색 파라미터(k, chunk_size) 튜닝"에 초점을 맞췄다면, RAGAS 평가는 그 위에서 실제 사용자에게 나가는 **최종 자연어 응답의 품질**을 검증하는 상위 레벨 평가로 채택했습니다.

### 평가 방법

Agent 전체(`create_react_agent`)를 거치면 `pandas_filter` 등 다른 Tool로 분기될 수 있어, `rag_search` 경로만 분리해서 평가합니다.

1. `rag_search` Tool을 직접 호출해 벡터 검색 결과(context)를 얻는다.
2. 검색 결과만 근거로 LLM(`get_llm()`)이 최종 답변을 생성한다. (Agent의 "도구 결과를 자연스럽게 요약" 단계 재현)
3. (질문, 답변, context, reference) 조합을 RAGAS 4개 지표로 채점한다.
4. 질문 하나를 처리·채점할 때마다 바로 `ragas_result.csv`에 append — 무료 티어 일일 한도 때문에
   중간에 실패해도 그 전까지 채점된 질문은 파일에 남는다.

질문도 한 번에 하나씩만 순차 처리하고, API 호출 사이마다 `SLEEP_SECONDS`(5초)만큼 대기해
순간 요청량을 최소화한다 (무료 티어 레이트리밋 대응).

| 항목 | 값 |
|------|-----|
| 평가 대상 | `rag_search` Tool (RAG 경로) |
| LLM (답변 생성·채점) | `src.llm_config.get_llm()` (현재 `gemini-3.1-flash-lite`) |
| 임베딩 | `GoogleGenerativeAIEmbeddings` (`gemini-embedding-001`) |
| 지표 | faithfulness, answer_relevancy, context_precision, context_recall |

### 평가 지표 설명

| 지표 | 한 줄 요약 | 상세 설명 |
|------|-----------|----------|
| **context_precision** | 검색이 정확한가 | 검색된 문서들이 실제로 정답과 관련 있는 문서인지를 측정합니다. 관련 없는 문서가 섞여 있을수록 낮아집니다. |
| **context_recall** | 필요한 정보를 다 가져왔는가 | 정답에 필요한 정보가 검색 결과에 포함되어 있는지를 측정합니다. 필요한 근거를 빠뜨릴수록 낮아집니다. |
| **faithfulness** | 검색 결과에 없는 내용을 지어내진 않았는가 | 생성된 답변의 각 문장이 검색된 컨텍스트로 실제 뒷받침되는 비율입니다. 컨텍스트에 없는 내용을 답변에 포함할수록 낮아집니다. |
| **answer_relevancy** | 질문과 관련된 답을 했는가 | 생성된 답변이 원래 질문에 얼마나 관련 있는지를 측정합니다. 질문과 동떨어진 내용을 답할수록 낮아집니다. |

### 평가 질문 3개

| # | 질문 |
|---|------|
| 1 | 분위기 좋은 한식집 추천해줘 |
| 2 | 서울에서 디지털 상품권 되는 카페 알려줘 |
| 3 | 조용히 혼밥하기 좋은 곳 |

> `reference`(context_recall/precision 계산용 정답)는 retriever(k=5, mmr)가 실제로
> 반환하는 상위 문서의 상호명·지역·품목을 그대로 반영해 작성한 골든셋입니다
> (`ragas_eval.py`의 `REFERENCES`). vectordb·retriever 설정이 바뀌면 재확인이 필요합니다.

### 실행 결과

`gemini-3.1-flash-lite` 기준, 3개 질문 모두 처리 완료. `answer_relevancy`는 이 모델이
한 번의 호출에서 다중 candidate를 생성하지 못해 `AnswerRelevancy(strictness=1)`로
후보 1개만 생성하도록 낮춰서 계산했습니다.

| 질문 | faithfulness | answer_relevancy | context_precision | context_recall |
|------|:---:|:---:|:---:|:---:|
| 분위기 좋은 한식집 추천해줘 | 0.000 | 0.753 | 0.0 | 1.0 |
| 서울에서 디지털 상품권 되는 카페 알려줘 | 0.500 | 0.860 | 0.0 | 1.0 |
| 조용히 혼밥하기 좋은 곳 | 0.250 | 0.000 | 0.0 | 1.0 |
| **평균** | **0.250** | **0.538** | **0.0** | **1.0** |

**해석 및 한계**

- **context_recall = 1.0**: `REFERENCES`를 구체적인 상호명·지역 골든셋으로 다시 쓰자 0.0 → 1.0으로 바뀌었습니다. 검색이 필요한 정보를 실제로 다 가져오고 있다는 뜻입니다.
- **context_precision = 0.0**: context_recall이 1.0인 걸 보면 검색 자체의 문제는 아니고, legacy `context_precision` 지표가 각 검색 결과를 reference와 비교해 랭킹 순서를 매기는 방식 자체의 특성으로 보입니다. 원인은 아직 명확히 파악하지 못해 추가 조사가 필요합니다.
- **answer_relevancy**: 0.753 / 0.860 / 0.0 (평균 0.538). 세 번째 질문("조용히 혼밥하기 좋은 곳")에서는 챗봇이 "혼밥 분위기 정보는 검색 결과에 없다"고 사실대로 회피 답변을 해서 관련도가 0으로 나왔습니다 — 이는 hallucination을 피한 결과이므로 faithfulness 관점에선 오히려 바람직한 동작입니다.
- **faithfulness**: 0.0 / 0.5 / 0.25 (평균 0.25) — 생성된 답변 문장이 검색된 컨텍스트로 실제 뒷받침되는 비율입니다. 세 질문 모두 컨텍스트에 없는 "분위기" 관련 서술을 답변에 섞어서 낮게 나오는 경향이 있습니다. 답변 프롬프트에서 "검색 결과에 없는 내용은 지어내지 마세요"를 더 강하게 강제하면 개선 여지가 있어 보입니다.

---

## 온톨로지 기반 카테고리 계층 구조 설계

> 매핑 정의: `src/category_taxonomy.py` | 시각화 스크립트: `experiments/visualize_ontology.py`

### 배경

`취급품목` 컬럼은 22,113개의 자유 입력 텍스트로, "한식" / "음식(한식)" / "중식" / "분식"처럼 표기가 제각각입니다. 기존에는 `str.contains(category)` 단순 문자열 포함 검색만 사용해서, "음식점"으로 검색하면 정확히 "음식점"이라는 문자열이 들어간 값만 잡히고 "한식"·"중식"·"분식" 등 실제로는 음식점에 속하는 값은 빠지는 문제가 있었습니다. 또한 `chatbot.py`에 6개 항목짜리 매핑이 있었지만 `search_engine.py`와 공유되지 않아 도구마다 검색 결과가 달랐습니다.

그래프 DB(Neo4j/RDF)를 새로 두기보다, 기존 pandas/ChromaDB 구조를 그대로 두고 바로 적용 가능한 **경량 카테고리 태그 매핑**을 선택했습니다.

### 설계

- 실제 데이터의 상위 빈도 취급품목(`value_counts` 상위권)을 기준으로 **대분류 21개 → 하위 원본 키워드 리스트** 형태의 매핑을 사람이 직접 구성 (`CATEGORY_EXPANSIONS: dict[str, list[str]]`).
- `expand_category(term)` 함수가 사용자가 입력한 category를 관련 키워드 전체로 확장해서 검색.
- 매핑에 없는 term은 원본 그대로 반환(fallback)해 기존 동작과 호환.

### 적용 위치

- `chatbot.py`의 `pandas_filter`, `market_analysis` Tool, `extract_area_category()` 헬퍼
- `search_engine.py`의 `statistics()` 함수
- `str.contains(..., regex=False)` 명시 — 키워드에 괄호가 포함된 값(`음식(한식)`, `도소매(의류)`)이 정규식 그룹으로 잘못 해석되어 매칭이 깨지는 문제를 함께 수정.

### 효과 (필터링 매칭 건수 변화)

| category | 적용 전 (단순 substring) | 적용 후 (계층 확장) |
|---|---:|---:|
| 음식점 | 3,132 | 23,226 |
| 한식 | 13,427 | 15,287 |
| 카페 | 858 | 5,055 |
| 고기 | 839 | 8,682 |
| 미용 | 4,390 | 5,204 |
| 자전거 | 98 | 100 |

`chunk_tuning.py` 실험의 "chunk_size는 효과가 없고 k가 실질적 개선 요인이었다"는 결론과 별개로, 검색 **재현율(recall)** 을 끌어올리는 지점은 벡터 파라미터가 아니라 이 카테고리 매핑 쪽이었습니다 — "음식점" 검색이 3,132건에서 23,226건으로 늘어난 게 그 예시입니다.

### 시각화

<p align="center">
  <img src="./experiments/ontology_graph_overview.png" width="600" alt="카테고리 태그 매핑 개요 그래프">
</p>
<p align="center"><sub>대분류 개요 그래프 — 노드 크기는 하위 키워드 수, 선은 키워드를 공유하는 대분류 간 연결(예: 음식점 ↔ 한식/중식/일식/분식)</sub></p>

<p align="center">
  <img src="./experiments/ontology_graph.png" width="700" alt="카테고리 태그 매핑 전체 그래프">
</p>
<p align="center"><sub>전체 그래프 — 대분류(큰 노드) → 취급품목 키워드(작은 노드) 스포크 레이아웃</sub></p>

---

## 실행 방법

### 1. 사전 준비

```bash
# conda 가상환경 생성 및 활성화
conda create -n new_env python=3.11
conda activate new_env

# Python 패키지 설치
pip install -r requirements.txt

# Node.js 패키지 설치 (프론트엔드)
cd frontend
npm install
cd ..
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일 생성:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

### 3. 벡터DB 구축 (최초 1회)

```bash
# 노트북으로 데이터 전처리
jupyter notebook
# 순서: 01_data_exploration.ipynb → 02_preprocessing.ipynb

# 벡터DB 생성 (약 10~20분, OpenAI API 비용 약 $0.30)
python -m src.rag_setup
```

> `vectordb/chroma_db/` 가 이미 존재하면 기존 DB를 재사용합니다.

### 4. 서버 실행

터미널 1 — 백엔드:

```bash
uvicorn backend.main:app --reload
```

터미널 2 — 프론트엔드 개발 서버:

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/chat` | 챗봇 질문 처리 |
| `GET` | `/api/report` | PDF 보고서 생성 및 다운로드 |
| `GET` | `/health` | 서버 상태 확인 |

### POST /api/chat 요청 예시

```json
{
  "message": "서울 디지털 가능한 음식점 알려줘",
  "history": [["이전 질문", "이전 답변"]]
}
```

### GET /api/report 파라미터

| 파라미터 | 타입 | 예시 | 설명 |
|----------|------|------|------|
| `region` | string | `서울` | 지역명 (빈 값 = 전체) |
| `category` | string | `카페` | 업종 (빈 값 = 전체) |
| `digital_only` | bool | `true` | 디지털 가맹점만 |
| `paper_only` | bool | `false` | 지류 가맹점만 |

---

## 데이터

### cleaned_onnuri.csv 주요 컬럼

| 컬럼명 | 설명 |
|--------|------|
| `가맹점명` | 상호명 |
| `소재지` | 주소 (지역 필터 기준) |
| `취급품목` | 업종 분류 |
| `디지털형 가맹 여부` | `Y` / `N` |
| `지류형 가맹 여부` | `Y` / `N` |
| `소속 시장명(또는 상점가)` | 소속 전통시장명 |

- 전국 약 **15만 건** 가맹점 데이터
- 원본: 공공데이터포털 소상공인시장진흥공단 제공

---

## 주의사항

- **벡터DB** (`vectordb/chroma_db/`): 용량 약 500MB~1GB, git 추적 제외
- **API 키**: `.env` 파일은 git에 포함하지 않음. OpenAI·Google API 키 모두 필요
- **한국어 PDF**: Windows 맑은 고딕 폰트 (`C:\Windows\Fonts\malgun.ttf`) 사용 — Windows 환경 전용

---

## 데이터 플로우

### 리팩토링 전
DataFlow<br>
<p align="center">
  <img src="./docs/DataFlow.png" width="600" alt="DataFlow">
</p>

### 리팩토링 후
리팩토링 DataFlow<br>
<p align="center">
  <img src="./docs/refactor/리팩토링 DataFlow.png" width="600" alt="리팩토링 DataFlow">
</p>

## 시스템 아키텍처 다이어그램

### 리팩토링 전
시스템 아키텍처<br>
<p align="center">
  <img src="./docs/시스템 아키텍처.png" width="600" alt="시스템 아키텍처">
</p>

### 리팩토링 후
리팩토링 시스템 아키텍처<br>
<p align="center">
  <img src="./docs/refactor/리팩토링 시스템 아키텍처.png" width="600" alt="리팩토링 시스템 아키텍처">
</p>

## 시연 영상

<p align="center">
  <img src="./docs/refactor/시연영상.gif" width="700" alt="시연 영상">
</p>

입지 분석 시연<br>
<p align="center">
  <img src="./docs/refactor/입지분석.gif" width="700" alt="입지 분석 시연 영상">
</p>

---

## 실행 화면

### 리팩토링 전
RAG 기반 추천 답변<br>
<p align="center">
  <img src="./docs/RAG 기반 답변.png" width="500" alt="RAG 기반 답변">
</p>
지역+업종 답변 <br>
<p align="center">
  <img src="./docs/경기 자전거 가맹점 수.png" width="500" alt="경기 자전거 가맹점 수">
</p>
지역별 가맹점 수<br>
<p align="center">
  <img src="./docs/서울 가맹점 수.png" width="500" alt="서울 가맹점 수">
</p>

지역별 업종 비율<br>
<p align="center">
  <img src="./docs/서울 업종 비율.png" width="500" alt="서울 업종 비율">
</p>

### 리팩토링 후

사용자 매뉴얼<br>
<p align="center">
  <img src="./docs/refactor/사용자 매뉴얼.png" width="500" alt="사용자 매뉴얼 페이지 - 가상환경 구축 안내">
</p>

사용자 매뉴얼(2)<br>
<p align="center">
  <img src="./docs/refactor/사용자 매뉴얼(2).png" width="500" alt="사용자 매뉴얼 페이지 - 프론트엔드 환경 설정 및 빠른 시작">
</p>

질문 유형 가이드<br>
<p align="center">
  <img src="./docs/refactor/질문 유형 가이드.png" width="500" alt="질문 유형 가이드 페이지 - 추천/검색 질문 예시">
</p>

질문 유형 가이드(2)<br>
<p align="center">
  <img src="./docs/refactor/질문 유형 가이드(2).png" width="500" alt="질문 유형 가이드 페이지 - 통계 질문 예시">
</p>

시스템 아키텍처<br>
<p align="center">
  <img src="./docs/refactor/시스템 아키텍처.png" width="500" alt="DataFlow / 아키텍처 페이지 - 시스템 아키텍처 다이어그램">
</p>

DataFlow<br>
<p align="center">
  <img src="./docs/refactor/DataFlow.png" width="500" alt="DataFlow / 아키텍처 페이지 - 데이터 흐름 다이어그램">
</p>

데이터 인사이트<br>
<p align="center">
  <img src="./docs/refactor/데이터 인사이트.png" width="500" alt="데이터 인사이트 대시보드 - 지역별 가맹점 수">
</p>

데이터 인사이트(2)<br>
<p align="center">
  <img src="./docs/refactor/데이터 인사이트(2).png" width="500" alt="데이터 인사이트 대시보드 - 연도별 판매·회수금액 추이">
</p>

보고서 생성<br>
<p align="center">
  <img src="./docs/refactor/보고서 생성.png" width="500" alt="보고서 생성 페이지 - 지역/업종/가맹 유형 조건 선택">
</p>

보고서1pg<br>
<p align="center">
  <img src="./docs/refactor/보고서1pg.png" width="500" alt="생성된 PDF 보고서 1페이지 - 적용 필터 및 요약 통계">
</p>

보고서2pg<br>
<p align="center">
  <img src="./docs/refactor/보고서2pg.png" width="500" alt="생성된 PDF 보고서 2페이지 - 가맹 유형 분포 파이 차트">
</p>

보고서3pg<br>
<p align="center">
  <img src="./docs/refactor/보고서3pg.png" width="500" alt="생성된 PDF 보고서 3페이지 - 가맹점 목록">
</p>

보고서4pg<br>
<p align="center">
  <img src="./docs/refactor/보고서4pg.png" width="500" alt="생성된 PDF 보고서 4페이지 - 가맹점 목록 (계속)">
</p>

디지털 상품권 불가능 가맹점 질문<br>
<p align="center">
  <img src="./docs/refactor/챗봇 디지털 불가능.png" width="500" alt="챗봇 - 서울 디지털 상품권 사용 불가 가맹점 안내">
</p>

RAG 기반 추천 답변<br>
<p align="center">
  <img src="./docs/refactor/서울 음식점 알려줘.png" width="500" alt="챗봇 - 서울 음식점 가맹점 안내">
</p>

지역 + 업종 + 디지털 사용 가능여부<br>
<p align="center">
  <img src="./docs/refactor/서울 음식점 디지털.png" width="500" alt="챗봇 - 서울 한식점 디지털 상품권 사용 가능 여부 안내">
</p>

지역 업종 통계<br>
<p align="center">
  <img src="./docs/refactor/서울 가맹점 업종 통계.png" width="500" alt="챗봇 - 서울 가맹점 업종별 통계 안내">
</p>

디지털 상품권 안되는 곳<br>
<p align="center">
  <img src="./docs/refactor/디지털 상품권 안되는 곳.png" width="500" alt="챗봇 - 디지털 상품권 사용 불가 가맹점 목록 안내">
</p>

지역 + 업종 추천 답변<br>
<p align="center">
  <img src="./docs/refactor/서울 카페 추천.png" width="500" alt="챗봇 - 서울 카페 추천">
</p>

서울 업종 카페 추천<br>
<p align="center">
  <img src="./docs/refactor/서울 업종 카페 추천.png" width="500" alt="챗봇 - 조건 기반 서울 카페 가맹점 추천">
</p>

정책 검색<br>
<p align="center">
  <img src="./docs/refactor/정책 검색.png" width="500" alt="챗봇 - 상품권 정책 FAQ 검색">
</p>

상품권 사용처 유효기간<br>
<p align="center">
  <img src="./docs/refactor/상품권 사용처 유효기간.png" width="500" alt="챗봇 - 상품권 사용처 및 유효기간 안내">
</p>

입지분석<br>
<p align="center">
  <img src="./docs/refactor/입지분석.png" width="500" alt="챗봇 - 입지분석">
</p>

