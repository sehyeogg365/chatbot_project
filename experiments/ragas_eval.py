"""
RAGAS 평가 스크립트

평가 대상: rag_search Tool (RAG 경로, src/chatbot.py)
지표     : faithfulness, answer_relevancy, context_precision, context_recall
LLM      : gemini-2.5-flash        (src.llm_config.get_llm)
임베딩   : GoogleGenerativeAIEmbeddings (src.llm_config.get_embeddings)
출력     : experiments/ragas_result.csv

평가 흐름 (질문 1개씩 순차 실행, Gemini 무료 티어 일일 한도 초과 방지):
  1. rag_search Tool 을 그대로 호출해 검색 결과(context)를 얻는다.
  2. 검색 결과만 근거로 LLM이 최종 답변을 생성한다. (SYSTEM_PROMPT의
     "도구 결과를 자연스럽게 요약" 단계를 재현 — agent 전체를 거치면
     pandas_filter 등 다른 Tool로 분기될 수 있어 rag_search 경로만 분리 평가)
  3. (질문, 답변, context, reference) 를 RAGAS로 채점한다. (질문 1개 = 1회 evaluate)

  각 API 호출(검색 / 답변 생성 / 채점) 사이에 SLEEP_SECONDS 만큼 대기하고,
  질문도 한 번에 하나씩만 처리하여 순간 요청량을 최소화한다.

주의: context_recall 계산에 쓰이는 REFERENCES 는 프로젝트에 정답 골든셋이
     없어 검토자가 임시로 작성한 참고 답변입니다. 실제 데이터 품질에 맞춰
     검토 후 수정하세요.
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
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig

from src.llm_config import get_llm, get_embeddings
from src.chatbot import rag_search, retriever

OUTPUT_CSV = ROOT / "experiments" / "ragas_result.csv"

SLEEP_SECONDS = 5  # API 호출 사이 대기 시간 (무료 티어 레이트리밋 방지)

# 질문 3개로 축소 (1차 실행에서 answer_relevancy가 채점됐던 질문 위주로 선정)
QUESTIONS = [
    "분위기 좋은 한식집 추천해줘",
    "서울에서 디지털 상품권 되는 카페 알려줘",
    "조용히 혼밥하기 좋은 곳",
]

# 참고용 reference (골든셋 부재로 임시 작성 — 검토 후 수정 권장)
REFERENCES = {
    "분위기 좋은 한식집 추천해줘":
        "한식·한정식 등 한식 관련 업종을 취급하며 분위기가 좋다고 볼 수 있는 "
        "온누리 가맹점을 위치와 함께 추천한다.",
    "서울에서 디지털 상품권 되는 카페 알려줘":
        "서울 소재이면서 취급품목이 카페(커피·디저트·베이커리 포함)이고, "
        "디지털형 가맹 여부가 Y인 가맹점을 추천한다.",
    "조용히 혼밥하기 좋은 곳":
        "1인 방문 및 혼밥에 적합한 조용한 분위기의 음식점을 추천한다.",
}

ANSWER_PROMPT = """다음은 사용자 질문과 온누리상품권 가맹점 벡터 검색 결과입니다.
검색 결과에 있는 내용만 근거로 자연스러운 한국어 답변을 2~3문장으로 작성하세요.
검색 결과에 없는 내용은 지어내지 마세요.

질문: {question}

검색 결과:
{context}

답변:"""


def build_sample(llm, question: str) -> SingleTurnSample:
    docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in docs]
    time.sleep(SLEEP_SECONDS)

    tool_output = rag_search.invoke({"query": question})
    time.sleep(SLEEP_SECONDS)

    answer = llm.invoke(
        ANSWER_PROMPT.format(question=question, context=tool_output)
    ).content
    time.sleep(SLEEP_SECONDS)

    return SingleTurnSample(
        user_input=question,
        retrieved_contexts=contexts,
        response=answer,
        reference=REFERENCES[question],
    )


def evaluate_sample(sample: SingleTurnSample, llm, embeddings) -> pd.DataFrame:
    dataset = EvaluationDataset(samples=[sample])
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(llm),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
        # 질문 1개씩 순차 채점 (동시 요청 없음)
        run_config=RunConfig(max_workers=1, timeout=180),
    )
    return result.to_pandas()


def main():
    llm = get_llm(temperature=0.0)
    embeddings = get_embeddings()

    result_dfs = []
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/{len(QUESTIONS)}] {question}")

        print("  1️⃣ rag_search Tool 호출 및 답변 생성 중...")
        sample = build_sample(llm, question)

        print("  2️⃣ RAGAS 채점 중 (faithfulness, answer_relevancy, context_precision, context_recall)...")
        result_dfs.append(evaluate_sample(sample, llm, embeddings))

        if i < len(QUESTIONS):
            time.sleep(SLEEP_SECONDS)

    df = pd.concat(result_dfs, ignore_index=True).rename(
        columns={
            "user_input": "question",
            "retrieved_contexts": "contexts",
            "response": "answer",
            "reference": "ground_truth",
        }
    )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    print("\n=== 평균 점수 ===")
    print(df[metric_cols].mean())
    print(f"\n✅ 결과 저장 완료: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
