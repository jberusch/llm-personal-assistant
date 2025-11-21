import { useState, useEffect } from 'react'
import TaskList from '../components/TaskList'

const API_URL = 'http://localhost:5555'

export default function Tasks() {
  const [tasks, setTasks] = useState({ today: [], upcoming: [], inbox: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  async function loadTasks() {
    try {
      const response = await fetch(`${API_URL}/api/tasks`)
      if (!response.ok) throw new Error('Failed to load tasks')
      const data = await response.json()
      setTasks(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCompleteTask(taskId) {
    try {
      const response = await fetch(`${API_URL}/api/tasks/${taskId}/complete`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Failed to complete task')
      await loadTasks() // Reload tasks
    } catch (err) {
      alert('Error completing task: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading tasks...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">Error: {error}</div>
      </div>
    )
  }

  const totalTasks = tasks.today.length + tasks.upcoming.length + tasks.inbox.length

  return (
    <div className="container">
      <div className="header">
        <h1>✅ Tasks</h1>
        <p>Check boxes to mark tasks as complete</p>
      </div>

      <div className="content">
        <TaskList
          title="📌 TODAY"
          tasks={tasks.today}
          onComplete={handleCompleteTask}
          showDueDate
        />
        
        <TaskList
          title="📅 UPCOMING"
          tasks={tasks.upcoming}
          onComplete={handleCompleteTask}
          showDueDate
        />
        
        <TaskList
          title="📥 INBOX"
          tasks={tasks.inbox}
          onComplete={handleCompleteTask}
        />

        <div className="stats">
          Total: {totalTasks} incomplete tasks
        </div>
      </div>
    </div>
  )
}

