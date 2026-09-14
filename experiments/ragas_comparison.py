"""
RAGAS 비교 평가 스크립트 — Query Rewrite + Reranker 적용 전/후

평가 대상:
  Mode A (before) : Query Rewrite / Reranker 없는 기존 rag_search
                    vectorstore.as_retriever(search_type="mmr", k=5, lambda_mult=0.7)
                    → 상위 5개 문서를 그대로 context 로 사용
                    (커밋 b659338 시점의 src/chatbot.py rag_search 구현을 그대로 재현)
  Mode B (after)  : 현재 src/chatbot.py 의 rag_search
                    rewrite_query() → similarity_search(k=10) → CrossEncoder 리랭킹 → 상위 3개

지표 : faithfulness, answer_relevancy, context_precision, context_recall
LLM  : src.llm_config.get_llm() (모델명 하드코딩 안 함) — src.chatbot 의 llm 인스턴스 공유
임베딩: GoogleGenerativeAIEmbeddings (src.llm_config.get_embeddings)
출력 : experiments/ragas_comparison.csv (샘플 채점 직후 바로 append —
       중간에 실패해도 그 전까지 채점된 행은 파일에 남는다)

평가 흐름 (질문 1개 → Mode A → Mode B 순으로 순차 실행, Gemini 무료 티어 한도 방지):
  1. 각 모드의 검색 경로를 그대로 실행해 context 를 얻는다.
  2. 검색 결과만 근거로 LLM 이 최종 답변을 생성한다. (두 모드 모두 동일한 ANSWER_PROMPT —
     달라지는 것은 검색 품질뿐이므로 검색 파이프라인 효과만 분리 측정된다)
  3. (질문, 답변, context, reference) 를 RAGAS 로 채점한다. (샘플 1개 = 1회 evaluate)
  모든 API 호출 사이에 SLEEP_SECONDS 만큼 대기한다.

주의: REFERENCES 는 특정 retriever 가 반환한 상호명 목록이 아니라, 질문이 요구하는
     조건(지역·업종·상품권 형태)을 서술한 mode-neutral 골든셋입니다.
     기존 ragas_eval.py 의 REFERENCES 는 Mode A(mmr k=5)의 실제 검색 결과에서 뽑은
     상호명이라, 그대로 쓰면 context_recall 이 Mode A 에 유리하게 편향됩니다.
"""

import os
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # src/chatbot.py 가 상대경로(cleaned_onnuri.csv 등)를 쓰므로 필요

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ["LANGCHAIN_TRACING_V2"] = "false"  # LangSmith 키 미설정 시 403 노이즈 방지

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    faithfulness,
    AnswerRelevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig

from src.llm_config import get_embeddings

# llm / vectorstore / reranker / rewrite_query 를 src.chatbot 에서 그대로 가져와
# Mode B 가 실제 운영 경로와 동일하도록 맞춘다.
from src.chatbot import llm, vectorstore, reranker, rewrite_query

OUTPUT_CSV = ROOT / "experiments" / "ragas_comparison.csv"

SLEEP_SECONDS = 5  # API 호출 사이 대기 시간 (무료 티어 레이트리밋 방지)

METRIC_COLS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

# strictness=1: 기본값(3)은 답변에서 역질문을 여러 개 한 번의 호출로 동시 생성(multiple
# candidates)하는데, gemini-3.1-flash-lite 는 이를 지원하지 않아 "Multiple candidates is
# not enabled for this model" 오류가 남. strictness=1 로 낮춰 호출당 후보 1개만 생성.
answer_relevancy = AnswerRelevancy(strictness=1)

# 기존 ragas_eval.py 와 동일한 질문 3개
QUESTIONS = [
    "분위기 좋은 한식집 추천해줘",
    "서울에서 디지털 상품권 되는 카페 알려줘",
    "조용히 혼밥하기 좋은 곳",
]

