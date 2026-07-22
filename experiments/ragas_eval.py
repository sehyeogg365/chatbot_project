"""
RAGAS 평가 스크립트

평가 대상: rag_search Tool (RAG 경로, src/chatbot.py)
지표     : faithfulness, answer_relevancy, context_precision, context_recall
LLM      : src.llm_config.get_llm() 이 반환하는 모델을 그대로 사용 (모델명 하드코딩 안 함)
임베딩   : GoogleGenerativeAIEmbeddings (src.llm_config.get_embeddings)
출력     : experiments/ragas_result.csv (질문 처리 직후 바로 append — 중간에 실패해도
          그 전까지 채점된 질문은 파일에 남는다)

평가 흐름 (질문 1개씩 순차 실행, Gemini 무료 티어 일일 한도 초과 방지):
  1. rag_search Tool 을 그대로 호출해 검색 결과(context)를 얻는다.
  2. 검색 결과만 근거로 LLM이 최종 답변을 생성한다. (SYSTEM_PROMPT의
     "도구 결과를 자연스럽게 요약" 단계를 재현 — agent 전체를 거치면
     pandas_filter 등 다른 Tool로 분기될 수 있어 rag_search 경로만 분리 평가)
  3. (질문, 답변, context, reference) 를 RAGAS로 채점한다. (질문 1개 = 1회 evaluate)

  각 API 호출(검색 / 답변 생성 / 채점) 사이에 SLEEP_SECONDS 만큼 대기하고,
  질문도 한 번에 하나씩만 처리하여 순간 요청량을 최소화한다.

주의: REFERENCES 는 retriever(k=5, mmr)가 실제로 반환하는 상위 문서의 상호명·지역·
     품목을 반영해 작성한 골든셋입니다. vectordb/retriever 설정이 바뀌면 실제
     검색 결과와 어긋날 수 있으니 재확인하세요.
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

from src.llm_config import get_llm, get_embeddings
from src.chatbot import rag_search, retriever

OUTPUT_CSV = ROOT / "experiments" / "ragas_result.csv"

SLEEP_SECONDS = 5  # API 호출 사이 대기 시간 (무료 티어 레이트리밋 방지)

# strictness=1: 기본값(3)은 답변에서 역질문을 여러 개 한 번의 호출로 동시 생성(multiple
# candidates)하는데, gemini-3.1-flash-lite는 이를 지원하지 않아 "Multiple candidates is
# not enabled for this model" 오류가 남. strictness=1로 낮춰 호출당 후보 1개만 생성.
answer_relevancy = AnswerRelevancy(strictness=1)

# 질문 3개로 축소 (1차 실행에서 answer_relevancy가 채점됐던 질문 위주로 선정)
QUESTIONS = [
    "분위기 좋은 한식집 추천해줘",
    "서울에서 디지털 상품권 되는 카페 알려줘",
    "조용히 혼밥하기 좋은 곳",
]

# 골든셋 reference: retriever(k=5, mmr)가 실제로 반환하는 상위 문서의 상호명·지역·품목을
# 그대로 반영해 작성 (1차 실행 결과의 retrieved_contexts 기준). retriever나 벡터DB가
# 바뀌면 이 목록도 다시 확인해야 함.
REFERENCES = {
    "분위기 좋은 한식집 추천해줘":
        "돈꿔줘(전북, 한식), 더코네(서울, 한식), 뜨란(광주, 한식), "
        "로비(서울, 한식), 한숲생고기(경기, 한식) 등 한식 가맹점을 추천한다.",
    "서울에서 디지털 상품권 되는 카페 알려줘":
        "케어(서울, 커피 및 디저트), 카페로뎀(서울, 카페), 케이크팝(서울, 카페), "
        "페이지(서울, 커피), 스터디카페 공유(서울, 스터디카페) 등 서울 소재 "
        "디지털 상품권 가능 가맹점을 추천한다.",
    "조용히 혼밥하기 좋은 곳":
        "쉼, 어묵 그리고 한잔술(세종, 한식), 여기가 좋겠네(서울, 한식), "
        "핵밥 숭실대점(서울, 한식), 전주24시참편한 39콩나물국밥(광주, 한식), "
        "덥(광주, 일식) 등을 추천한다.",
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


def build_sample(llm, question: str) -> SingleTurnSample:
    docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in docs]
    time.sleep(SLEEP_SECONDS)

    tool_output = rag_search.invoke({"query": question})
    time.sleep(SLEEP_SECONDS)

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


COLUMN_RENAME = {
    "user_input": "question",
    "retrieved_contexts": "contexts",
    "response": "answer",
    "reference": "ground_truth",
}


def main():
    llm = get_llm(temperature=0.0)
    embeddings = get_embeddings()

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    result_dfs = []
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/{len(QUESTIONS)}] {question}")

        print("  1️⃣ rag_search Tool 호출 및 답변 생성 중...")
        sample = build_sample(llm, question)

        print("  2️⃣ RAGAS 채점 중 (faithfulness, answer_relevancy, context_precision, context_recall)...")
        row_df = evaluate_sample(sample, llm, embeddings).rename(columns=COLUMN_RENAME)
        result_dfs.append(row_df)

        # 질문 처리 직후 바로 저장 — 다음 질문에서 실패해도 이 행은 남는다.
        row_df.to_csv(
            OUTPUT_CSV,
            mode="w" if i == 1 else "a",
            header=(i == 1),
            index=False,
            encoding="utf-8-sig",
        )
        print(f"  💾 저장 완료 ({OUTPUT_CSV})")

        if i < len(QUESTIONS):
            time.sleep(SLEEP_SECONDS)

    df = pd.concat(result_dfs, ignore_index=True)
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    print("\n=== 평균 점수 ===")
    print(df[metric_cols].mean())
    print(f"\n✅ 전체 {len(df)}개 질문 결과 저장 완료: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
