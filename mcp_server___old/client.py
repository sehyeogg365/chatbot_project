"""
FastAPI → MCP Server 연동 클라이언트.
백엔드 라우터에서 import해서 사용합니다.
"""
import json
from typing import Optional

from mcp_server.pandas_tools import (
    get_statistics,
    search_by_area,
    search_by_area_and_name,
    search_by_name,
    search_stores,
)


class OnnuriMCPClient:
    """MCP 툴을 직접 호출하는 동기 클라이언트 (같은 프로세스 내 호출)."""

    def search_by_area(self, area: str, limit: int = 10) -> dict:
        return json.loads(search_by_area(area, limit))

    def search_by_name(self, name: str, limit: int = 10) -> dict:
        return json.loads(search_by_name(name, limit))

    def search_by_area_and_name(self, area: str, name: str, limit: int = 10) -> dict:
        return json.loads(search_by_area_and_name(area, name, limit))

    def get_statistics(self, area: str, category: Optional[str] = None) -> dict:
        return json.loads(get_statistics(area, category))

    def search_stores(
        self,
        area: Optional[str] = None,
        category: Optional[str] = None,
        digital_only: bool = False,
        limit: int = 10,
    ) -> dict:
        return json.loads(search_stores(area, category, digital_only, limit))


# 싱글턴 — 백엔드 전체에서 공유
mcp_client = OnnuriMCPClient()