# 골든셋 reference: 두 모드 중 어느 쪽 검색 결과에도 의존하지 않도록, 상호명 대신
# 질문이 요구하는 조건(지역·업종·상품권 형태)을 서술한다.
REFERENCES = {
    "분위기 좋은 한식집 추천해줘":
        "한식(백반·고기·국밥 등) 업종으로 등록된 온누리상품권 가맹점을 추천한다. "
        "각 가맹점의 상호명, 소재지, 취급품목을 함께 안내한다.",
    "서울에서 디지털 상품권 되는 카페 알려줘":
        "소재지가 서울이고 디지털형 온누리상품권 가맹 여부가 'Y'인 "
        "카페·커피·디저트 업종 가맹점을 추천한다. "
        "각 가맹점의 상호명, 서울 내 소재지, 취급품목을 함께 안내한다.",
    "조용히 혼밥하기 좋은 곳":
        "혼자 식사하기 적합한 한식·분식·일식 등 소규모 음식점 업종의 "
        "온누리상품권 가맹점을 추천한다. "
        "각 가맹점의 상호명, 소재지, 취급품목을 함께 안내한다.",
}

ANSWER_PROMPT = """다음은 사용자 질문과 온누리상품권 가맹점 벡터 검색 결과입니다.
검색 결과에 있는 내용만 근거로 자연스러운 한국어 답변을 2~3문장으로 작성하세요.
검색 결과에 없는 내용은 지어내지 마세요.

질문: {question}

검색 결과:
{context}

답변:"""


def extract_text(content) -> str:
    """Gemini가 content를 list[dict] 형태로 반환하는 경우 처리 (src/chatbot.py와 동일 패턴)"""
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return content


def format_docs(docs) -> str:
    """rag_search Tool 의 반환 포맷을 동일하게 재현"""
    lines = [f"유사도 검색 결과 ({len(docs)}개):"]
    for i, doc in enumerate(docs, 1):
        lines.append(f"[{i}] {doc.page_content}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# Mode A: Query Rewrite / Reranker 없는 기존 검색 (b659338 시점 구현)
# ──────────────────────────────────────────────────────────────────
baseline_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "lambda_mult": 0.7},
)


def retrieve_mode_a(question: str) -> list:
    docs = baseline_retriever.invoke(question)
    print(f"    검색: mmr k=5 → {len(docs)}개 문서")
    return docs


# ──────────────────────────────────────────────────────────────────
# Mode B: Query Rewrite + Reranker 적용 (현재 src/chatbot.py rag_search)
# ──────────────────────────────────────────────────────────────────
def retrieve_mode_b(question: str) -> list:
    rewritten = rewrite_query(question)
    if rewritten == question:
        # rewrite_query 는 실패 시 조용히 원본 쿼리를 반환하므로 명시적으로 경고
        print("    ⚠️ Query Rewrite 결과가 원본과 동일 (재작성 실패 가능성)")
    print(f"    Query Rewrite: '{question}' → '{rewritten}'")
    time.sleep(SLEEP_SECONDS)

    docs = vectorstore.similarity_search(rewritten, k=10)
    if not docs:
        return []

    pairs = [(rewritten, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    reranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)[:3]
    print(f"    검색: similarity k=10 → 리랭킹 상위 {len(reranked)}개")
    return [doc for doc, _ in reranked]


MODES = {
    "A_before": retrieve_mode_a,  # Query Rewrite + Reranker 없음
    "B_after": retrieve_mode_b,   # Query Rewrite + Reranker 적용
}


def build_sample(question: str, retrieve_fn) -> SingleTurnSample:
    docs = retrieve_fn(question)
    contexts = [doc.page_content for doc in docs]
    time.sleep(SLEEP_SECONDS)

    tool_output = format_docs(docs) if docs else "유사한 가맹점 정보를 찾을 수 없습니다."
    answer = extract_text(
        llm.invoke(ANSWER_PROMPT.format(question=question, context=tool_output)).content
    )
    time.sleep(SLEEP_SECONDS)

    return SingleTurnSample(
        user_input=question,
        retrieved_contexts=contexts,
        response=answer,
        reference=REFERENCES[question],
    )


def evaluate_sample(sample: SingleTurnSample, embeddings) -> pd.DataFrame:
    dataset = EvaluationDataset(samples=[sample])
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(llm),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
        # 샘플 1개씩 순차 채점 (동시 요청 없음)
        run_config=RunConfig(max_workers=1, timeout=180),
    )
    return result.to_pandas()


