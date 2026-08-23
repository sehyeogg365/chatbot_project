"""
목적: category_taxonomy.py의 CATEGORY_EXPANSIONS(카테고리 태그 매핑)를
      networkx + matplotlib으로 시각화.

출력:
  experiments/ontology_graph.png           대분류(허브) + 소분류(키워드) 전체 그래프
  experiments/ontology_graph_overview.png  대분류끼리만 연결한 단순 개요 그래프
                                            (키워드를 공유하는 대분류끼리 선으로 연결)
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
import networkx as nx

from category_taxonomy import CATEGORY_EXPANSIONS

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

CATEGORIES = list(CATEGORY_EXPANSIONS.keys())
CMAP = plt.get_cmap("gist_rainbow")
CATEGORY_COLORS = {cat: CMAP(i / len(CATEGORIES)) for i, cat in enumerate(CATEGORIES)}

OUT_FULL = ROOT / "experiments" / "ontology_graph.png"
OUT_OVERVIEW = ROOT / "experiments" / "ontology_graph_overview.png"


# ── 전체 그래프 (대분류 + 소분류) ────────────────────────────────────────────
def build_full_graph() -> tuple[nx.Graph, dict]:
    """대분류를 큰 원 위에 배치하고, 각 대분류의 키워드를 부채꼴(스포크) 모양으로
    바깥쪽으로 뻗어나가게 배치한다. 키워드 개수가 많은 대분류일수록 반지름이
    커져서 인접 대분류의 키워드 군집과 겹치지 않는다."""
    g = nx.Graph()
    pos: dict[str, tuple[float, float]] = {}

    n = len(CATEGORIES)
    R1 = 10.0        # 대분류 배치 반지름
    node_gap = 1.3    # 키워드 하나당 바깥으로 밀려나는 거리
    angle_step = 0.05  # 키워드 하나당 각도 편차 (라디안)

    for i, cat in enumerate(CATEGORIES):
        theta = 2 * math.pi * i / n
        cx, cy = R1 * math.cos(theta), R1 * math.sin(theta)
        g.add_node(cat, kind="category")
        pos[cat] = (cx, cy)

        keywords = CATEGORY_EXPANSIONS[cat]
        m = len(keywords)
        for j, kw in enumerate(keywords):
            node_id = f"{cat}::{kw}"
            radius = R1 + node_gap * (j + 1)
            angle = theta + (j - (m - 1) / 2) * angle_step
            kx, ky = radius * math.cos(angle), radius * math.sin(angle)
            g.add_node(node_id, kind="keyword", label=kw, parent=cat)
            pos[node_id] = (kx, ky)
            g.add_edge(cat, node_id)

    return g, pos


def draw_full_graph() -> None:
    g, pos = build_full_graph()

    category_nodes = [n for n, d in g.nodes(data=True) if d["kind"] == "category"]
    keyword_nodes = [n for n, d in g.nodes(data=True) if d["kind"] == "keyword"]

    fig, ax = plt.subplots(figsize=(24, 24))

    # 엣지: 부모 대분류 색으로, 옅게
    for cat in category_nodes:
        edges = [(u, v) for u, v in g.edges() if cat in (u, v)]
        nx.draw_networkx_edges(
            g, pos, edgelist=edges, edge_color=[CATEGORY_COLORS[cat]],
            width=1.0, alpha=0.5, ax=ax,
        )

    # 소분류(키워드) 노드: 부모 색을 옅게
    keyword_colors = [
        (*CATEGORY_COLORS[g.nodes[n]["parent"]][:3], 0.55) for n in keyword_nodes
    ]
    nx.draw_networkx_nodes(
        g, pos, nodelist=keyword_nodes, node_size=180,
        node_color=keyword_colors, edgecolors="white", linewidths=0.4, ax=ax,
    )
    keyword_labels = {n: g.nodes[n]["label"] for n in keyword_nodes}
    for n, (x, y) in pos.items():
        if n in keyword_labels:
            ax.text(x, y + 0.22, keyword_labels[n], fontsize=7, ha="center", va="bottom", color="#333333")

    # 대분류 노드: 크고 진하게
    category_colors = [CATEGORY_COLORS[n] for n in category_nodes]
    nx.draw_networkx_nodes(
        g, pos, nodelist=category_nodes, node_size=2200,
        node_color=category_colors, edgecolors="black", linewidths=1.2, ax=ax,
    )
    for n in category_nodes:
        x, y = pos[n]
        ax.text(x, y, n, fontsize=13, fontweight="bold", ha="center", va="center")

    ax.set_title(
        "온누리 가맹점 카테고리 태그 매핑 (경량 온톨로지) — 대분류 → 취급품목 키워드",
        fontsize=18, pad=20,
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT_FULL, dpi=150)
    plt.close(fig)
    print(f"저장 완료: {OUT_FULL}")


# ── 개요 그래프 (대분류끼리만 연결) ──────────────────────────────────────────
def build_overview_graph() -> nx.Graph:
    """두 대분류가 같은 키워드를 공유하면 두 대분류를 연결한다.
    (예: '음식점' 안에 '한식'/'중식'/'일식'/'분식' 키워드가 포함되어 있으므로
    '음식점' 노드가 그 네 대분류와 모두 연결된다.)"""
    g = nx.Graph()
    g.add_nodes_from(CATEGORIES)

    keyword_to_cats: dict[str, list[str]] = {}
    for cat, kws in CATEGORY_EXPANSIONS.items():
        for kw in kws:
            keyword_to_cats.setdefault(kw, []).append(cat)

    for kw, cats in keyword_to_cats.items():
        cats = sorted(set(cats))
        for a in range(len(cats)):
            for b in range(a + 1, len(cats)):
                g.add_edge(cats[a], cats[b], keyword=kw)

    return g


def draw_overview_graph() -> None:
    g = build_overview_graph()
    pos = nx.circular_layout(g, scale=10)

    sizes = [400 + 220 * len(CATEGORY_EXPANSIONS[n]) for n in g.nodes()]
    colors = [CATEGORY_COLORS[n] for n in g.nodes()]

    fig, ax = plt.subplots(figsize=(12, 12))
    nx.draw_networkx_edges(g, pos, edge_color="#999999", width=1.5, alpha=0.6, ax=ax)
    nx.draw_networkx_nodes(
        g, pos, node_size=sizes, node_color=colors, edgecolors="black", linewidths=1.0, ax=ax,
    )
    label_pos = {n: (x, y + 0.9) for n, (x, y) in pos.items()}
    nx.draw_networkx_labels(
        g, label_pos, font_size=11, font_weight="bold", font_family="Malgun Gothic", ax=ax,
    )

    ax.set_title(
        "카테고리 태그 매핑 — 대분류 개요 (노드 크기 = 하위 키워드 수, 선 = 키워드 공유)",
        fontsize=15, pad=20,
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT_OVERVIEW, dpi=150)
    plt.close(fig)
    print(f"저장 완료: {OUT_OVERVIEW}")


if __name__ == "__main__":
    draw_overview_graph()
    draw_full_graph()
