"""
/api/report  — 조건 필터링 후 PDF 보고서 생성
"""
import datetime
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fpdf import FPDF

router = APIRouter()

# ── 상수 ──────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
_CSV  = _ROOT / "cleaned_onnuri.csv"
_FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"
_FONT_BOLD    = r"C:\Windows\Fonts\malgunbd.ttf"

CATEGORY_EXPANSIONS: dict[str, list[str]] = {
    "카페":   ["카페", "커피", "디저트", "베이커리"],
    "음식점": ["음식점", "식당", "한식", "중식", "일식"],
    "자전거": ["자전거", "바이크"],
    "미용":   ["미용", "헤어", "네일", "뷰티"],
    "의류":   ["의류", "옷", "패션"],
    "고기":   ["고기", "구이", "삼겹살", "갈비"],
}

# ── CSV 로드 (모듈 임포트 시 1회) ─────────────────────────────────
df = pd.read_csv(_CSV, encoding="utf-8-sig")

# matplotlib 한국어 폰트 등록
fm.fontManager.addfont(_FONT_REGULAR)
_font_prop = fm.FontProperties(fname=_FONT_REGULAR)
plt.rcParams["font.family"] = _font_prop.get_name()
plt.rcParams["axes.unicode_minus"] = False


# ── 헬퍼 ──────────────────────────────────────────────────────────
def _filter(region: str, category: str, digital_only: bool, paper_only: bool) -> pd.DataFrame:
    result = df.copy()
    if region:
        result = result[result["소재지"].str.contains(region, na=False)]
    if category:
        keywords = CATEGORY_EXPANSIONS.get(category, [category])
        mask = pd.Series([False] * len(result), index=result.index)
        for kw in keywords:
            mask |= result["취급품목"].str.contains(kw, na=False, case=False)
        result = result[mask]
    if digital_only:
        result = result[result["디지털형 가맹 여부"] == "Y"]
    if paper_only:
        result = result[result["지류형 가맹 여부"] == "Y"]
    return result


def _build_chart(filtered: pd.DataFrame) -> bytes:
    """업종 분포 상위 10개 가로 막대 차트 → PNG bytes"""
    top = filtered["취급품목"].value_counts().head(10)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = ["#2563eb"] + ["#60a5fa"] * (len(top) - 1)
    bars = ax.barh(top.index[::-1], top.values[::-1], color=colors[::-1], height=0.6)
    ax.bar_label(bars, fmt="%,.0f", padding=5, fontsize=9)
    ax.set_xlabel("가맹점 수", fontsize=10)
    ax.set_title("업종별 가맹점 수 (상위 10개)", fontsize=12, pad=10)
    ax.set_xlim(0, top.max() * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _build_pie(filtered: pd.DataFrame) -> bytes:
    """디지털 / 지류 비율 파이 차트 → PNG bytes"""
    digital = (filtered["디지털형 가맹 여부"] == "Y").sum()
    paper   = (filtered["지류형 가맹 여부"]   == "Y").sum()
    both    = ((filtered["디지털형 가맹 여부"] == "Y") & (filtered["지류형 가맹 여부"] == "Y")).sum()
    digital_only_cnt = digital - both
    paper_only_cnt   = paper   - both
    neither = len(filtered) - digital - paper + both

    labels = ["디지털+지류", "디지털만", "지류만", "미분류"]
    sizes  = [both, digital_only_cnt, paper_only_cnt, max(0, neither)]
    colors = ["#2563eb", "#60a5fa", "#a78bfa", "#e5e7eb"]

    non_zero = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
    if not non_zero:
        return b""
    labels, sizes, colors = zip(*non_zero)

    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=90,
        textprops={"fontsize": 9},
    )
    ax.set_title("가맹 유형 분포", fontsize=11, pad=10)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


