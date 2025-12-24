import pandas as pd
from typing import Optional

'''
목적: 검색 함수 개발
내용:
- 지역 검색 함수
- 업종 검색 함수
- 복합 검색 함수
- 통계 함수
- 각 함수 테스트
- 성능 측정

"출력: 검증된 검색 로직"
'''
# 지역검색 함수, 업종검색 함수, 복합 검색 함수, 통계

df1 = pd.read_csv('cleaned_onnuri.csv')
df2 = pd.read_csv('area_onnuri.csv')

# 지역 기반 
def area_search(df: pd.DataFrame, area: str) -> pd.DataFrame:
    area_df = df[df['소재지'].str.contains(area, na=False)]
    if area_df.empty:
        return pd.DataFrame() # 빈 데이터프레임 반환
    return area_df

# 시장명 기반 
def name_search(df: pd.DataFrame, name: str) -> pd.DataFrame:
    name_df = df[df['소속 시장명(또는 상점가)'].str.contains(name, na=False)]
    if name_df.empty:
        return pd.DataFrame() # 빈 데이터프레임 반환
    return name_df

# 지역+시장명 기반
def multi_search(df: pd.DataFrame, area: str, name: str) -> pd.DataFrame:
    area_name_df = df[(df['소속 시장명(또는 상점가)'].str.contains(name, na=False)) & (df['소재지'].str.contains(area, na=False))]
    if area_name_df.empty:
        return pd.DataFrame()
    return area_name_df

# 통계 함수: 특정 지역(area)에 대한 가맹점 통계 생성
def statistics(df: pd.DataFrame, area: str, category: Optional[str] = None) -> dict:
    stats = {}

      # --------------------------------------------------
    # 1. 지역(area) 기준 필터링
    # 소재지 컬럼에 지역명이 포함된 데이터만 추출
    # --------------------------------------------------
    filtered_df = df[df["소재지"].str.contains(area, na=False)]

    # --------------------------------------------------
    # 2. 업종(category) 기준 추가 필터링 (선택)
    # category가 None이 아닐 때만 적용
    # --------------------------------------------------
    if category:
        filtered_df = filtered_df[
            filtered_df["취급품목"].str.contains(category, na=False)
        ]

    # --------------------------------------------------
    # 3. 전체 가맹점 수
    # (지역 + 업종 조건을 모두 만족하는 데이터 기준)
    # --------------------------------------------------
    stats["total_count"] = len(filtered_df)

    # 조건에 맞는 데이터가 없을 경우 조기 반환
    if filtered_df.empty:
        stats["message"] = "해당 조건에 맞는 가맹점이 없습니다."
        return stats

    # --------------------------------------------------
    # 4. 시/도(또는 시/군)별 가맹점 분포
    # 소재지 문자열에서 첫 단어만 추출
    # --------------------------------------------------
    city_series = (
        filtered_df["소재지"]
        .str.split()
        .str[0]
    )

    city_counts = city_series.value_counts()

    stats["top_regions"] = city_counts.head(5).to_dict()

    stats["region_distribution_ratio"] = (
        (city_counts / city_counts.sum())
        .round(3)
        .to_dict()
    )

    # --------------------------------------------------
    # 5. 주요 취급 품목 TOP 5
    # (업종을 지정하지 않았을 때만 의미 있음)
    # --------------------------------------------------
    stats["top_items"] = (
        filtered_df["취급품목"]
        .value_counts()
        .head(5)
        .to_dict()
    )
    return stats



# 테스트
if __name__ == "__main__":
    # 지역 검색
    seoul_stores = area_search(df1, '서울')
    print(f"서울 가맹점: {len(seoul_stores)}개")
    print(seoul_stores.head())
    
    # 시장명 검색
    market_stores = name_search(df1, '중앙시장')
    print(f"\n중앙시장 가맹점: {len(market_stores)}개")
    print(market_stores.head())

    # 지역+시장명 검색
    seoul_market_stores = multi_search(df1, '서울', '중앙시장')
    print(f"서울 중앙시장 가맹점: {len(seoul_market_stores)}개")
    print(seoul_market_stores.head())

    # 통계
    statistics_seoul = statistics(df1, '서울')
    print(f"통계")
    print(statistics_seoul)

# 1. 문서화 (정보 합치기)
from langchain_core.documents import Document

# 1. 문서화 리스트 생성
df1['full_text'] = df1.apply(lambda r: f"상호명: {r['가맹점명']} | 위치: {r['소재지']} | 주요품목: {r['취급품목']}", axis=1)

document_list = []

for index, row in df1.iterrows():
    content = row['full_text']
    metadata = {"id": index, "name": row['가맹점명'], "location": row['소재지']}
    
    # 여기서 Document 객체 생성
    doc = Document(page_content=content, metadata=metadata)
    document_list.append(doc)
    

for doc in document_list[:15]:
    print(doc)