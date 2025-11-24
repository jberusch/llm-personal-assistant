import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

const API_URL = 'http://localhost:5555'

function buildChatExchanges(chat_history) {
  if (!chat_history || chat_history.length === 0) return []
  
  const exchanges = []
  let current = null
  
  chat_history.forEach((entry = {}) => {
    const role = (entry && entry.metadata && entry.metadata.role) || entry.role || 'user'
    const message = entry.response || entry.message || ''
    if (!message || !message.trim()) {
      return
    }
    
    let timestamp = entry && entry.metadata && entry.metadata.timestamp
    if (!timestamp && entry.timestamp) {
      try {
        const d = new Date(entry.timestamp)
        if (!isNaN(d.getTime())) {
          timestamp = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      } catch {
        timestamp = ''
      }
    }
    
    if (role === 'user') {
      if (current && (current.user || current.assistant)) {
        exchanges.push(current)
      }
      current = { timestamp, user: message, assistant: '' }
    } else {
      if (!current) {
        current = { timestamp, user: '', assistant: message }
      } else if (!current.assistant) {
        current.assistant = message
        if (!current.timestamp) current.timestamp = timestamp
        exchanges.push(current)
        current = null
      } else {
        exchanges.push(current)
        current = { timestamp, user: '', assistant: message }
      }
    }
  })
  
  if (current && (current.user || current.assistant)) {
    exchanges.push(current)
  }
  
  return exchanges
}

export default function DailyLog() {
  const { date } = useParams()
  const [logData, setLogData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadLog()
    const interval = setInterval(loadLog, 30000)
    return () => clearInterval(interval)
  }, [date])

  async function loadLog() {
    try {
      const endpoint = date ? `/api/log/${date}` : '/api/log'
      const response = await fetch(`${API_URL}${endpoint}`)
      if (!response.ok) throw new Error('Failed to load log')
      const data = await response.json()
      setLogData(data)
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
      await loadLog()
    } catch (err) {
      alert('Error completing task: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading daily log...</div>
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

  const { intention, daily_pages, notes, tasks, morning, chat_history } = logData
  const dateObj = new Date(logData.date)
  const formattedDate = dateObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  const chatExchanges = buildChatExchanges(chat_history || [])

  return (
    <div className="container">
      <div className="header">
        <h1>📅 {formattedDate}</h1>
        <p>Your daily log</p>
      </div>

      <div className="content daily-log-content">
        {/* Intention Section */}
        {intention && (
          <div className="log-section">
            <h2 className="log-section-title">🎯 Today's Intention</h2>
            <div className="intention-card">
              {intention.intention && (
                <div className="intention-item">
                  <strong>Intention:</strong> {intention.intention}
                </div>
              )}
              {intention.priorities && (
                <div className="intention-item">
                  <strong>Key Priorities:</strong> {intention.priorities}
                </div>
              )}
              {intention.joy && (
                <div className="intention-item">
                  <strong>Bring Joy:</strong> {intention.joy}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Daily Pages Section */}
        {daily_pages && (
          <div className="log-section">
            <h2 className="log-section-title">📝 Daily Pages</h2>
            <div className="daily-pages-display">
              {daily_pages.split('\n').map((paragraph, idx) => (
                <p key={idx}>{paragraph}</p>
              ))}
              <div className="word-count-display">
                {daily_pages.split(/\s+/).length} words
              </div>
            </div>
          </div>
        )}

        {/* Tasks Section */}
        {(tasks.today.length > 0 || tasks.completed.length > 0) && (
          <div className="log-section">
            <h2 className="log-section-title">✅ Tasks</h2>
            
            {tasks.today.length > 0 && (
              <div className="task-group">
                <h3>Active</h3>
                <div className="task-list">
                  {tasks.today.map(task => (
                    <div key={task.id} className="task-item">
                      <input
                        type="checkbox"
                        className="task-checkbox"
                        onChange={() => handleCompleteTask(task.id)}
                      />
                      <span className="task-text">{task.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {tasks.completed.length > 0 && (
              <div className="task-group">
                <h3>Completed</h3>
                <div className="task-list">
                  {tasks.completed.map(task => (
                    <div key={task.id} className="task-item completed">
                      <input type="checkbox" checked disabled className="task-checkbox" />
                      <span className="task-text">{task.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Notes Section */}
        {notes && notes.length > 0 && (
          <div className="log-section">
            <h2 className="log-section-title">📝 Notes</h2>
            <div className="notes-list">
              {notes.map((note, idx) => (
                <div key={idx} className="note-item">
                  <div className="note-timestamp">{note.timestamp}</div>
                  <div className="note-content">{note.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Morning Reflection */}
        {morning && morning.metadata && morning.metadata.responses && (
          <div className="log-section">
            <h2 className="log-section-title">🌅 Morning Reflection</h2>
            <div className="reflection-list">
              {Object.entries(morning.metadata.responses).map(([question, answer], idx) => (
                <div key={idx} className="reflection-item">
                  <div className="reflection-question">{question}</div>
                  <div className="reflection-answer">{answer}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chat History */}
        {chatExchanges.length > 0 && (
          <div className="log-section">
            <h2 className="log-section-title">💬 Conversations</h2>
            <div className="chat-history">
              {chatExchanges.map((entry, idx) => (
                <div key={idx} className="chat-entry">
                  {entry.timestamp && (
                    <div className="chat-timestamp">{entry.timestamp}</div>
                  )}
                  {entry.user && (
                    <div className="chat-message user-message">
                      <strong>You:</strong> {entry.user}
                    </div>
                  )}
                  {entry.assistant && (
                    <div className="chat-message assistant-message">
                      <strong>Assistant:</strong> {entry.assistant}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!intention && !daily_pages && tasks.today.length === 0 && tasks.completed.length === 0 && (!notes || notes.length === 0) && !morning && chatExchanges.length === 0 && (
          <div className="empty-state">
            <p>Nothing recorded for this day yet.</p>
            <p>Start your morning flow to begin!</p>
          </div>
        )}
      </div>
    </div>
  )
}

