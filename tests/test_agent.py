"""Tool-calling Agent의 도구 선택(라우팅) 검증 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.chatbot import agent_app


def get_called_tools(query: str) -> set[str]:
    """질문에 대해 에이전트가 호출한 도구 이름 집합을 반환한다."""
    result = agent_app.invoke({"messages": [HumanMessage(content=query)]})
    called = set()
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            for tool_call in msg.tool_calls:
                called.add(tool_call["name"])
    return called


@pytest.mark.parametrize(
    "query, expected_tool",
    [
        ("서울 디지털 가능한 음식점", "pandas_filter"),
        ("경기 자전거 매장 몇 개", "pandas_filter"),
        ("디지털 상품권 어떻게 써", "faq_answer"),
        ("서울 한식 추천해줘", "rag_search"),
        ("부산 카페 디지털 가능", "pandas_filter"),
    ],
)
def test_agent_tool_selection(query, expected_tool):
    called_tools = get_called_tools(query)
    assert expected_tool in called_tools, (
        f"'{query}' 질문에서 '{expected_tool}' 도구가 호출되지 않음 "
        f"(실제 호출: {called_tools or '없음'})"
    )
