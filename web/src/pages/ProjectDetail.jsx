import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import TaskList from '../components/TaskList'

const API_URL = 'http://localhost:5555'

export default function ProjectDetail() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadProject()
    const interval = setInterval(loadProject, 30000)
    return () => clearInterval(interval)
  }, [projectId])

  async function loadProject() {
    try {
      const response = await fetch(`${API_URL}/api/projects/${projectId}`)
      if (!response.ok) throw new Error('Project not found')
      const projectData = await response.json()
      setData(projectData)
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
      await loadProject()
    } catch (err) {
      alert('Error completing task: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading project...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">Error: {error}</div>
        <button onClick={() => navigate('/projects')}>← Back to Projects</button>
      </div>
    )
  }

  const { project, tasks, notes } = data
  const activeTasks = tasks.filter(t => !t.completed)
  const completedTasks = tasks.filter(t => t.completed)

  return (
    <div className="container">
      <div className="header">
        <div className="header-with-back">
          <button className="back-button" onClick={() => navigate('/projects')}>
            ← Back
          </button>
          <div>
            <h1>📁 {project.name}</h1>
            {project.description && <p>{project.description}</p>}
          </div>
        </div>
      </div>

      <div className="project-detail-content">
        <div className="project-column">
          <h2 className="column-title">✅ Tasks</h2>
          
          {activeTasks.length > 0 && (
            <div className="task-list">
              {activeTasks.map(task => (
                <div key={task.id} className="task-item">
                  <input
                    type="checkbox"
                    className="task-checkbox"
                    onChange={() => handleCompleteTask(task.id)}
                  />
                  <div className="task-details">
                    <div className="task-text">{task.text}</div>
                    <div className="task-meta">
                      {task.due_date && (
                        <span className="task-due">Due {task.due_date}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {completedTasks.length > 0 && (
            <details className="completed-tasks">
              <summary>✓ {completedTasks.length} completed</summary>
              <div className="task-list">
                {completedTasks.map(task => (
                  <div key={task.id} className="task-item completed">
                    <input type="checkbox" checked disabled className="task-checkbox" />
                    <div className="task-details">
                      <div className="task-text">{task.text}</div>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          )}

          {tasks.length === 0 && (
            <div className="empty-state">No tasks in this project</div>
          )}
        </div>

        <div className="project-column">
          <h2 className="column-title">📝 Notes</h2>
          
          {notes.length > 0 ? (
            <div className="notes-list">
              {notes.map((note, idx) => (
                <div key={idx} className="note-item">
                  <div className="note-header">
                    <div className="note-date">{note.date} {note.timestamp}</div>
                  </div>
                  <div className="note-content">{note.content}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No notes in this project yet</div>
          )}
        </div>
      </div>

      <div className="stats-bar">
        <div className="stat-item">
          <div className="stat-value">{activeTasks.length}</div>
          <div className="stat-label">Active Tasks</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{completedTasks.length}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{notes.length}</div>
          <div className="stat-label">Notes</div>
        </div>
      </div>
    </div>
  )
}

