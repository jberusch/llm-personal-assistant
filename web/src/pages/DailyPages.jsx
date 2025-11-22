import { useState, useEffect, useRef } from 'react'

const API_URL = 'http://localhost:5555'
const MIN_WORD_COUNT = 750

export default function DailyPages() {
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState('')
  const [skipReason, setSkipReason] = useState('')
  const [showSkipDialog, setShowSkipDialog] = useState(false)
  const contentRef = useRef(null)

  useEffect(() => {
    loadExistingPages()
    contentRef.current?.focus()
  }, [])

  async function loadExistingPages() {
    try {
      const response = await fetch(`${API_URL}/api/daily-pages`)
      if (response.ok) {
        const data = await response.json()
        if (data.content) {
          setContent(data.content)
        }
      }
    } catch (err) {
      console.error('Failed to load daily pages:', err)
    }
  }

  async function handleSave() {
    if (!content.trim()) {
      setStatus('Please write something first')
      return
    }

    const wordCount = countWords(content)
    if (wordCount < MIN_WORD_COUNT) {
      setStatus(`Need ${MIN_WORD_COUNT - wordCount} more words to save`)
      return
    }

    setSaving(true)
    setStatus('Saving...')

    try {
      const response = await fetch(`${API_URL}/api/daily-pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content.trim() })
      })

      if (!response.ok) throw new Error('Failed to save daily pages')

      setStatus('✓ Daily pages saved!')
      
      setTimeout(() => {
        setStatus('')
      }, 2000)
    } catch (err) {
      setStatus('Error: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleSkip() {
    if (!skipReason.trim()) {
      alert('Please provide a reason for skipping')
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/daily-pages/skip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reason: skipReason.trim(),
          word_count: countWords(content)
        })
      })

      if (!response.ok) throw new Error('Failed to log skip')

      alert('Skip logged. You can close this window.')
      setShowSkipDialog(false)
    } catch (err) {
      alert('Error logging skip: ' + err.message)
    }
  }

  function handleKeyDown(e) {
    // Cmd/Ctrl + S to save
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    }
  }

  function countWords(text) {
    if (!text || !text.trim()) return 0
    return text.trim().split(/\s+/).length
  }

  const wordCount = countWords(content)
  const progress = Math.min((wordCount / MIN_WORD_COUNT) * 100, 100)
  const canSave = wordCount >= MIN_WORD_COUNT

  return (
    <div className="container" onKeyDown={handleKeyDown}>
      <div className="header">
        <div className="header-title-row">
          <div>
            <h1>📝 Daily Pages</h1>
            <p>Write at least {MIN_WORD_COUNT} words to start your day</p>
          </div>
        </div>
      </div>

      <div className="content daily-pages-content">
        <div className="word-count-bar">
          <div className="word-count-progress" style={{ width: `${progress}%` }}>
          </div>
          <div className="word-count-text">
            <span className={canSave ? 'text-success' : ''}>
              {wordCount} / {MIN_WORD_COUNT} words
            </span>
            {canSave && <span className="text-success"> ✓ Ready to save!</span>}
          </div>
        </div>

        <textarea
          ref={contentRef}
          className="daily-pages-textarea"
          placeholder="Start writing your daily pages...

This is your space for stream-of-consciousness writing. No one will judge. Just write whatever comes to mind.

The goal is to get {MIN_WORD_COUNT} words down to clear your mind and start the day fresh."
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />

        <div className="daily-pages-actions">
          <div className="status-area">
            {status && (
              <div className={`status ${status.startsWith('✓') ? 'success' : status.startsWith('Error') ? 'error' : ''}`}>
                {status}
              </div>
            )}
            {!status && (
              <div className="status-tip">
                💡 Tip: Press Cmd/Ctrl+S to save
              </div>
            )}
          </div>

          <div className="button-group">
            <button
              className="btn-secondary"
              onClick={() => setShowSkipDialog(true)}
            >
              Skip Today
            </button>
            <button
              className="btn-save"
              onClick={handleSave}
              disabled={saving || !canSave}
            >
              {saving ? 'Saving...' : canSave ? 'Save Daily Pages' : `Need ${MIN_WORD_COUNT - wordCount} more words`}
            </button>
          </div>
        </div>
      </div>

      {showSkipDialog && (
        <div className="modal-overlay" onClick={() => setShowSkipDialog(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Skip Daily Pages</h3>
            <p>Why are you skipping today?</p>
            <textarea
              className="skip-reason-input"
              placeholder="Enter your reason..."
              value={skipReason}
              onChange={(e) => setSkipReason(e.target.value)}
              rows={3}
            />
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowSkipDialog(false)}
              >
                Cancel
              </button>
              <button
                className="btn-save"
                onClick={handleSkip}
                disabled={!skipReason.trim()}
              >
                Log Skip
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

