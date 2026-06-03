'''
목적: Tool-calling Agent 기반 챗봇 로직
구조:
  Tool 1 (pandas_filter) : 지역 / 품목 / 디지털·지류 가맹 여부 정형 필터링
  Tool 2 (rag_search)    : 벡터 유사도 검색 (자연어·분위기 기반)
  Tool 3 (faq_answer)    : 상품권 정책·사용법 FAQ
  create_agent           : 복합 조건 자동 분기 및 다중 Tool 호출
'''

from dotenv import load_dotenv
from pathlib import Path

current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir.parent / "api_keys.txt")

import pandas as pd
from typing import Optional

from langgraph.prebuilt import create_react_agent
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

from src.llm_config import get_llm, get_embeddings

# ──────────────────────────────────────────────────────────────────
# 초기화
# ──────────────────────────────────────────────────────────────────
print("1️⃣ 초기화 중...")

df = pd.read_csv("cleaned_onnuri.csv")

embeddings = get_embeddings()
vectorstore = Chroma(
    persist_directory="vectordb/chroma_db",
    embedding_function=embeddings,
)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 10, "lambda_mult": 0.7},
)

llm = get_llm(temperature=0.3)

print(f"✅ 초기화 완료 (벡터DB: {vectorstore._collection.count()}개)")

# ──────────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────────
AREAS = [
    "강원", "경기", "경남", "경북", "광주", "대구", "대전", "부산",
    "서울", "세종", "울산", "인천", "전남", "전북", "제주", "충남", "충북",
]

CATEGORY_EXPANSIONS: dict[str, list[str]] = {
    "카페":   ["카페", "커피", "디저트", "베이커리"],
    "음식점": ["음식점", "식당", "한식", "중식", "일식"],
    "자전거": ["자전거", "바이크"],
    "미용":   ["미용", "헤어", "네일", "뷰티"],
    "의류":   ["의류", "옷", "패션"],
    "고기":   ["고기", "구이", "삼겹살", "갈비"],
}

FAQ_DB: dict[str, str] = {
    "사용처":    "온누리상품권은 전통시장 및 상점가 가맹점에서만 사용할 수 있습니다. 대형마트·백화점·편의점은 사용 불가합니다.",
    "유효기간":  "온누리상품권 유효기간은 발행일로부터 5년입니다.",
    "구입처":    "농협·신한·우리·국민·하나 등 시중은행, 우체국, 농협 하나로마트에서 구입할 수 있습니다.",
    "할인":      "전통시장 활성화를 위해 액면가 대비 5~10% 할인 구매가 가능합니다. 채널에 따라 할인율이 다를 수 있습니다.",
    "디지털형":  "디지털 온누리상품권은 온누리페이 등 모바일 앱에서 충전 후 가맹점 QR코드로 결제하는 전자상품권입니다.",
    "지류형":    "지류 온누리상품권은 종이 형태로 1천·5천·1만원권이 있으며, 점주에게 직접 제출하는 방식입니다.",
    "한도":      "1인당 월 최대 100만원까지 구입 가능합니다.",
    "환불":      "구입 후 60일 이내 미사용 상품권은 100% 환불 가능합니다. 잔액이 60% 이상이면 부분 환불도 가능합니다.",
    "가맹점신청": "전통시장·상점가 점포는 소상공인진흥공단 또는 중소벤처기업부를 통해 온누리상품권 가맹 신청을 할 수 있습니다.",
}

