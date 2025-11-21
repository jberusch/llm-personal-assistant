import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = 'http://localhost:5555'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadProjects()
  }, [])

  async function loadProjects() {
    try {
      const response = await fetch(`${API_URL}/api/projects`)
      if (!response.ok) throw new Error('Failed to load projects')
      const data = await response.json()
      setProjects(data.projects)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading projects...</div>
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

  if (projects.length === 0) {
    return (
      <div className="container">
        <div className="header">
          <h1>📁 Projects</h1>
        </div>
        <div className="content">
          <div className="empty-state">
            No projects yet. Projects will be created when you assign tasks or notes to them.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <h1>📁 Projects</h1>
        <p>Select a project to view details</p>
      </div>

      <div className="content">
        <div className="projects-grid">
          {projects.map(project => (
            <div
              key={project.id}
              className="project-card"
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              <div className="project-header">
                <h3>{project.name}</h3>
              </div>
              
              {project.description && (
                <p className="project-description">{project.description}</p>
              )}
              
              <div className="project-stats">
                {project.task_count > 0 && (
                  <span className="stat">✅ {project.task_count} tasks</span>
                )}
                {project.note_count > 0 && (
                  <span className="stat">📝 {project.note_count} notes</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

