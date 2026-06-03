"""
온누리상품권 가맹점 MCP Server
기존 Pandas 검색 로직을 MCP 툴로 노출합니다.

실행: python -m mcp_server.server
"""
import asyncio
import json
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from mcp_server.pandas_tools import (
    get_statistics,
    search_by_area,
    search_by_area_and_name,
    search_by_name,
    search_stores,
)

# ──────────────────────────────────────────────
# 서버 인스턴스
# ──────────────────────────────────────────────
server = Server("onnuri-mcp")

# ──────────────────────────────────────────────
# 툴 목록 정의
# ──────────────────────────────────────────────
TOOLS: list[types.Tool] = [
    types.Tool(
        name="search_by_area",
        description="소재지(시/도) 기준으로 온누리상품권 가맹점을 검색합니다. 예: '서울', '경기', '부산'",
        inputSchema={
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "검색할 지역명 (예: 서울, 경기, 부산)",
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)",
                    "default": 10,
                },
            },
            "required": ["area"],
        },
    ),
    types.Tool(
        name="search_by_name",
        description="소속 시장명 또는 상점가명으로 가맹점을 검색합니다. 예: '중앙시장', '남대문'",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "검색할 시장명 또는 상점가명",
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)",
                    "default": 10,
                },
            },
            "required": ["name"],
        },
    ),
    types.Tool(
        name="search_by_area_and_name",
        description="지역과 시장명을 동시에 조건으로 가맹점을 검색합니다.",
        inputSchema={
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "검색할 지역명",
                },
                "name": {
                    "type": "string",
                    "description": "검색할 시장명 또는 상점가명",
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)",
                    "default": 10,
                },
            },
            "required": ["area", "name"],
        },
    ),
    types.Tool(
        name="get_statistics",
        description="지역별 가맹점 통계를 조회합니다. 전체 수, 주요 업종 TOP 5, 지역 분포를 반환합니다.",
        inputSchema={
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "통계를 조회할 지역명",
                },
                "category": {
                    "type": "string",
                    "description": "업종 필터 (선택, 예: 자전거, 카페, 음식점)",
                },
            },
            "required": ["area"],
        },
    ),
    types.Tool(
        name="search_stores",
        description="지역·업종·디지털 여부를 조합한 복합 검색. 유사 업종 키워드를 자동으로 확장합니다.",
        inputSchema={
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "검색할 지역명 (선택)",
                },
                "category": {
                    "type": "string",
                    "description": "업종 (선택, 예: 카페, 자전거, 음식점). 유사 키워드 자동 확장 포함.",
                },
                "digital_only": {
                    "type": "boolean",
                    "description": "디지털 온누리상품권 사용 가능 가맹점만 조회 (기본값: false)",
                    "default": False,
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)",
                    "default": 10,
                },
            },
        },
    ),
]


# ──────────────────────────────────────────────
# 핸들러
# ──────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    handlers = {
        "search_by_area": lambda a: search_by_area(
            area=a["area"], limit=a.get("limit", 10)
        ),
        "search_by_name": lambda a: search_by_name(
            name=a["name"], limit=a.get("limit", 10)
        ),
        "search_by_area_and_name": lambda a: search_by_area_and_name(
            area=a["area"], name=a["name"], limit=a.get("limit", 10)
        ),
        "get_statistics": lambda a: get_statistics(
            area=a["area"], category=a.get("category")
        ),
        "search_stores": lambda a: search_stores(
            area=a.get("area"),
            category=a.get("category"),
            digital_only=a.get("digital_only", False),
            limit=a.get("limit", 10),
        ),
    }

    handler = handlers.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")

    result = handler(arguments)
    return [types.TextContent(type="text", text=result)]


# ──────────────────────────────────────────────
# 진입점
# ──────────────────────────────────────────────
async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="onnuri-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
