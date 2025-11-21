import { useState } from 'react'

export default function TaskList({ title, tasks, onComplete, showDueDate = false }) {
  const [completingIds, setCompletingIds] = useState(new Set())

  async function handleCheckbox(taskId) {
    setCompletingIds(prev => new Set([...prev, taskId]))
    
    try {
      await onComplete(taskId)
    } catch (err) {
      setCompletingIds(prev => {
        const next = new Set(prev)
        next.delete(taskId)
        return next
      })
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="section">
        <div className="section-header">
          <h2>{title}</h2>
          <span className="count-badge">0</span>
        </div>
        <div className="empty-state">No tasks here</div>
      </div>
    )
  }

  return (
    <div className="section">
      <div className="section-header">
        <h2>{title}</h2>
        <span className="count-badge">{tasks.length}</span>
      </div>
      
      <div className="task-list">
        {tasks.map(task => (
          <div
            key={task.id}
            className={`task-item ${completingIds.has(task.id) ? 'completing' : ''}`}
          >
            <input
              type="checkbox"
              className="task-checkbox"
              onChange={() => handleCheckbox(task.id)}
              disabled={completingIds.has(task.id)}
            />
            <span className="task-text">{task.text}</span>
            {showDueDate && task.due_date && (
              <span className="task-due">{task.due_date}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

