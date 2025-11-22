import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = 'http://localhost:5555'

export default function WriteNote() {
  const [content, setContent] = useState('')
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const contentRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadProjects()
    // Auto-focus content textarea
    contentRef.current?.focus()
  }, [])

  async function loadProjects() {
    try {
      const response = await fetch(`${API_URL}/api/projects`)
      if (response.ok) {
        const data = await response.json()
        setProjects(data.projects)
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  async function handleSave() {
    if (!content.trim()) {
      setStatus('Please enter some content')
      return
    }

    setSaving(true)
    setStatus('Saving...')

    try {
      const response = await fetch(`${API_URL}/api/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: content.trim(),
          project_id: selectedProject || null
        })
      })

      if (!response.ok) throw new Error('Failed to save note')

      setStatus('✓ Note saved!')
      
      // Clear form after brief delay
      setTimeout(() => {
        setContent('')
        setSelectedProject('')
        setStatus('')
        contentRef.current?.focus()
      }, 1000)
    } catch (err) {
      setStatus('Error: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  function handleKeyDown(e) {
    // Cmd/Ctrl + S to save
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    }
    // Cmd/Ctrl + P to toggle preview
    if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
      e.preventDefault()
      setShowPreview(!showPreview)
    }
  }

  return (
    <div className="container" onKeyDown={handleKeyDown}>
      <div className="header">
        <div className="header-title-row">
          <div>
            <h1>📝 Write Note</h1>
            <p>Create a new markdown note</p>
          </div>
          <button 
            className="toggle-preview-btn"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? '📝 Hide Preview' : '👁️ Show Preview'}
          </button>
        </div>
      </div>

      <div className="content">
        <div className={`write-note-content ${showPreview ? 'with-preview' : 'no-preview'}`}>
        <div className="editor-section">
          <div className="form-group">
            <label htmlFor="content">Markdown Note</label>
            <textarea
              ref={contentRef}
              id="content"
              className="content-textarea"
              placeholder="Write your note here using markdown...

Examples:
# Heading 1
## Heading 2

**bold text**
*italic text*

- List item 1
- List item 2

> Quote

`code`"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>

          {projects.length > 0 && (
            <div className="form-group">
              <label htmlFor="project">Project (optional)</label>
              <select
                id="project"
                className="project-select"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
              >
                <option value="">No project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="actions">
            <div className={`status ${status.startsWith('✓') ? 'success' : status.startsWith('Error') ? 'error' : ''}`}>
              {status || '💡 Tip: Cmd/Ctrl+S to save • Cmd/Ctrl+P to toggle preview'}
            </div>
            <button
              className="btn-save"
              onClick={handleSave}
              disabled={saving || !content.trim()}
            >
              {saving ? 'Saving...' : 'Save Note'}
            </button>
          </div>
        </div>

        {showPreview && (
          <div className="preview-section">
            <label>Preview</label>
            <div className="preview">
              {content ? (
                <div dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
              ) : (
                <p className="preview-placeholder">Preview will appear here...</p>
              )}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  )
}

function renderMarkdown(text) {
  // Simple markdown rendering
  let html = text
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Code
    .replace(/`(.+?)`/g, '<code>$1</code>')
    // Line breaks
    .replace(/\n/g, '<br>')

  return html
}

