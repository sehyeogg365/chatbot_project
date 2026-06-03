import styles from './Page.module.css'

const IMAGES = [
  { src: '/docs/서울 가맹점 수.png',      caption: '서울 가맹점 수 조회' },
  { src: '/docs/경기 자전거 가맹점 수.png', caption: '경기 자전거 가맹점 수' },
  { src: '/docs/서울 가맹점 통계.png',     caption: '서울 가맹점 통계' },
  { src: '/docs/서울 업종 비율.png',       caption: '서울 업종 비율' },
  { src: '/docs/RAG 기반 답변.png',       caption: 'RAG 기반 답변' },
]

const GOOD = [
  { q: '서울 자전거 몇 개?',       reason: '지역 + 업종 + 의도 명확' },
  { q: '강남역 근처 맛집 추천',    reason: '위치 + 카테고리 + 의도' },
  { q: '디지털 되는 카페',         reason: '조건 + 카테고리' },
]

const BAD = [
  { q: '카페',     problem: '너무 광범위',  fix: '"서울 카페 추천"' },
  { q: '많이 있어?', problem: '의도 불명확', fix: '"서울 가맹점 몇 개?"' },
  { q: '거기',     problem: '맥락 없음',    fix: '"강남역 근처"' },
]

export default function QuestionGuide() {
  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <h1 className={styles.pageTitle}>💡 질문 유형 가이드</h1>
        <p className={styles.pageSubtitle}>챗봇을 효과적으로 활용하는 질문 유형과 예시를 안내합니다.</p>

        {/* 통계 질문 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>📊 통계 질문 (개수 / 통계)</h2>
          <div className={styles.card}>
            <span className={styles.cardTag}>키워드</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
              {['몇 개', '개수', '통계', '비율'].map(kw => (
                <span key={kw} className={styles.inlineCode}>{kw}</span>
              ))}
            </div>

            <p className={styles.cardTitle}>예시</p>
            <ul className={styles.exampleList}>
              <li className={styles.exampleItem}>서울 한식 몇 개?</li>
              <li className={styles.exampleItem}>경기도 음식점 개수</li>
              <li className={styles.exampleItem}>제주도 가맹점 통계</li>
              <li className={styles.exampleItem}>서울 가맹점 업종 통계</li>
            </ul>

            <p className={styles.cardTitle} style={{ marginTop: '14px' }}>제공 정보</p>
            <div className={styles.infoGrid}>
              {['정확한 개수', '종류별 분포', '대표 가맹점 10개', '디지털 상품권 여부'].map(info => (
                <span key={info} className={styles.infoBadge}>{info}</span>
              ))}
            </div>
          </div>
        </div>

        {/* 추천/검색 질문 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🔍 추천 / 검색 질문</h2>
          <div className={styles.card}>
            <span className={styles.cardTag}>키워드</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
              {['추천', '알려줘', '찾아줘', '어디'].map(kw => (
                <span key={kw} className={styles.inlineCode}>{kw}</span>
              ))}
            </div>

            <p className={styles.cardTitle}>예시</p>
            <ul className={styles.exampleList}>
              <li className={styles.exampleItem}>서울 유명한 카페 추천</li>
              <li className={styles.exampleItem}>강남역 근처 맛집</li>
              <li className={styles.exampleItem}>디지털 상품권 되는 곳</li>
              <li className={styles.exampleItem}>부산 자전거 가게 알려줘</li>
            </ul>

            <p className={styles.cardTitle} style={{ marginTop: '14px' }}>제공 정보</p>
            <div className={styles.infoGrid}>
              {['3~5개 추천', '가맹점 특징', '위치 정보', '디지털 상품권 여부'].map(info => (
                <span key={info} className={styles.infoBadge}>{info}</span>
              ))}
            </div>
          </div>
        </div>

        {/* 대화형 질문 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>💬 대화형 질문 (연속 필터링)</h2>
          <div className={styles.card}>
            <p className={styles.cardTitle}>대화 예시</p>
            <div className={styles.codeBlock}
              style={{ fontFamily: 'inherit', fontSize: '14px' }}>
              <span style={{ color: '#93c5fd' }}>사용자:</span> "서울 음식점 알려줘"{'\n'}
              <span style={{ color: '#6ee7b7' }}>챗봇:</span>    [15,000개 결과 요약]{'\n\n'}
              <span style={{ color: '#93c5fd' }}>사용자:</span> "중국음식만"{'\n'}
              <span style={{ color: '#6ee7b7' }}>챗봇:</span>    [500개로 필터링]{'\n\n'}
              <span style={{ color: '#93c5fd' }}>사용자:</span> "디지털 되는 곳"{'\n'}
              <span style={{ color: '#6ee7b7' }}>챗봇:</span>    [300개로 재필터링]
            </div>
            <p className={styles.stepNote} style={{ marginTop: '10px' }}>
              이전 대화 맥락이 유지되어 점진적으로 조건을 추가할 수 있습니다.
            </p>
          </div>
        </div>

        {/* 질문 잘하는 법 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🎯 질문 잘하는 법</h2>

          <h3 className={styles.sectionSubtitle}>✅ 좋은 예시</h3>
          <table className={styles.table} style={{ marginBottom: '20px' }}>
            <thead>
              <tr>
                <th>질문</th>
                <th>이유</th>
              </tr>
            </thead>
            <tbody>
              {GOOD.map(({ q, reason }) => (
                <tr key={q}>
                  <td><span className={styles.goodBadge}>"{q}"</span></td>
                  <td>{reason}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3 className={styles.sectionSubtitle}>❌ 나쁜 예시</h3>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>질문</th>
                <th>문제점</th>
                <th>개선</th>
              </tr>
            </thead>
            <tbody>
              {BAD.map(({ q, problem, fix }) => (
                <tr key={q}>
                  <td><span className={styles.badBadge}>"{q}"</span></td>
                  <td>{problem}</td>
                  <td><span className={styles.inlineCode}>{fix}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 챗봇 실행 화면 예시 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>📌 챗봇 실행 화면 예시</h2>
          <div className={styles.imageGrid}>
            {IMAGES.map(({ src, caption }) => (
              <div key={src} className={styles.imageCard}>
                <img
                  src={src}
                  alt={caption}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
                <p className={styles.imageCaption}>{caption}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
