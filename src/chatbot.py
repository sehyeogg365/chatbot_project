'''
목적: 챗봇 로직 개발
내용:
- LLM 연동
- 질문 유형 분류 로직
- 프롬프트 엔지니어링 (ChatPromptTemplate)
- 체인 구성 (LCEL)
- 출력 파서 (StrOutputParser)
- 하이브리드 검색 테스트
- 다양한 질문 테스트

출력: 검증된 챗봇 로직
'''
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# 1. 벡터 스토어 및 임베딩 (사용하던 것과 동일)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
# 2. LLM 및 RAG 체인 (이 부분이 핵심)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.search_engine import statistics
from typing import Optional
from pathlib import Path
# 3. 환경변수 로드  
current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / "api_keys.txt"

load_dotenv(env_path)

# ============================================
# [단계 1] 벡터 스토어 로드
# ============================================
print("1️⃣ 벡터 스토어 로딩 중...")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    persist_directory="vectordb/chroma_db", 
    embedding_function=embeddings
)

print(f"✅ 벡터 스토어 로드 완료! (저장된 문서: {vectorstore._collection.count()}개)")

# ============================================
# [단계 2] 리트리버 생성
# ============================================
print("\n2️⃣ 리트리버 생성 중...")

retriever = vectorstore.as_retriever(
    search_type="mmr",  # MMR (Maximum Marginal Relevance) 검색
    search_kwargs={
        "k": 1000,              # 상위 1000개 검색
        "lambda_mult": 0.7,   # 다양성 vs 관련성 (0.7 = 관련성 우선)
        "filter": {"category": "자전거"} # 메타데이터에 카테고리가 저장되어 있어야 함
    }
)

print("✅ 리트리버 생성 완료!")

# ============================================
# [단계 3] LLM 초기화
# ============================================
print("\n3️⃣ LLM 초기화 중...")

llm = ChatOpenAI(
    model_name="gpt-3.5-turbo", 
    temperature=0.7  # 약간의 창의성 (0=결정적, 1=창의적)
)

print("✅ LLM 초기화 완료!")

# ============================================
# [단계 4] 프롬프트 템플릿 (수업 내용 적용!)
# ============================================
print("\n4️⃣ 프롬프트 템플릿 생성 중...")

# ChatPromptTemplate 사용 (수업에서 배운 방식)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """당신은 온누리상품권 가맹점 안내 전문 챗봇입니다.

역할:
- 사용자가 원하는 가맹점을 찾도록 도와줍니다
- 검색 결과를 바탕으로 정확하고 친절하게 답변합니다
- 결과가 많으면 범위를 좁히도록 추가 질문을 유도합니다

답변 형식:
1. 검색된 가맹점 정보를 요약합니다
2. 주요 가맹점 3-5개를 소개합니다
3. 필요시 추가 질문을 제안합니다
"""),
    ("human", """검색된 가맹점 정보:
{context}

사용자 질문: {question}

