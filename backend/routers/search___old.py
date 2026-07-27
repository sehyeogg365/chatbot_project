"""
MCP 기반 가맹점 검색 라우터.
/api/search/* 엔드포인트를 제공합니다.
"""
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from mcp_server.client import mcp_client

router = APIRouter(prefix="/search", tags=["search"])


# ──────────────────────────────────────────────
# 응답 모델
# ──────────────────────────────────────────────
class StoreItem(BaseModel):
    가맹점명: str = ""
    소재지: str = ""
    취급품목: str = ""
    디지털형_가맹_여부: str = ""
    소속_시장명: str = ""

    class Config:
        populate_by_name = True


class SearchResponse(BaseModel):
    total: int
    stores: list[dict]


class StatisticsResponse(BaseModel):
    area: str
    category: Optional[str]
    total: int
    top_items: dict
    top_regions: dict


# ──────────────────────────────────────────────
# 엔드포인트
# ──────────────────────────────────────────────
@router.get("/area", response_model=SearchResponse, summary="지역 검색")
def search_by_area(
    area: str = Query(..., description="검색할 지역명 (예: 서울, 경기)"),
    limit: int = Query(10, ge=1, le=100),
):
    result = mcp_client.search_by_area(area, limit)
    return SearchResponse(total=result["total"], stores=result["stores"])


@router.get("/name", response_model=SearchResponse, summary="시장명 검색")
def search_by_name(
    name: str = Query(..., description="시장명 또는 상점가명"),
    limit: int = Query(10, ge=1, le=100),
):
    result = mcp_client.search_by_name(name, limit)
    return SearchResponse(total=result["total"], stores=result["stores"])


@router.get("/combined", response_model=SearchResponse, summary="지역+시장명 복합 검색")
def search_combined(
    area: str = Query(..., description="지역명"),
    name: str = Query(..., description="시장명"),
    limit: int = Query(10, ge=1, le=100),
):
    result = mcp_client.search_by_area_and_name(area, name, limit)
    return SearchResponse(total=result["total"], stores=result["stores"])


@router.get("/stores", response_model=SearchResponse, summary="지역·업종·디지털 복합 검색")
def search_stores(
    area: Optional[str] = Query(None, description="지역명 (선택)"),
    category: Optional[str] = Query(None, description="업종 (선택, 예: 카페, 자전거)"),
    digital_only: bool = Query(False, description="디지털 상품권 가능 가맹점만"),
    limit: int = Query(10, ge=1, le=100),
):
    result = mcp_client.search_stores(area, category, digital_only, limit)
    return SearchResponse(total=result["total"], stores=result["stores"])


@router.get("/statistics", response_model=StatisticsResponse, summary="지역 통계")
def get_statistics(
    area: str = Query(..., description="통계를 조회할 지역명"),
    category: Optional[str] = Query(None, description="업종 필터 (선택)"),
):
    result = mcp_client.get_statistics(area, category)
    return StatisticsResponse(
        area=result["area"],
        category=result.get("category"),
        total=result["total"],
        top_items=result.get("top_items", {}),
        top_regions=result.get("top_regions", {}),
    )
