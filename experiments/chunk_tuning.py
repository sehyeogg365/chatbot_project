"""
청크 사이즈 및 검색 파라미터 튜닝 실험

실험 조합:
  chunk_size  : 500 / 1000 / 2000
  k           : 5 / 10
  lambda_mult : 0.7 (고정, MMR 검색)

정확도 판별 기준:
  Q1 "서울 음식점"      → 검색된 문서의 소재지에 "서울" 포함
  Q2 "경기 자전거 매장" → 소재지에 "경기" 포함
  Q3 "디지털 가능한 카페" → 디지털형 가맹 여부 == Y
  Q4 "분위기 좋은 한식집" → 취급품목에 한식 관련 키워드 포함
  Q5 "부산 카페"         → 소재지에 "부산" 포함

참고: cleaned_onnuri.csv 의 문서 1건 길이가 평균 ~100자 수준이므로
      chunk_size=500 이상에서는 청킹이 거의 발생하지 않습니다.
      chunk_size 효과보다 k 값 변화가 더 두드러지게 나타날 수 있습니다.

출력: experiments/chunk_experiment.csv
"""

import csv
import gc
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

# ── 실험 설정 ───────────────────────────────────────────────────────────────
CHUNK_SIZES         = [500, 1000, 2000]
K_VALUES            = [5, 10]
LAMBDA_MULT         = 0.7
SAMPLE_SIZE         = 5000   # 원본 문서 샘플 수 (API 비용 절감용)
CHUNK_OVERLAP_RATIO = 0.2    # overlap = chunk_size × 0.2
BATCH_SIZE          = 500    # Chroma 배치 삽입 단위
API_SLEEP           = 0.3    # 배치 간 API 쿨다운 (초)

TEMP_DB_PATH = ROOT / "experiments" / "temp_chroma"
OUTPUT_CSV   = ROOT / "experiments" / "chunk_experiment.csv"

# 한식 관련 키워드 (Q4 정확도 판별)
KOREAN_FOOD_KW = [
    "한식", "한정식", "국밥", "삼겹살", "갈비", "찌개", "불고기",
    "설렁탕", "냉면", "순대", "곱창", "족발", "보쌈", "비빔밥", "된장",
    "두부", "쌈밥", "탕", "국", "죽", "해장국", "감자탕", "뼈해장국",
]

# ── 고정 질문 5개 ─────────────────────────────────────────────────────────
QUERIES = [
    {
        "text":  "서울 음식점",
        "check": lambda doc: "서울" in doc.metadata.get("location", ""),
        "label": "서울 지역 일치",
    },
    {
        "text":  "경기 자전거 매장",
        "check": lambda doc: "경기" in doc.metadata.get("location", ""),
        "label": "경기 지역 일치",
    },
    {
        "text":  "디지털 가능한 카페",
        "check": lambda doc: doc.metadata.get("digital") == "Y",
        "label": "디지털 가맹 Y",
    },
    {
        "text":  "분위기 좋은 한식집",
        "check": lambda doc: any(
            kw in doc.metadata.get("category", "") for kw in KOREAN_FOOD_KW
        ),
        "label": "한식 업종 키워드 일치",
    },
    {
        "text":  "부산 카페",
        "check": lambda doc: "부산" in doc.metadata.get("location", ""),
        "label": "부산 지역 일치",
    },
]


# ── 함수 정의 ─────────────────────────────────────────────────────────────

def load_documents() -> list[Document]:
    df = pd.read_csv(ROOT / "cleaned_onnuri.csv")

    df["full_text"] = df.apply(
        lambda r: (
            f"상호명: {r['가맹점명']} | "
            f"시장명: {r['소속 시장명(또는 상점가)']} | "
            f"위치: {r['소재지']} | "
            f"주요품목: {r['취급품목']} | "
            f"디지털상품권: {'가능' if r['디지털형 가맹 여부'] == 'Y' else '불가'} | "
            f"지류상품권: {'가능' if r['지류형 가맹 여부'] == 'Y' else '불가'}"
        ),
        axis=1,
    )

    docs = [
        Document(
            page_content=row["full_text"],
            metadata={
                "id":       idx,
                "name":     row["가맹점명"],
                "location": str(row["소재지"]),
                "category": str(row["취급품목"]),
                "digital":  str(row["디지털형 가맹 여부"]),
            },
        )
        for idx, row in df.head(SAMPLE_SIZE).iterrows()
    ]
    return docs


def _release_vectorstore(vs: Chroma) -> None:
    """참조를 끊고 GC + sleep으로 Windows 파일 락 해제.
    chromadb 1.x Rust 백엔드에서는 _system.stop() 호출 시 내부 상태가
    오염되므로 호출하지 않고 GC만 사용한다."""
    del vs
    gc.collect()
    time.sleep(3)


def _rmtree_safe(path: Path, retries: int = 6, delay: float = 2.0) -> None:
    """Windows 파일 락이 남아 있을 경우 재시도하며 디렉토리 삭제."""
    for attempt in range(retries):
        try:
            if path.exists():
                shutil.rmtree(path)
            return
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def _db_path_for(chunk_size: int) -> Path:
    """chunk_size별 독립 경로 반환 (tenant 상태 오염 방지)."""
    return TEMP_DB_PATH / f"cs_{chunk_size}"