위 정보를 바탕으로 답변해주세요.""")
])

print("✅ 프롬프트 템플릿 생성 완료!")

# ============================================
# [단계 5] 출력 파서 (수업 내용 적용!)
# ============================================
output_parser = StrOutputParser()

# ============================================
# [단계 6] RAG 체인 구성 (LCEL 패턴)
# ============================================
print("\n5️⃣ RAG 체인 구성 중...")

def format_docs(docs):
    """검색된 문서를 하나의 문자열로 포맷팅"""
    return "\n\n".join([
        f"[가맹점 {i+1}]\n{doc.page_content}" 
        for i, doc in enumerate(docs)
    ])

# LCEL (LangChain Expression Language) 체인
rag_chain = (
    {
        "context": retriever | format_docs,  # 검색 → 포맷팅
        "question": RunnablePassthrough()     # 질문 그대로 전달
    }
    | prompt_template   # 프롬프트 적용
    | llm               # LLM 호출
    | output_parser     # 문자열로 파싱
)

print("✅ RAG 체인 구성 완료!")

# ============================================
# [단계 7] 챗봇 함수 (체인 활용)
# ============================================

def ask_question_v1(query: str) -> str:
    """
    RAG 체인을 사용한 질문 답변
    
    Args:
        query: 사용자 질문
        
    Returns:
        str: 챗봇 응답
    """
    response = rag_chain.invoke(query)
    return response


def ask_question_v2_with_history(query: str, history: list = None) -> str:
    """
    RAG 검색 (Pandas 1차 필터링 추가)  RAG에도 Pandas 필터링 추가
    """
    # ============================================
    # 1. 지역/카테고리 추출
    # ============================================
    area, category = extract_area_category(query)
    
    print(f"🔍 RAG 추출: area={area}, category={category}")
    
    # ============================================
    # 2. Pandas로 1차 필터링 (area 있으면)
    # ============================================
    filtered_df = df.copy()
    
    if area:
        filtered_df = filtered_df[
            filtered_df['소재지'].str.contains(area, na=False)
        ]
        print(f"✅ {area} 필터: {len(filtered_df)}개")
    
    if category:
        # 카테고리 확장
        category_expansions = {
            "카페": ["카페", "커피", "디저트", "베이커리"],
            "음식점": ["음식점", "식당", "한식", "중식", "일식"],
            "자전거": ["자전거", "바이크"],
        }
        
        keywords = category_expansions.get(category, [category])
        
        mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for keyword in keywords:
            mask |= filtered_df['취급품목'].str.contains(
                keyword, na=False, case=False
            )
        
        filtered_df = filtered_df[mask]
        print(f"✅ {category} 필터: {len(filtered_df)}개")
    
    # ============================================
    # 3. 결과 없으면 조기 반환
    # ============================================
    if len(filtered_df) == 0:
        return f"{area or '해당 지역'}에 {category or '관련'} 가맹점이 없습니다."
    
    # ============================================
    # 4. 필터링된 데이터를 문서로 변환
    # ============================================
    docs_text = ""
    for i, (_, row) in enumerate(filtered_df.head(20).iterrows(), 1):
        docs_text += f"""
    [{i}]
    가맹점명: {row['가맹점명']}
    소재지: {row['소재지']}
    취급품목: {row['취급품목']}
    디지털: {'가능' if row.get('디지털형 가맹 여부')=='Y' else '불가'}
    """
    # ============================================
    # 5. 히스토리 처리
    # ============================================
    history_text = ""
    if history:
        history_text = "\n".join([
            f"사용자: {user}\n챗봇: {bot}"
            for user, bot in history[-3:]
        ])    
    """
    대화 히스토리를 포함한 질문 답변
    
    Args:
        query: 사용자 질문
        history: 이전 대화 리스트 [(user_msg, bot_msg), ...]
        
    Returns:
        str: 챗봇 응답
    """
    # 히스토리를 문자열로 변환
    history_text = ""
    if history:
        history_text = "\n".join([
            f"사용자: {user}\n챗봇: {bot}" 
            for user, bot in history[-3:]  # 최근 3개만
        ])
    
    # 히스토리 포함 프롬프트
    prompt_with_history = ChatPromptTemplate.from_messages([
        ("system", """당신은 온누리상품권 가맹점 안내 전문 챗봇입니다.
        이전 대화 맥락을 고려하여 자연스럽게 대화를 이어가세요.
         다음 규칙을 반드시 따르세요:


            [답변 원칙]
            1. 근거 중심: 반드시 제공된 가맹점 정보(Context)를 기반으로 답변하세요.
            2. 매칭 우선순위:
            - 사용자가 요청한 [지역]과 [업종]에 가장 잘 부합하는 곳을 우선적으로 나열하세요.
            - 요청한 지역이 광범위할 경우(예: 서울), 해당 지역 내 가맹점을 폭넓게 포함하세요.
            3. 정보 부족 시 대응: 
            - 조건에 완벽히 일치하는 곳이 없더라도, 맥락상 유사한 가맹점이 있다면 "요청하신 조건과 가장 유사한 가맹점 정보입니다"라는 안내와 함께 정보를 제공하세요.
            - 데이터가 정말 하나도 없을 때만 "죄송합니다. 해당 조건에 맞는 가맹점을 찾을 수 없습니다."라고 정중히 답하세요.
            4. 출력 형식 (가급적 유지):
            - 가맹점명: 
            - 위치: 
            - 주요품목: 
            (디지털 온누리상품권 사용 가능 여부가 있다면 함께 언급해 주세요.)

            5. 대화 맥락 유지: 이전 대화에서 언급된 지역이나 업종을 기억하여 자연스럽게 대답하세요.
         
            [검증 규칙]
            1. 적극적으로 추천하세요.
            2. 관련 있는 가맹점도 추천하세요.
            3. 유사한 가맹점도 도움이 됩니다.

            💡 예시:
            - "카페" → "커피", "디저트"도 OK
            - "고기" → "구이", "삼겹살"도 OK

            → LLM: "비슷한 곳을 추천드립니다!" ✅
         """
         ),
                ("human", """이전 대화:
                {history}

                검색된 가맹점 정보:
                {context}

                사용자 질문: {question}

                위 정보를 바탕으로 답변해주세요.
                정확히 일치하지 않아도 관련 있으면 추천하세요.      
                 """)
    ])
    
    # 임시 체인
    chain_with_history = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "history": lambda x: history_text
        }
        | prompt_with_history
        | llm
        | output_parser
    )
    
    response = chain_with_history.invoke(query)
    return response


# ============================================
# [단계 8] 테스트
# ============================================
# print("\n" + "="*60)
# print("6️⃣ 챗봇 테스트 시작")
# print("="*60)

# # 테스트 질문들
# test_queries = [
#     "경기도 가맹점을 알려줘",
#     "서울 음식점 찾아줘",
#     "디지털 상품권 되는 카페 알려줘"
# ]

# for i, query in enumerate(test_queries, 1):
#     print(f"\n[질문 {i}] {query}")
#     print("-" * 60)
    
#     # 체인 활용 답변
#     answer = ask_question_v1(query)
#     print(answer)
#     print()

# ============================================
# [단계 9] 대화형 테스트
# ============================================
print("\n" + "="*60)
print("7️⃣ 대화형 챗봇 테스트 (히스토리 포함)")
print("="*60)

conversation_history = []

# 질문 분류 함수
def classify_question(query: str) -> str:
    """
    질문 유형 분류
    """

    # 1. STAT 키워드 (확실한 통계 질문)
    stat_keywords = ["몇 개", "갯수", "개수", "통계", "얼마나", "비율", "수" ,"%"]

    for kw in stat_keywords:
        if kw in query:
            return "STAT"
        
    # 2.지역 + 업종 조합 → STAT로 처리 (정확한 검색)
    areas = ["서울", "경기", "부산", "대구", "인천", "광주", "대전",
             "울산", "세종", "강원", "충북", "충남", "전북", "전남",
             "경북", "경남", "제주"]
    
    categories = ["자전거", "안경", "미용", "카페", "음식점", "한식", "고기"]
    
    has_area = any(area in query for area in areas)
    has_category = any(cat in query for cat in categories)

    # 지역 + 카테고리 → STAT (정확한 검색 필요)
    if has_area and has_category:
        recommend_keywords = ["추천", "알려", "소개", "찾아", "보여"]
        has_recommend = any(kw in query for kw in recommend_keywords)

        if has_recommend:
            print("🔍 [지역+업종+추천] → STAT_RECOMMEND 모드")
            return "RAG"
        else:
            print("🔍 [지역+업종] 감지 → STAT 모드")
            return "STAT"    

    

    # 3. RAG 키워드 (확실한 추천/검색 질문)
    rag_keywords = [
        "추천", "알려줘", "찾아줘", "보여줘"
        "어디", "뭐", "무엇", "어떤",
        "좋은", "맛있는", "유명한", "인기",
        "가고 싶", "먹고 싶", "사고 싶",
        "근처", "주변", "역",
        "~에서", "~에"
    ]
    
    for kw in rag_keywords:
        if kw in query:
            print(f"🔍 [RAG 키워드 '{kw}'] 감지 → RAG 모드")
            return "RAG"
        
    
    return "RAG"

    
    
    

def classify_stat_detail(query: str) -> str:
    """
    STAT 질문의 세부 유형 분류
    """
    # if "비율" in query or "퍼센트" in query or "%" in query:
    #     return "RATIO"
    # "비율" 또는 "업종" → CATEGORY
    if any(k in query for k in ["비율", "퍼센트", "%", "업종", "통계"]):
        return "CATEGORY"
    
    return "COUNT"

# 질문 파싱을 단일 함수로 통합
def parse_stat_query(query: str):
    area, category = extract_area_category(query)
    stat_type = classify_stat_detail(query)
    return area, category, stat_type

# 갯수 세기 
def handle_stat_count(area: str, category: Optional[str]) -> str:
    # area = next((a for a in AREAS if a in query), None)
    # category = next((c for c in CATEGORIES if c in query), None)

    stats = statistics(df, area=area, category=category)
    if "message" in stats:
        return stats["message"]
    # ============================================
    # 1. 기본 정보
    # ============================================
    count = stats['total_count']
    result_text = f"📍 {area or '전국'} 지역"
    if category:
        result_text += f" **{category}** 관련"
    result_text += f" 가맹점은 총 **{count:,}개**입니다.\n\n"
    
    # ============================================
    # 2. 종류별 분포 (category가 있을 때만)
    # ============================================
    if category and count > 0:
        result_text += f"📊 **{category} 종류별 분포:**\n"
        
        # 취급품목에서 카테고리 포함된 것 추출
        product_counter = {}
        filtered_df = stats.get('data', df[df['소재지'].str.contains(area, na=False)])
        
        for _, row in filtered_df.iterrows():# _는 인덱스 번호인데 사용하지 않으므로 생략하고, row에 행 데이터를 담는다.
            items = str(row['취급품목']).split(',')# '취급품목' 컬럼의 데이터를 문자열로 변환한 뒤 쉼표(,)를 기준으로 자름 
            for item in items:
                item = item.strip()# 불필요한 공백을 제거
                if category in item:  # 카테고리 포함
                    if item in product_counter: # 원래 있던 품목 
                        product_counter[item] += 1
                    else: # 처음발견된 품목 
                        product_counter[item] = 1 
        
        # 전체 분포 정렬
        all_sorted = sorted(product_counter.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 5개와 나머지 분리
        top_5 = all_sorted[:5]
        others = all_sorted[5:]
        
        for product, cnt in top_5:
            result_text += f"   - {product}: {cnt}개\n"
        
        # 나머지가 있다면 '기타'로 합산 표시
        if others:
            other_sum = sum(cnt for _, cnt in others)
            result_text += f"   - 기타: {other_sum}개\n"

        # # 상위 5개
        # sorted_products = sorted(product_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # for product, cnt in sorted_products:
        #     result_text += f"  - {product}: {cnt}개\n"
        
        result_text += "\n"
    
    # ============================================
    # 3. 전체 가맹점 목록 (10개까지)
    # ============================================
    result_text += "🏪 **가맹점 목록:**\n\n"
    
    # stats에서 data 가져오기 (없으면 직접 필터링)
    if 'data' in stats:
        sample_df = stats['data']# 필터링된 데이터
    else:
        sample_df = df[df['소재지'].str.contains(area, na=False)]
        if category:
            sample_df = sample_df[
                sample_df['취급품목'].str.contains(category, na=False, case=False)
            ]
    
    # 최대 10개만
    sample_df = sample_df.head(10)
    
    for i, (_, row) in enumerate(sample_df.iterrows(), 1):# _는 인덱스 번호인데 사용하지 않으므로 생략
        result_text += f"**{i}. {row['가맹점명']}**\n"
        result_text += f"   📍 소재지: {row['소재지']}\n"
        result_text += f"   🛒 취급품목: {row['취급품목']}\n"
        
        # 디지털 여부
        digital = "✅ 가능" if row.get('디지털형 가맹 여부') == 'Y' else "❌ 불가"
        result_text += f"   💳 디지털 상품권: {digital}\n"
        
        # 소속 시장
        if pd.notna(row.get('소속 시장명(또는 상점가)')):
            result_text += f"   🏬 소속: {row['소속 시장명(또는 상점가)']}\n"
        
        result_text += "\n"
    
    # ============================================
    # 4. 더 많은 결과가 있다면
    # ============================================
    if count > 10:
        result_text += f"💡 *총 {count}개 중 10개만 표시했습니다.*\n"
    
    return result_text
    # return (
    #     f"{area} 지역"
    #     + (f" {category} 업종의 " if category else " ")
    #     + f"가맹점은 총 {stats['total_count']}개입니다."
    # )

# 업종별 통계
def handle_stat_category(area: str) -> str:
    # area = next((a for a in AREAS if a in query), None)

    stats = statistics(df, area=area)

    # (업종을 지정하지 않아야 그 지역의 전체 업종 분포를 알 수 있다)
    if "message" in stats:
        return stats["message"]
    
    # 업종 분포 가져오기 
    total_count = stats["total_count"]  # 해당 지역 전체 가맹점 수
    top_items = stats.get("top_items", {}) # 주요 품목(업종) TOP 5

    if not area:
        return "비율을 알고 싶은 지역을 지정해 주세요."

    if not top_items:
        return f"{area} 지역에 업종 통계 데이터가 없습니다."

    # 2. 결과 텍스트 생성
    result = f"📊 **{area} 지역의 주요 업종별 비중 (TOP 5)**\n"
    result += f"(전체 가맹점 수: {total_count:,}개)\n\n"

    # 3. 각 업종별로 비율 계산 (업종 개수 / 지역 전체 개수)
    # sum_ratio = 0
    result = f"{area} 지역 가맹점 분포 비율은 다음과 같습니다:\n"
    for item, cnt in top_items.items():
        ratio = (cnt / total_count) * 100
        # sum_ratio += ratio
        result += f"- **{item}**: {ratio:.1f}% ({cnt:,}개)\n"

    # 4. 나머지 항목 합산 (선택 사항)
    # if sum_ratio < 100:
    #     result += f"- **기타**: {100 - sum_ratio:.1f}%\n"

    return result

# 비율
def handle_stat_ratio(area: str, category: Optional[str] = None) -> float:
    return handle_stat_category(area)


# 통계 응답 함수

import pandas as pd
df = pd.read_csv('cleaned_onnuri.csv')

# 딕셔너리 기반 파싱 함수 
AREAS = ["강원", "경기", "경남", "경북", "광주", "대구", "대전", "부산", "서울", "세종", "울산", "인천", "전남", "전북", "제주", "충남", "충북"]
CATEGORIES = ["자전거", "카페", "안경", "음식점", "미용", "의류", "커피", "한식", "기념품", "고기", "뷔페"]

def extract_area_category(query: str):
    area = next((a for a in AREAS if a in query), None)
    category = next((c for c in CATEGORIES if c in query), None)
    return area, category

# 2. 메인 질문 처리 함수
def handle_stat_question(query: str) -> str:
    """
    통계 질문 처리 (Python이 정답을 계산)
    """
    area, category  = extract_area_category(query)
    if not area and category:
        return "지역이나 업종을 다시 지정해 주세요. 예: '서울 자전거 매장 몇 개야?'"
    
    stat_type = classify_stat_detail(query)
    # 간소화된 코드문 
    if stat_type == "CATEGORY":
        # 업종 통계 (비율 포함)
        return handle_stat_category(area)
    else:
        # 개수 세기 (상세 정보)
        return handle_stat_count(area, category)


# n번째 질문 
# Streamlit 연동
def process_query(query: str, history: list) -> str:
    q_type = classify_question(query)

    if q_type == "STAT":
        return handle_stat_question(query)

    # 🔥 RAG 전에 조건 추출
    area, category = extract_area_category(query)

    # 조건이 명확하면 → RAG에 힌트로 넣기
    if area or category:
        query = f"[지역:{area}] [업종:{category}] {query}"

    return ask_question_v2_with_history(query, history)