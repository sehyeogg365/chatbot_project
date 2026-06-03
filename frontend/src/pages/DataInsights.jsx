import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import styles from './Page.module.css'

// ── 원본 데이터 ──────────────────────────────────────────────────
const AREA_DATA = [
  { region: '서울', count: 24187 },
  { region: '경기', count: 22089 },
  { region: '광주', count: 14396 },
  { region: '부산', count: 12283 },
  { region: '대구', count: 10052 },
  { region: '경남', count: 9424 },
  { region: '경북', count: 8742 },
  { region: '전남', count: 5937 },
  { region: '강원', count: 5916 },
  { region: '전북', count: 6178 },
  { region: '인천', count: 6675 },
  { region: '충남', count: 6067 },
  { region: '충북', count: 4582 },
  { region: '울산', count: 4014 },
  { region: '대전', count: 5404 },
  { region: '제주', count: 2806 },
  { region: '세종', count: 1749 },
].sort((a, b) => b.count - a.count)

const YEARS = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']

const SALES_RAW = {
  서울: [1968.9, 2500.6, 2064.6, 2884.2, 3327.9, 7183.3, 5058.3, 3903.4, 4536.2, 5201.1],
  부산: [1022.8, 1260.6, 1658.8, 2117.5, 2592.8, 5910.1, 4506.9, 3928.8, 3763.3, 5262],
  대구: [678.5, 897.9, 1166.4, 1578.5, 1842.8, 5684.2, 3606.4, 2868.3, 2856.8, 3584],
  인천: [286, 439.1, 438.7, 634.9, 639.7, 1582.1, 1164.6, 750.8, 721.1, 921.3],
  광주: [267.1, 375.3, 467.2, 681.3, 716.9, 1368.5, 904.3, 728, 677.4, 1146.6],
  대전: [255.5, 271.8, 299.1, 379.7, 447.4, 895, 801.9, 606.7, 661.8, 885.9],
  울산: [349.4, 765.6, 460.9, 730.5, 679.7, 1454.7, 1270.1, 1184.8, 919.3, 903.3],
  세종: [34.5, 32.6, 33.7, 50.2, 63.5, 159, 129.4, 89.7, 71.1, 88.3],
  경기: [1013.6, 1286.6, 1030.1, 1582.5, 1583.9, 3321.6, 2615.1, 1710.6, 1517.8, 2023],
  강원: [211.6, 241.5, 235.8, 153.2, 189.3, 510.9, 379.7, 252.9, 237.2, 275.3],
  충북: [130.7, 132.5, 126.2, 192.8, 240.3, 475.6, 435.6, 291.6, 289.6, 370.8],
  충남: [179.4, 179.1, 173.3, 272, 334.3, 624.9, 506.5, 340, 330.9, 397],
  전북: [478.8, 555.1, 606.5, 729.2, 813.4, 1611.6, 1185.2, 881.1, 802.1, 1001.7],
  전남: [336, 399.1, 393.9, 574.5, 585.4, 1334.7, 1112, 886.6, 720.3, 855.4],
  경북: [520.4, 701, 598, 937.4, 1017.5, 3080.4, 1985.4, 1433, 1509.8, 1900],
  경남: [509, 609.6, 807.6, 1155.2, 1356.2, 2831.1, 2032.3, 1469.8, 1420.3, 1705.2],
  제주: [73.7, 83.2, 88.1, 124.1, 141.4, 410.8, 218.6, 133.4, 149.5, 211.6],
}

const RECOVERY_RAW = {
  서울: [1460.6, 2131.7, 2257.8, 2889.8, 3449, 6806.3, 7281.2, 6194.1, 7288.1, 9361.5],
  부산: [1147, 1647.9, 1916.3, 2454.1, 2909.2, 5808, 5606.2, 4010.3, 5038.3, 5475.8],
  대구: [844.8, 1246.4, 1520.2, 2013.8, 2332.8, 6066.5, 5812.6, 4460.2, 5536.2, 8124.6],
  인천: [344.7, 498.6, 491.3, 606.9, 632.8, 1352.6, 1143, 752.4, 896.8, 1107.9],
  광주: [309.7, 444.5, 569.6, 800.3, 857, 1331.2, 1282.3, 835.1, 963.1, 1308.1],
  대전: [209.5, 256.4, 240, 325.3, 378.8, 763.2, 846.8, 632.4, 1008.6, 1332.9],
  울산: [286.1, 463.6, 386.4, 576.1, 544.5, 976.9, 1077.2, 830.9, 949.6, 1108.7],
  세종: [37.8, 16.6, 14.6, 19.3, 23.5, 75.9, 75, 55.8, 78, 127.7],
  경기: [758.3, 1056, 885.9, 1134.8, 1169.1, 2087.1, 2218, 1566.3, 2018, 3473.5],
  강원: [145.3, 172.3, 161.8, 174.8, 211.9, 485.2, 510.2, 389.4, 409.8, 488.2],
  충북: [160.7, 161.7, 146.1, 187, 216.9, 393.9, 451.9, 307.5, 388.8, 498.1],
  충남: [184.5, 270.5, 227.6, 294.4, 300.5, 587.8, 559.4, 340.8, 430.3, 619.3],
  전북: [460.7, 610.6, 615.5, 749.6, 800.3, 1407.2, 1286.2, 853.1, 972.5, 1163.5],
  전남: [320.4, 430.5, 392.5, 529.3, 565.9, 1142.9, 1212.5, 792.2, 882.3, 998.3],
  경북: [429.8, 646.5, 479.3, 689.8, 727.9, 2056.4, 1779.9, 1219.9, 1552.4, 1854.4],
  경남: [441.4, 550.7, 630.6, 956.8, 1124.6, 2126.4, 2053.6, 1585.8, 1843.8, 2262.3],
  제주: [79.7, 100.6, 102.2, 130, 148.3, 377.8, 297.5, 164.1, 233.9, 287.7],
}

