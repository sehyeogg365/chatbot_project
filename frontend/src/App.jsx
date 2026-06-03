import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import Manual from './pages/Manual'
import QuestionGuide from './pages/QuestionGuide'
import Architecture from './pages/Architecture'
import DataInsights from './pages/DataInsights'
import Report from './pages/Report'
import styles from './App.module.css'

const PAGES = {
  manual:       Manual,
  guide:        QuestionGuide,
  architecture: Architecture,
  insights:     DataInsights,
  report:       Report,
  chat:         Chat,
}

export default function App() {
  const [page, setPage] = useState('chat')
  const Page = PAGES[page]

  return (
    <div className={styles.appLayout}>
      <Sidebar current={page} onNavigate={setPage} />
      <main className={styles.main}>
        <Page />
      </main>
    </div>
  )
}
