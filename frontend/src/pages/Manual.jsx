import styles from './Page.module.css'

export default function Manual() {
  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <h1 className={styles.pageTitle}>📖 사용자 매뉴얼</h1>
        <p className={styles.pageSubtitle}>온누리상품권 가맹점 챗봇 개발 환경 구축 및 실행 가이드</p>

        {/* 가상환경 구축 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🐍 가상환경 구축</h2>
          <ol className={styles.stepList}>
            <li className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>Python 3.11 가상환경 생성</p>
                <div className={styles.codeBlock}>conda create --name new_env python=3.11</div>
                <p className={styles.stepNote}>Python 3.11 버전 이상으로 생성</p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>필수 패키지 설치</p>
                <div className={styles.codeBlock}>pip install pandas sqlalchemy langchain-openai langgraph{'\n'}pip install langchain-google-genai langchain-community{'\n'}pip install chromadb python-dotenv fastapi uvicorn</div>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>3</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>환경 설정 저장</p>
                <div className={styles.codeBlock}>pip freeze &gt; requirements.txt</div>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>4</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>저장된 환경 복원 (다른 환경에서)</p>
                <div className={styles.codeBlock}>pip install -r requirements.txt</div>
              </div>
            </li>
          </ol>
        </div>

        {/* 프론트엔드 환경 설정 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>⚛️ 프론트엔드 환경 설정 (React)</h2>
          <ol className={styles.stepList}>
            <li className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>frontend 디렉토리로 이동</p>
                <div className={styles.codeBlock}>cd frontend</div>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>Node.js 패키지 설치</p>
                <div className={styles.codeBlock}>npm install</div>
              </div>
            </li>
          </ol>
        </div>

        {/* 빠른 시작 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🚀 빠른 시작</h2>

          <h3 className={styles.sectionSubtitle}>1단계: 가상환경 활성화</h3>
          <div className={styles.codeBlock}>conda activate new_env</div>

          <h3 className={styles.sectionSubtitle}>2단계: 백엔드 서버 실행</h3>
          <div className={styles.codeBlock}>uvicorn backend.main:app --reload</div>
          <p className={styles.stepNote}>→ http://localhost:8000 에서 API 서버 실행</p>

          <h3 className={styles.sectionSubtitle}>3단계: 프론트엔드 개발 서버 실행</h3>
          <div className={styles.codeBlock}>cd frontend{'\n'}npm run dev</div>
          <p className={styles.stepNote}>→ http://localhost:5173 에서 챗봇 UI 실행</p>
        </div>

        {/* 챗봇 사용법 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>💬 챗봇 사용법</h2>
          <ol className={styles.stepList}>
            <li className={styles.step}>
              <span className={styles.stepNum}>1</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>앱 접속</p>
                <p className={styles.stepNote}>브라우저에서 http://localhost:5173 접속 후 왼쪽 사이드바에서 <strong>🏪 챗봇</strong> 선택</p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>2</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>질문 입력</p>
                <p className={styles.stepNote}>하단 입력창에 질문 입력 후 <strong>Enter</strong> 또는 <strong>전송</strong> 버튼 클릭</p>
              </div>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>3</span>
              <div className={styles.stepBody}>
                <p className={styles.stepLabel}>답변 확인</p>
                <p className={styles.stepNote}>2~3초 후 AI 답변이 생성됩니다. 대화 이력이 유지되어 연속 질문이 가능합니다.</p>
              </div>
            </li>
          </ol>
        </div>

        {/* 환경 변수 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>🔑 환경 변수 설정</h2>
          <div className={styles.card}>
            <p className={styles.cardTitle}>프로젝트 루트에 <span className={styles.inlineCode}>.env</span> 파일 생성</p>
            <div className={styles.codeBlock}>OPENAI_API_KEY=sk-...{'\n'}GOOGLE_API_KEY=AIza...</div>
          </div>
          <ul style={{ paddingLeft: '20px', color: '#4b5563', fontSize: '14px', lineHeight: '1.8' }}>
            <li><strong>OPENAI_API_KEY</strong>: 텍스트 임베딩용 (ChromaDB 벡터 검색)</li>
            <li><strong>GOOGLE_API_KEY</strong>: Gemini 2.5 Flash LLM용</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
