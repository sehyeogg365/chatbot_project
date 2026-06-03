import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  { id: 'manual',       icon: '📖', label: '사용자 매뉴얼' },
  { id: 'guide',        icon: '💡', label: '질문 유형 가이드' },
  { id: 'architecture', icon: '🔄', label: 'DataFlow / 아키텍처' },
  { id: 'insights',     icon: '📊', label: '데이터 인사이트' },
  { id: 'report',       icon: '📄', label: '보고서' },
  { id: 'chat',         icon: '🏪', label: '챗봇' },
]

export default function Sidebar({ current, onNavigate }) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <p className={styles.brandTitle}>온누리상품권</p>
        <p className={styles.brandSub}>가맹점 안내 챗봇</p>
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map(({ id, icon, label }) => (
          <button
            key={id}
            className={`${styles.navItem} ${current === id ? styles.active : ''}`}
            onClick={() => onNavigate(id)}
          >
            <span className={styles.icon}>{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