COLUMN_RENAME = {
    "user_input": "question",
    "retrieved_contexts": "contexts",
    "response": "answer",
    "reference": "ground_truth",
}


def print_comparison(df: pd.DataFrame) -> None:
    """전/후 비교 표를 콘솔에 출력"""
    available = [c for c in METRIC_COLS if c in df.columns]
    means = df.groupby("mode")[available].mean()

    before = means.loc["A_before"] if "A_before" in means.index else None
    after = means.loc["B_after"] if "B_after" in means.index else None

    print("\n" + "=" * 76)
    print("  Query Rewrite + Reranker 적용 전/후 RAGAS 비교")
    print("=" * 76)
    print(f"{'지표':<20}{'Mode A (before)':>18}{'Mode B (after)':>18}{'Δ (B-A)':>16}")
    print("-" * 76)
    for metric in available:
        b = before[metric] if before is not None else float("nan")
        a = after[metric] if after is not None else float("nan")
        delta = a - b
        sign = "▲" if delta > 0 else ("▼" if delta < 0 else "－")
        print(f"{metric:<20}{b:>18.4f}{a:>18.4f}{sign + format(delta, '+.4f'):>16}")
    print("-" * 76)
    if before is not None and after is not None:
        b_avg, a_avg = before[available].mean(), after[available].mean()
        sign = "▲" if a_avg > b_avg else ("▼" if a_avg < b_avg else "－")
        print(f"{'평균':<20}{b_avg:>18.4f}{a_avg:>18.4f}"
              f"{sign + format(a_avg - b_avg, '+.4f'):>16}")
    print("=" * 76)

    print("\n[질문별 상세]")
    per_q = df.pivot_table(index="question", columns="mode", values=available)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(per_q.round(4))


def main():
    embeddings = get_embeddings()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    result_dfs = []
    total = len(QUESTIONS) * len(MODES)
    step = 0

    for q_idx, question in enumerate(QUESTIONS, 1):
        print(f"\n{'=' * 70}\n[Q{q_idx}/{len(QUESTIONS)}] {question}\n{'=' * 70}")

        for mode, retrieve_fn in MODES.items():
            step += 1
            print(f"\n  ▶ [{step}/{total}] Mode {mode}")

            print("    1️⃣ 검색 및 답변 생성 중...")
            sample = build_sample(question, retrieve_fn)

            print("    2️⃣ RAGAS 채점 중 "
                  "(faithfulness, answer_relevancy, context_precision, context_recall)...")
            row_df = evaluate_sample(sample, embeddings).rename(columns=COLUMN_RENAME)
            row_df.insert(0, "mode", mode)
            row_df.insert(0, "q_idx", q_idx)
            result_dfs.append(row_df)

            # 샘플 채점 직후 바로 저장 — 다음 샘플에서 실패해도 이 행은 남는다.
            row_df.to_csv(
                OUTPUT_CSV,
                mode="w" if step == 1 else "a",
                header=(step == 1),
                index=False,
                encoding="utf-8-sig",
            )
            print(f"    💾 저장 완료 ({OUTPUT_CSV})")

            if step < total:
                time.sleep(SLEEP_SECONDS)

    df = pd.concat(result_dfs, ignore_index=True)
    print_comparison(df)
    print(f"\n✅ 전체 {len(df)}개 샘플({len(QUESTIONS)}질문 × {len(MODES)}모드) "
          f"결과 저장 완료: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
