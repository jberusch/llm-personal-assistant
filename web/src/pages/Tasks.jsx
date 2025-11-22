import { useState, useEffect } from 'react'
import TaskList from '../components/TaskList'

const API_URL = 'http://localhost:5555'

export default function Tasks() {
  const [tasks, setTasks] = useState({ today: [], upcoming: [], inbox: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newTaskText, setNewTaskText] = useState('')
  const [addingTask, setAddingTask] = useState(false)

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

  async function handleAddTask(e) {
    e.preventDefault()
    
    if (!newTaskText.trim()) return
    
    setAddingTask(true)
    
    try {
      const response = await fetch(`${API_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: newTaskText.trim()
        })
      })
      
      if (!response.ok) throw new Error('Failed to add task')
      
      setNewTaskText('')
      await loadTasks()
    } catch (err) {
      alert('Error adding task: ' + err.message)
    } finally {
      setAddingTask(false)
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
        <form onSubmit={handleAddTask} className="add-task-form">
          <input
            type="text"
            className="add-task-input"
            placeholder="Add a new task..."
            value={newTaskText}
            onChange={(e) => setNewTaskText(e.target.value)}
            disabled={addingTask}
          />
          <button
            type="submit"
            className="add-task-button"
            disabled={addingTask || !newTaskText.trim()}
          >
            {addingTask ? 'Adding...' : 'Add Task'}
          </button>
        </form>
        
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