// ── 파생 데이터 ──────────────────────────────────────────────────
const sum = (arr) => arr.reduce((a, b) => a + b, 0)

const TREND_DATA = YEARS.map((year, i) => ({
  year,
  판매: Math.round(Object.values(SALES_RAW).reduce((s, v) => s + v[i], 0)),
  회수: Math.round(Object.values(RECOVERY_RAW).reduce((s, v) => s + v[i], 0)),
}))

const SALE_2024 = Object.entries(SALES_RAW)
  .map(([region, vals]) => ({ region, amount: vals[9] }))
  .sort((a, b) => b.amount - a.amount)
  .slice(0, 10)

const TOTAL_STORES = AREA_DATA.reduce((s, d) => s + d.count, 0)
const TOTAL_SALE_2024 = Math.round(Object.values(SALES_RAW).reduce((s, v) => s + v[9], 0))
const TOTAL_RECV_2024 = Math.round(Object.values(RECOVERY_RAW).reduce((s, v) => s + v[9], 0))

// ── 포매터 ───────────────────────────────────────────────────────
const fmtAmt = (v) => `${v.toLocaleString()}억원`
const fmtCount = (v) => `${v.toLocaleString()}개`

export default function DataInsights() {
  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <h1 className={styles.pageTitle}>📊 데이터 인사이트</h1>
        <p className={styles.pageSubtitle}>온누리상품권 가맹점 현황 및 판매·회수 통계 대시보드</p>

        {/* 요약 카드 */}
        <div className={styles.section}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '8px' }}>
            <StatCard label="전체 가맹점 수" value={fmtCount(TOTAL_STORES)} sub="전국 17개 시도" color="#2563eb" />
            <StatCard label="2024년 전국 판매금액" value={fmtAmt(TOTAL_SALE_2024)} sub="전년 대비 증가" color="#16a34a" />
            <StatCard label="2024년 전국 회수금액" value={fmtAmt(TOTAL_RECV_2024)} sub="판매 대비 회수율" color="#9333ea" />
          </div>
        </div>

        {/* 지역별 가맹점 수 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>지역별 가맹점 수</h2>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={AREA_DATA} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => v.toLocaleString()} tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="region" width={40} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [`${v.toLocaleString()}개`, '가맹점 수']} />
              <Bar dataKey="count" name="가맹점 수" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 연도별 판매·회수 추이 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>연도별 전국 판매·회수금액 추이 (억원)</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={TREND_DATA} margin={{ left: 8, right: 20, top: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${(v / 10000).toFixed(1)}조`} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [`${v.toLocaleString()}억원`]} />
              <Legend />
              <Line type="monotone" dataKey="판매" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="회수" stroke="#9333ea" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 2024년 지역별 판매금액 Top 10 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>2024년 지역별 판매금액 Top 10 (억원)</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={SALE_2024} margin={{ left: 8, right: 20, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => v.toLocaleString()} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [`${v.toLocaleString()}억원`, '판매금액']} />
              <Bar dataKey="amount" name="판매금액" fill="#16a34a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: '#fff',
      border: '1px solid #e5e7eb',
      borderRadius: '12px',
      padding: '20px',
      borderTop: `3px solid ${color}`,
    }}>
      <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 8px' }}>{label}</p>
      <p style={{ fontSize: '22px', fontWeight: '700', color: '#111827', margin: '0 0 4px' }}>{value}</p>
      <p style={{ fontSize: '12px', color: '#9ca3af', margin: 0 }}>{sub}</p>
    </div>
  )
}
