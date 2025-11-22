import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Tasks from './pages/Tasks'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import WriteNote from './pages/WriteNote'
import DailyPages from './pages/DailyPages'
import DailyLog from './pages/DailyLog'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/tasks" replace />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:projectId" element={<ProjectDetail />} />
        <Route path="/write" element={<WriteNote />} />
        <Route path="/daily-pages" element={<DailyPages />} />
        <Route path="/log" element={<DailyLog />} />
        <Route path="/log/:date" element={<DailyLog />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
