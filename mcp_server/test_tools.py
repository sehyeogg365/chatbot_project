"""pandas_tools 단독 실행 테스트 (MCP 없이 직접 호출)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_server.pandas_tools import (
    get_statistics,
    search_by_area,
    search_by_area_and_name,
    search_by_name,
    search_stores,
)


def _pretty(label: str, raw: str) -> None:
    data = json.loads(raw)
    total = data.get("total", "?")
    print(f"\n{'='*50}")
    print(f"[{label}]  총 {total}건")
    for i, s in enumerate(data.get("stores", [])[:3], 1):
        print(f"  {i}. {s.get('가맹점명')} | {s.get('소재지')} | {s.get('취급품목')}")
    if "top_items" in data:
        print("  TOP 품목:", list(data["top_items"].keys())[:3])


if __name__ == "__main__":
    _pretty("search_by_area(서울)", search_by_area("서울", limit=5))
    _pretty("search_by_name(중앙시장)", search_by_name("중앙시장", limit=5))
    _pretty("search_by_area_and_name(서울, 시장)", search_by_area_and_name("서울", "시장", limit=5))
    _pretty("search_stores(경기, 카페)", search_stores(area="경기", category="카페", limit=5))
    _pretty("search_stores(디지털전용, 자전거)", search_stores(category="자전거", digital_only=True, limit=5))

    stats = json.loads(get_statistics("서울"))
    print(f"\n{'='*50}")
    print(f"[get_statistics(서울)]  총 {stats['total']}건")
    print("  TOP 품목:", list(stats.get("top_items", {}).keys())[:5])
    print("  TOP 지역:", list(stats.get("top_regions", {}).keys())[:3])