# ──────────────────────────────────────────────────────────────────
# Tool 1: Pandas 정형 필터링
# ──────────────────────────────────────────────────────────────────
@tool
def pandas_filter(
    region: str = "",
    category: str = "",
    digital_only: bool = False,
    paper_only: bool = False,
    limit: int = 20,
) -> str:
    """
    온누리 가맹점 데이터를 정형 조건으로 필터링합니다.

    - region      : 지역명 (예: 서울, 경기, 부산). 빈 문자열이면 전국 검색.
    - category    : 취급품목 (예: 음식점, 카페, 자전거). 빈 문자열이면 전 업종.
    - digital_only: True이면 디지털형 상품권 가맹점만 반환.
    - paper_only  : True이면 지류형 상품권 가맹점만 반환.
    - limit       : 반환할 최대 가맹점 수 (기본 20).

    지역 + 디지털, 지역 + 품목 + 디지털 등 복합 조건도 처리합니다.
    통계 질문(몇 개, 얼마나)에도 사용하세요.
    """
    result_df = df.copy()

    if region:
        result_df = result_df[result_df["소재지"].str.contains(region, na=False)]

    if category:
        keywords = CATEGORY_EXPANSIONS.get(category, [category])
        mask = pd.Series([False] * len(result_df), index=result_df.index)
        for kw in keywords:
            mask |= result_df["취급품목"].str.contains(kw, na=False, case=False)
        result_df = result_df[mask]

    if digital_only:
        result_df = result_df[result_df["디지털형 가맹 여부"] == "Y"]

    if paper_only and "지류형 가맹 여부" in result_df.columns:
        result_df = result_df[result_df["지류형 가맹 여부"] == "Y"]

    total = len(result_df)
    if total == 0:
        conds = []
        if region:       conds.append(f"지역={region}")
        if category:     conds.append(f"품목={category}")
        if digital_only: conds.append("디지털=가능")
        if paper_only:   conds.append("지류=가능")
        return f"[{', '.join(conds) or '전체'}] 조건에 맞는 가맹점이 없습니다."

    shown = min(limit, total)
    lines = [f"총 {total:,}개 가맹점 (상위 {shown}개 표시)\n"]

    for i, (_, row) in enumerate(result_df.head(limit).iterrows(), 1):
        digital = "✅" if row.get("디지털형 가맹 여부") == "Y" else "❌"
        paper   = "✅" if row.get("지류형 가맹 여부") == "Y" else "❌"
        market  = row.get("소속 시장명(또는 상점가)", "")
        market_str = f" | 시장: {market}" if pd.notna(market) and market else ""
        lines.append(
            f"{i}. **{row['가맹점명']}**\n"
            f"   📍 {row['소재지']} | 🛒 {row['취급품목']}\n"
            f"   💳 디지털:{digital} 지류:{paper}{market_str}"
        )

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# Tool 2: RAG 유사도 검색
# ──────────────────────────────────────────────────────────────────
@tool
def rag_search(query: str) -> str:
    """
    벡터 유사도 기반으로 가맹점을 검색합니다.
    '분위기 좋은 카페', '가족 식당', '전통 있는 시장' 같은 자연어 묘사나
    매장 이름 일부만 아는 경우에 사용하세요.
    정확한 조건(지역·디지털)이 있으면 pandas_filter를 먼저 사용하세요.
    """
    docs = retriever.invoke(query)
    if not docs:
        return "유사한 가맹점 정보를 찾을 수 없습니다."

    lines = [f"유사도 검색 결과 ({len(docs)}개):"]
    for i, doc in enumerate(docs, 1):
        lines.append(f"[{i}] {doc.page_content}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# Tool 3: FAQ 정책·사용법 안내
# ──────────────────────────────────────────────────────────────────
@tool
def faq_answer(question: str) -> str:
    """
    온누리상품권의 정책·사용법·규정에 관한 FAQ 답변을 제공합니다.
    사용처, 유효기간, 구입처, 할인율, 디지털형/지류형 차이,
    구입 한도, 환불 정책, 가맹점 신청 방법 등을 다룹니다.
    """
    keyword_map: dict[str, list[str]] = {
        "사용처":    ["사용처", "쓸 수", "어디서 쓰", "사용 가능", "쓰는 곳"],
        "유효기간":  ["유효기간", "기간", "만료", "소멸"],
        "구입처":    ["구입처", "구매", "살 수", "사는 곳", "어디서 사"],
        "할인":      ["할인", "싸게", "얼마", "가격"],
        "디지털형":  ["디지털", "모바일", "앱", "QR"],
        "지류형":    ["지류", "종이"],
        "한도":      ["한도", "최대", "얼마까지"],
        "환불":      ["환불", "취소", "반환"],
        "가맹점신청": ["가맹점 신청", "신청 방법", "등록"],
    }

    matched = []
    for key, keywords in keyword_map.items():
        if any(kw in question for kw in keywords):
            matched.append(FAQ_DB[key])

    if not matched:
        return (
            "온누리상품권은 전통시장 가맹점에서 사용하는 상품권입니다. "
            "사용처, 유효기간, 디지털/지류 차이, 구입처, 환불 정책 등 "
            "구체적인 질문을 입력하시면 안내드립니다."
        )

    return "\n\n".join(matched)


# ──────────────────────────────────────────────────────────────────
# Agent 초기화
# ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """당신은 온누리상품권 가맹점 안내 전문 AI 어시스턴트입니다.

사용 가능한 도구:
1. pandas_filter  — 지역·품목·디지털/지류 조건으로 정확한 가맹점 필터링 (복합 조건에 강함)
2. rag_search     — 자연어·분위기 설명 기반 유사도 검색
3. faq_answer     — 상품권 정책·사용법·규정 안내

도구 선택 기준:
• 지역, 품목, 디지털/지류 조건이 포함된 질문 → pandas_filter 우선
• "분위기 좋은", "추천해줘" 같은 주관적 표현 → rag_search 추가 활용
• 복합 조건 ("서울 디지털 가능한 음식점") → pandas_filter 단독으로 처리
• 통계 ("몇 개", "얼마나") → pandas_filter로 집계 후 답변
• 정책·사용법 질문 → faq_answer
• 조건 검색 + 정책 혼합 질문 → 두 도구 모두 호출 가능

답변 원칙:
1. 도구 결과를 자연스럽게 요약하여 답변하세요.
2. 가맹점명·위치·취급품목·디지털 가능 여부를 명확히 표시하세요.
3. 결과가 많으면 상위 5~10개 소개 후 전체 개수를 안내하세요.
4. 이전 대화 맥락을 유지하여 자연스럽게 이어가세요."""

tools = [pandas_filter, rag_search, faq_answer]

agent_app = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)

print("✅ Tool-calling Agent 준비 완료!")


# ──────────────────────────────────────────────────────────────────
# 공개 API (backend/routers/chat.py 호환)
# ──────────────────────────────────────────────────────────────────
def process_query(query: str, history: list) -> str:
    """
    사용자 질문 처리 진입점.
    history: [(user_msg, bot_msg), ...]  최근 3턴만 사용
    """
    messages = []
    for user_msg, bot_msg in history[-3:]:
        messages.append(HumanMessage(content=user_msg))
        messages.append(AIMessage(content=bot_msg))
    messages.append(HumanMessage(content=query))

    try:
        result = agent_app.invoke({"messages": messages})
        content = result["messages"][-1].content
        # Gemini가 content를 list[dict] 형태로 반환하는 경우 처리
        if isinstance(content, list):
            return "".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
        return content
    except Exception as e:
        print(f"❌ Agent 오류: {e}")
        return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."


# ──────────────────────────────────────────────────────────────────
# 하위 호환: 다른 모듈에서 참조하는 헬퍼
# ──────────────────────────────────────────────────────────────────
def extract_area_category(query: str) -> tuple[Optional[str], Optional[str]]:
    area = next((a for a in AREAS if a in query), None)
    all_cats = list(CATEGORY_EXPANSIONS.keys()) + ["안경", "커피", "기념품", "뷔페"]
    category = next((c for c in all_cats if c in query), None)
    return area, category