class KoreanPDF(FPDF):
    """맑은 고딕 한국어 PDF"""

    def __init__(self):
        super().__init__()
        self.add_font("MG",  fname=_FONT_REGULAR)
        self.add_font("MGB", fname=_FONT_BOLD)
        self.set_auto_page_break(auto=True, margin=15)

    # ── 섹션 제목 ──
    def section_title(self, text: str):
        self.set_font("MGB", size=12)
        self.set_fill_color(239, 246, 255)
        self.set_text_color(30, 64, 175)
        self.cell(0, 9, f"  {text}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    # ── 키-값 행 ──
    def kv_row(self, label: str, value: str, fill: bool = False):
        self.set_font("MGB", size=9)
        self.set_fill_color(248, 250, 252)
        self.cell(50, 8, f"  {label}", border=1, fill=fill)
        self.set_font("MG",  size=9)
        self.cell(0,  8, f"  {value}", border=1, new_x="LMARGIN", new_y="NEXT", fill=fill)

    # ── 테이블 헤더 ──
    def table_header(self, headers: list[str], widths: list[int]):
        self.set_font("MGB", size=8)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        for w, h in zip(widths, headers):
            self.cell(w, 8, h, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)

    # ── 테이블 행 ──
    def table_row(self, values: list[str], widths: list[int], aligns: list[str], even: bool):
        self.set_font("MG", size=7)
        self.set_fill_color(248, 250, 252 if even else 255)
        for w, val, align in zip(widths, values, aligns):
            self.cell(w, 6.5, val, border=1, fill=even, align=align)
        self.ln()


# ── 엔드포인트 ─────────────────────────────────────────────────────
@router.get("/report")
def generate_report(
    region: str = "",
    category: str = "",
    digital_only: bool = False,
    paper_only: bool = False,
):
    # 1) 필터링
    filtered = _filter(region, category, digital_only, paper_only)
    if filtered.empty:
        raise HTTPException(status_code=404, detail="조건에 맞는 가맹점이 없습니다.")

    total         = len(filtered)
    digital_count = int((filtered["디지털형 가맹 여부"] == "Y").sum())
    paper_count   = int((filtered["지류형 가맹 여부"]   == "Y").sum())

    # 2) 차트 생성
    chart_png = _build_chart(filtered)
    pie_png   = _build_pie(filtered)

    # 3) PDF 조립
    pdf = KoreanPDF()

    # ── 1페이지: 요약 ─────────────────────────────────────────────
    pdf.add_page()

    # 타이틀 배너
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("MGB", size=18)
    pdf.cell(0, 16, "온누리상품권 가맹점 보고서", new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
    pdf.ln(2)

    # 생성 일시
    pdf.set_text_color(120, 120, 120)
    pdf.set_font("MG", size=8)
    now = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    pdf.cell(0, 6, f"생성: {now}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.ln(4)

    # 적용 필터
    pdf.section_title("적용 필터")
    conds = [
        ("지역",   region   or "전체"),
        ("업종",   category or "전체"),
        ("디지털", "가맹점만" if digital_only else "전체"),
        ("지류",   "가맹점만" if paper_only   else "전체"),
    ]
    for i, (k, v) in enumerate(conds):
        pdf.kv_row(k, v, fill=(i % 2 == 0))
    pdf.ln(6)

    # 요약 통계
    pdf.section_title("요약 통계")
    stats = [
        ("총 가맹점 수",   f"{total:,}개"),
        ("디지털형 가맹",  f"{digital_count:,}개  ({digital_count/total*100:.1f}%)"),
        ("지류형 가맹",    f"{paper_count:,}개  ({paper_count/total*100:.1f}%)"),
    ]
    for i, (k, v) in enumerate(stats):
        pdf.kv_row(k, v, fill=(i % 2 == 0))
    pdf.ln(6)

    # 차트: 업종 분포
    pdf.section_title("업종별 가맹점 분포")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(chart_png)
        chart_path = f.name
    try:
        pdf.image(chart_path, w=175)
    finally:
        os.unlink(chart_path)
    pdf.ln(4)

    # 차트: 가맹 유형 파이
    if pie_png:
        pdf.section_title("가맹 유형 분포")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(pie_png)
            pie_path = f.name
        try:
            pdf.image(pie_path, x=55, w=95)
        finally:
            os.unlink(pie_path)

    # ── 2페이지~: 가맹점 목록 ─────────────────────────────────────
    pdf.add_page()
    pdf.section_title(f"가맹점 목록  (상위 200개 / 전체 {total:,}개 표시)")

    col_w = [10, 48, 36, 48, 18, 18]
    headers = ["No", "가맹점명", "소재지", "취급품목", "디지털", "지류"]
    aligns  = ["C", "L", "L", "L", "C", "C"]

    pdf.table_header(headers, col_w)

    for i, (_, row) in enumerate(filtered.head(200).iterrows(), 1):
        # 페이지 넘김 시 헤더 반복
        if pdf.get_y() > 272:
            pdf.add_page()
            pdf.table_header(headers, col_w)

        digital_yn = "O" if row.get("디지털형 가맹 여부") == "Y" else "X"
        paper_yn   = "O" if row.get("지류형 가맹 여부")   == "Y" else "X"

        vals = [
            str(i),
            str(row.get("가맹점명", ""))[:22],
            str(row.get("소재지",   ""))[:16],
            str(row.get("취급품목", ""))[:22],
            digital_yn,
            paper_yn,
        ]
        pdf.table_row(vals, col_w, aligns, even=(i % 2 == 0))

    # 4) 반환
    pdf_bytes = BytesIO(pdf.output())
    pdf_bytes.seek(0)

    fname = f"onnuri_{region or '전체'}_{category or '전체'}.pdf"
    from urllib.parse import quote
    encoded = quote(fname, safe="")

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
