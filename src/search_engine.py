import pandas as pd
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

# 통계
def statistics(df: pd.DataFrame) -> dict:
    stats = {}
    
    # 1. 전체 가맹점 수
    stats['total_count'] = len(df)
    
    # 2. 지역별(소재지) 가맹점 분포 (상위 5개)
    # 주소에서 앞부분(시/도)만 추출하여 계산
    # df['city'] = df['소재지'].str.split().str[0]
    # stats['city_distribution'] = df['city'].value_counts().head(5).to_dict()
    
    city_series = df["소재지"].str.split().str[0]
    city_counts = city_series.value_counts()

    # 3. 가장 활성화된 시장 (가맹점이 많은 시장 상위 5개) + 차지하는 비율
    # stats['top_markets'] = df['소속 시장명(또는 상점가)'].value_counts().head(5).to_dict()
    stats['top_markets'] = city_counts.head(5).to_dict()

    stats["city_distribution_ratio"] = (
        (city_counts / city_counts.sum()).round(3).to_dict()
    )

    # 4. 주요 취급 품목 순위
    stats['top_items'] = df['취급품목'].value_counts().head(5).to_dict()

    return stats

# def statistics_v2(df: pd.DataFrame) -> dict:
#     if df.empty:
#         return {"error": "데이터가 없습니다."}

#     stats = {
#         "total": len(df),
#         "top_regions": df['소재지'].str.split().str[1].value_counts().head(3).to_dict(), # '구' 단위 상위 3개
#         "category_ratio": (df['취급품목'].value_counts(normalize=True).head(3) * 100).to_dict(), # 상위 품목 비율(%)
#     }
    
#     # 인사이트 생성 로직
#     most_common_cat = list(stats['category_ratio'].keys())[0]
#     stats['insight'] = f"이 지역은 {most_common_cat} 업종이 가장 활성화되어 있습니다."
    
#     return stats


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
    statistics_seoul = statistics(df1)
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