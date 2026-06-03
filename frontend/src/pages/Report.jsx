import { useState } from 'react'
import styles from './Page.module.css'
import rStyles from './Report.module.css'

const REGIONS = [
  '전체', '서울', '경기', '부산', '대구', '인천', '광주',
  '대전', '울산', '세종', '강원', '충북', '충남',
  '전북', '전남', '경북', '경남', '제주',
]

const CATEGORIES = [
  '전체', '카페', '음식점', '자전거', '미용', '의류', '고기',
]

export default function Report() {
  const [region,      setRegion]      = useState('전체')
  const [category,    setCategory]    = useState('전체')
  const [digitalOnly, setDigitalOnly] = useState(false)
  const [paperOnly,   setPaperOnly]   = useState(false)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')

  async function handleDownload() {
    setLoading(true)
    setError('')

    const params = new URLSearchParams({
      region:       region      === '전체' ? '' : region,
      category:     category    === '전체' ? '' : category,
      digital_only: digitalOnly,
      paper_only:   paperOnly,
    })

    try {
      const res = await fetch(`/api/report?${params}`)
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `서버 오류 (${res.status})`)
      }

      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `onnuri_${region}_${category}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const hasFilter = region !== '전체' || category !== '전체' || digitalOnly || paperOnly

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <h1 className={styles.pageTitle}>📄 보고서 생성</h1>
        <p className={styles.pageSubtitle}>조건을 선택하면 가맹점 목록과 차트가 포함된 PDF를 생성합니다.</p>

        <div className={rStyles.card}>
          {/* 지역 */}
          <div className={rStyles.fieldGroup}>
            <label className={rStyles.label}>📍 지역</label>
            <div className={rStyles.chipGrid}>
              {REGIONS.map(r => (
                <button
                  key={r}
                  className={`${rStyles.chip} ${region === r ? rStyles.chipActive : ''}`}
                  onClick={() => setRegion(r)}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className={rStyles.divider} />

          {/* 업종 */}
          <div className={rStyles.fieldGroup}>
            <label className={rStyles.label}>🛒 업종</label>
            <div className={rStyles.chipGrid}>
              {CATEGORIES.map(c => (
                <button
                  key={c}
                  className={`${rStyles.chip} ${category === c ? rStyles.chipActive : ''}`}
                  onClick={() => setCategory(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className={rStyles.divider} />

          {/* 가맹 유형 */}
          <div className={rStyles.fieldGroup}>
            <label className={rStyles.label}>💳 가맹 유형</label>
            <div className={rStyles.toggleRow}>
              <label className={`${rStyles.toggle} ${digitalOnly ? rStyles.toggleActive : ''}`}>
                <input
                  type="checkbox"
                  checked={digitalOnly}
                  onChange={e => {
                    setDigitalOnly(e.target.checked)
                    if (e.target.checked) setPaperOnly(false)
                  }}
                />
                디지털 가맹점만
              </label>
              <label className={`${rStyles.toggle} ${paperOnly ? rStyles.toggleActive : ''}`}>
                <input
                  type="checkbox"
                  checked={paperOnly}
                  onChange={e => {
                    setPaperOnly(e.target.checked)
                    if (e.target.checked) setDigitalOnly(false)
                  }}
                />
                지류 가맹점만
              </label>
            </div>
          </div>
        </div>

        {/* 선택 요약 */}
        <div className={rStyles.summary}>
          <span className={rStyles.summaryLabel}>선택 조건</span>
          <div className={rStyles.summaryTags}>
            <span className={rStyles.tag}>지역: {region}</span>
            <span className={rStyles.tag}>업종: {category}</span>
            {digitalOnly && <span className={`${rStyles.tag} ${rStyles.tagBlue}`}>디지털 가맹점만</span>}
            {paperOnly   && <span className={`${rStyles.tag} ${rStyles.tagPurple}`}>지류 가맹점만</span>}
          </div>
        </div>

        {/* 오류 메시지 */}
        {error && (
          <div className={rStyles.errorBox}>
            ⚠️ {error}
          </div>
        )}

        {/* 다운로드 버튼 */}
        <button
          className={rStyles.downloadBtn}
          onClick={handleDownload}
          disabled={loading}
        >
          {loading
            ? <><span className={rStyles.spinner} /> PDF 생성 중...</>
            : '⬇ PDF 보고서 다운로드'}
        </button>

        {/* PDF 포함 내용 안내 */}
        <div className={rStyles.infoBox}>
          <p className={rStyles.infoTitle}>📋 PDF 포함 내용</p>
          <ul className={rStyles.infoList}>
            <li>적용 필터 요약</li>
            <li>총 가맹점 수 · 디지털 / 지류 비율 통계</li>
            <li>업종별 가맹점 수 막대 차트</li>
            <li>가맹 유형 분포 파이 차트</li>
            <li>가맹점 목록 테이블 (최대 200개)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
