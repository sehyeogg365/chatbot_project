import styles from './Page.module.css'

const TECH_STACK = [
  { layer: '프론트엔드',  items: ['React 18', 'Vite', 'CSS Modules'] },
  { layer: '백엔드 API', items: ['FastAPI', 'Uvicorn'] },
  { layer: 'AI / LLM',   items: ['Gemini 2.5 Flash', 'LangGraph', 'LangChain'] },
  { layer: '데이터 저장', items: ['ChromaDB (벡터DB)', 'CSV (가맹점 원본)'] },
  { layer: '임베딩',      items: ['OpenAI text-embedding-3-small'] },
]

export default function Architecture() {
  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <h1 className={styles.pageTitle}>🔄 DataFlow / 시스템 아키텍처</h1>
        <p className={styles.pageSubtitle}>온누리상품권 가맹점 챗봇의 데이터 흐름과 시스템 구성</p>

        {/* 시스템 아키텍처 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🏗 시스템 아키텍처</h2>
          <div className={styles.archImageWrap}>
            <img
              src="./docs/refactor/리팩토링 시스템 아키텍처.png"
              alt="시스템 아키텍처"
              onError={(e) => {
                e.currentTarget.parentElement.style.display = 'none'
              }}
            />
            <p className={styles.archCaption}>시스템 아키텍처</p>
          </div>
        </div>

        {/* DataFlow */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>📊 DataFlow</h2>
          <div className={styles.archImageWrap}>
            <img
              src="./docs/refactor/리팩토링 DataFlow.png"
              alt="DataFlow"
              onError={(e) => {
                e.currentTarget.parentElement.style.display = 'none'
              }}
            />
            <p className={styles.archCaption}>DataFlow</p>
          </div>
        </div>

        {/* 요청 처리 흐름 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>⚡ 요청 처리 흐름</h2>
          <ol className={styles.stepList}>
            <li className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>사용자 입력</p>
                <p className={styles.stepNote}>React UI에서 질문 입력 → <span className={styles.inlineCode}>POST /api/chat</span></p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>LangGraph Agent 판단</p>
                <p className={styles.stepNote}>질문 유형 분석 → 적합한 Tool 선택 (pandas_filter / rag_search / faq_answer)</p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>3</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>Tool 실행</p>
                <p className={styles.stepNote}>
                  정형 필터링(Pandas) / 벡터 유사도 검색(ChromaDB) / FAQ 매칭 중 선택 실행
                </p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>4</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>Gemini 2.5 Flash 응답 생성</p>
                <p className={styles.stepNote}>Tool 결과를 바탕으로 자연어 답변 생성</p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>5</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>React UI 표시</p>
                <p className={styles.stepNote}>JSON 응답 수신 → 채팅 버블로 렌더링</p>
              </div>
            </li>
          </ol>
        </div>

        {/* 기술 스택 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🛠 기술 스택</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {TECH_STACK.map(({ layer, items }) => (
              <div key={layer} className={styles.card} style={{ padding: '14px 20px' }}>
                <p className={styles.cardTitle} style={{ marginBottom: '8px' }}>{layer}</p>
                <div className={styles.infoGrid}>
                  {items.map(item => (
                    <span key={item} className={styles.infoBadge}>{item}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tool 구성 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🔧 Agent Tool 구성</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className={styles.card}>
              <p className={styles.cardTitle}>Tool 1 — pandas_filter</p>
              <p className={styles.stepNote}>지역·품목·디지털/지류 조건으로 CSV 데이터 정형 필터링. 통계 및 개수 질문에 사용.</p>
            </div>
            <div className={styles.card}>
              <p className={styles.cardTitle}>Tool 2 — rag_search</p>
              <p className={styles.stepNote}>ChromaDB 벡터 유사도 검색. "분위기 좋은 카페" 같은 자연어 묘사 질문에 사용.</p>
            </div>
            <div className={styles.card}>
              <p className={styles.cardTitle}>Tool 3 — faq_answer</p>
              <p className={styles.stepNote}>온누리상품권 정책·사용법·규정 FAQ 답변. 유효기간·할인·환불 등 정책 질문에 사용.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
