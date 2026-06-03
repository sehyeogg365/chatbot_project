"""Agent 동작 검증 스크립트"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.chatbot import process_query

tests = [
    ("서울 디지털 가능한 음식점 알려줘",     "Tool1: region=서울, digital_only=True, category=음식점"),
    ("경기 자전거 매장 몇 개야?",              "Tool1: region=경기, category=자전거"),
    ("디지털 상품권 어떻게 써?",               "Tool3: FAQ"),
    ("분위기 좋은 카페 추천해줘",              "Tool2: RAG"),
    ("부산 지류형 가능한 카페",               "Tool1: region=부산, paper_only=True, category=카페"),
]

for q, expected_tool in tests:
    print(f"\n{'='*60}")
    print(f"[질문] {q}")
    print(f"[예상] {expected_tool}")
    print("-" * 60)
    ans = process_query(q, [])
    print(ans[:600])
