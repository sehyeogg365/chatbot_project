"""
기존 Pandas 검색 로직을 MCP 툴용 함수로 래핑.
CSV는 모듈 임포트 시 1회 로드, 이후 메모리에서 서빙.
"""
import json
from pathlib import Path
from typing import Optional
import pandas as pd

# ──────────────────────────────────────────────
# 데이터 로드 (서버 기동 시 1회)
# ──────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_df = pd.read_csv(_ROOT / "cleaned_onnuri.csv")
_df_area = pd.read_csv(_ROOT / "area_onnuri.csv")

AREAS = [
    "강원", "경기", "경남", "경북", "광주", "대구", "대전",
    "부산", "서울", "세종", "울산", "인천", "전남", "전북",
    "제주", "충남", "충북",
]
CATEGORIES = [
    "자전거", "카페", "안경", "음식점", "미용", "의류",
    "커피", "한식", "기념품", "고기", "뷔페",
]


# ──────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────
def _df_to_records(df: pd.DataFrame, limit: int) -> list[dict]:
    cols = ["가맹점명", "소재지", "취급품목", "디지털형 가맹 여부", "소속 시장명(또는 상점가)"]
    available = [c for c in cols if c in df.columns]
    return df[available].head(limit).fillna("").to_dict(orient="records")


def _ok(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# 툴 구현 함수
# ──────────────────────────────────────────────

def search_by_area(area: str, limit: int = 10) -> str:
    """소재지 기준으로 가맹점을 검색합니다."""
    result = _df[_df["소재지"].str.contains(area, na=False)]
    if result.empty:
        return _ok({"total": 0, "area": area, "stores": []})
    return _ok({
        "total": len(result),
        "area": area,
        "stores": _df_to_records(result, limit),
    })


def search_by_name(name: str, limit: int = 10) -> str:
    """소속 시장명 또는 상점가명으로 가맹점을 검색합니다."""
    result = _df[_df["소속 시장명(또는 상점가)"].str.contains(name, na=False)]
    if result.empty:
        return _ok({"total": 0, "name": name, "stores": []})
    return _ok({
        "total": len(result),
        "name": name,
        "stores": _df_to_records(result, limit),
    })


def search_by_area_and_name(area: str, name: str, limit: int = 10) -> str:
    """지역과 시장명을 동시에 조건으로 가맹점을 검색합니다."""
    result = _df[
        _df["소재지"].str.contains(area, na=False)
        & _df["소속 시장명(또는 상점가)"].str.contains(name, na=False)
    ]
    if result.empty:
        return _ok({"total": 0, "area": area, "name": name, "stores": []})
    return _ok({
        "total": len(result),
        "area": area,
        "name": name,
        "stores": _df_to_records(result, limit),
    })


def get_statistics(area: str, category: Optional[str] = None) -> str:
    """지역(+선택적 업종) 기준 통계를 반환합니다."""
    filtered = _df[_df["소재지"].str.contains(area, na=False)]
    if category:
        filtered = filtered[filtered["취급품목"].str.contains(category, na=False)]

    if filtered.empty:
        return _ok({"area": area, "category": category, "total": 0, "message": "해당 조건에 맞는 가맹점이 없습니다."})

    top_items = filtered["취급품목"].value_counts().head(5).to_dict()
    top_regions = (
        filtered["소재지"].str.split().str[0].value_counts().head(5).to_dict()
    )

    return _ok({
        "area": area,
        "category": category,
        "total": len(filtered),
        "top_items": top_items,
        "top_regions": top_regions,
    })


def search_stores(
    area: Optional[str] = None,
    category: Optional[str] = None,
    digital_only: bool = False,
    limit: int = 10,
) -> str:
    """지역·업종·디지털 여부를 조합한 복합 검색입니다."""
    result = _df.copy()

    if area:
        result = result[result["소재지"].str.contains(area, na=False)]

    if category:
        # 유사 키워드 확장
        expansions: dict[str, list[str]] = {
            "카페": ["카페", "커피", "디저트", "베이커리"],
            "음식점": ["음식점", "식당", "한식", "중식", "일식"],
            "자전거": ["자전거", "바이크"],
        }
        keywords = expansions.get(category, [category])
        mask = pd.Series(False, index=result.index)
        for kw in keywords:
            mask |= result["취급품목"].str.contains(kw, na=False, case=False)
        result = result[mask]

    if digital_only:
        result = result[result["디지털형 가맹 여부"] == "Y"]

    if result.empty:
        return _ok({"total": 0, "area": area, "category": category, "digital_only": digital_only, "stores": []})

    return _ok({
        "total": len(result),
        "area": area,
        "category": category,
        "digital_only": digital_only,
        "stores": _df_to_records(result, limit),
    })