def build_vectorstore(
    docs: list[Document], chunk_size: int, embeddings: GoogleGenerativeAIEmbeddings
) -> Chroma:
    db_path = _db_path_for(chunk_size)
    _rmtree_safe(db_path)
    db_path.mkdir(parents=True, exist_ok=True)

    overlap = int(chunk_size * CHUNK_OVERLAP_RATIO)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    splits = splitter.split_documents(docs)
    print(f"  청킹 결과: {len(docs)}개 문서 → {len(splits)}개 청크  (overlap={overlap})")

    vectorstore = Chroma.from_documents(
        documents=splits[:BATCH_SIZE],
        embedding=embeddings,
        persist_directory=str(db_path),
    )

    for i in tqdm(
        range(BATCH_SIZE, len(splits), BATCH_SIZE),
        desc="  배치 추가",
        leave=False,
    ):
        vectorstore.add_documents(splits[i : i + BATCH_SIZE])
        time.sleep(API_SLEEP)

    return vectorstore


FIELDNAMES = [
    "chunk_size", "k", "lambda_mult", "query",
    "accuracy_label", "matched", "retrieved", "accuracy",
]


def evaluate(vectorstore: Chroma, k: int) -> list[dict]:
    results = []
    for q in QUERIES:
        retrieved = vectorstore.max_marginal_relevance_search(
            q["text"], k=k, lambda_mult=LAMBDA_MULT
        )
        matched  = sum(1 for doc in retrieved if q["check"](doc))
        accuracy = matched / len(retrieved) if retrieved else 0.0
        results.append(
            {
                "query":    q["text"],
                "label":    q["label"],
                "matched":  matched,
                "total":    len(retrieved),
                "accuracy": round(accuracy, 4),
            }
        )
    return results


def _load_done_combos() -> tuple[list[dict], set[tuple[int, int]]]:
    """CSV에서 이미 완료된 (chunk_size, k) 조합을 읽어 반환."""
    if not OUTPUT_CSV.exists():
        return [], set()

    existing: list[dict] = []
    counts: dict[tuple[int, int], int] = {}
    with open(OUTPUT_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            existing.append(row)
            key = (int(row["chunk_size"]), int(row["k"]))
            counts[key] = counts.get(key, 0) + 1

    done = {key for key, cnt in counts.items() if cnt >= len(QUERIES)}
    return existing, done


def _print_summary(rows: list[dict]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    df["accuracy"]   = df["accuracy"].astype(float)
    df["chunk_size"] = df["chunk_size"].astype(int)
    df["k"]          = df["k"].astype(int)

    print("\n=== 조합별 평균 정확도 ===")
    print(
        df.groupby(["chunk_size", "k"])["accuracy"]
        .mean()
        .round(4)
        .rename("avg_accuracy")
        .to_string()
    )

    print("\n=== 질문별 최고 조합 ===")
    for q_text in df["query"].unique():
        best = df[df["query"] == q_text].sort_values("accuracy", ascending=False).iloc[0]
        print(
            f"  '{q_text}' "
            f"→ chunk_size={int(best['chunk_size'])}, k={int(best['k'])} "
            f"→ {float(best['accuracy']):.1%}"
        )
    print("\n실험 완료!")


# ── 메인 ──────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    existing_rows, done_combos = _load_done_combos()
    if done_combos:
        print(f"이전 결과 발견 → {done_combos} 조합 건너뜁니다.")

    combos    = [(cs, k) for cs in CHUNK_SIZES for k in K_VALUES]
    remaining = [(cs, k) for cs, k in combos if (cs, k) not in done_combos]

    if not remaining:
        print("모든 조합이 이미 완료되었습니다.")
        _print_summary(existing_rows)
        return

    print("=" * 60)
    print("청크 사이즈 & 검색 파라미터 튜닝 실험")
    print(f"  남은 조합   : {remaining}")
    print(f"  lambda_mult : {LAMBDA_MULT}  |  sample_size : {SAMPLE_SIZE}")
    print("=" * 60)

    print("\n문서 로딩 중...")
    docs = load_documents()
    print(f"원본 문서: {len(docs)}개")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 결과를 조합 완료 즉시 CSV에 flush (중단 시 복구 가능)
    write_header = not OUTPUT_CSV.exists()
    csv_file = open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig")
    writer   = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()

    new_rows: list[dict] = []
    prev_chunk_size: int | None = None
    vectorstore: Chroma | None = None

    try:
        for run_idx, (chunk_size, k) in enumerate(remaining, 1):
            if chunk_size != prev_chunk_size:
                # 이전 vectorstore 참조 해제 (독립 경로 방식이므로 rmtree 불필요)
                if vectorstore is not None:
                    _release_vectorstore(vectorstore)
                    vectorstore = None

                print(f"\n{'=' * 60}")
                print(f"[ChromaDB 생성] chunk_size={chunk_size}")
                vectorstore = build_vectorstore(docs, chunk_size, embeddings)
                prev_chunk_size = chunk_size

            print(f"\n[{run_idx}/{len(remaining)}] chunk_size={chunk_size}, k={k}, lambda_mult={LAMBDA_MULT}")
            query_results = evaluate(vectorstore, k)  # type: ignore[arg-type]

            for qr in query_results:
                row = {
                    "chunk_size":     chunk_size,
                    "k":              k,
                    "lambda_mult":    LAMBDA_MULT,
                    "query":          qr["query"],
                    "accuracy_label": qr["label"],
                    "matched":        qr["matched"],
                    "retrieved":      qr["total"],
                    "accuracy":       qr["accuracy"],
                }
                new_rows.append(row)
                writer.writerow(row)
                print(f"  '{qr['query']:16s}' → {qr['matched']}/{qr['total']} ({qr['accuracy']:.1%})  [{qr['label']}]")
            csv_file.flush()

    finally:
        csv_file.close()
        if vectorstore is not None:
            _release_vectorstore(vectorstore)
        # 모든 temp DB 정리
        _rmtree_safe(TEMP_DB_PATH)

    print(f"\n결과 저장 완료: {OUTPUT_CSV}")
    _print_summary(existing_rows + new_rows)


if __name__ == "__main__":
    main()
