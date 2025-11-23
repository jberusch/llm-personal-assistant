import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Lists() {
  const navigate = useNavigate()
  const [lists, setLists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [newListDescription, setNewListDescription] = useState('')
  const [newListCategory, setNewListCategory] = useState('general')
  const [creating, setCreating] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5555'

  const fetchLists = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setLists(data.lists || [])
    } catch (e) {
      setError(e.message)
      console.error('Error fetching lists:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLists()
  }, [])

  const handleCreateList = async (e) => {
    e.preventDefault()
    if (!newListName.trim()) return

    setCreating(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newListName,
          description: newListDescription,
          category: newListCategory
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create list')
      }

      // Refresh lists
      await fetchLists()
      
      // Reset form
      setNewListName('')
      setNewListDescription('')
      setNewListCategory('general')
      setShowCreateForm(false)
    } catch (error) {
      alert(`Error creating list: ${error.message}`)
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading lists...</div>
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

  return (
    <div className="container">
      <div className="header">
        <div className="header-with-actions">
          <div>
            <h1>📋 Lists</h1>
            <p>Your persistent collections</p>
          </div>
          <button 
            className="button primary-button"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? '✕ Cancel' : '+ New List'}
          </button>
        </div>
      </div>

      {showCreateForm && (
        <div className="content" style={{ marginBottom: '2rem' }}>
          <form onSubmit={handleCreateList} className="create-list-form">
            <div className="form-group">
              <label htmlFor="listName">List Name *</label>
              <input
                id="listName"
                type="text"
                placeholder="e.g., Places in SF, Book Recommendations"
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                required
                autoFocus
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="listDescription">Description</label>
              <input
                id="listDescription"
                type="text"
                placeholder="Optional description"
                value={newListDescription}
                onChange={(e) => setNewListDescription(e.target.value)}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="listCategory">Category</label>
              <select
                id="listCategory"
                value={newListCategory}
                onChange={(e) => setNewListCategory(e.target.value)}
              >
                <option value="general">General</option>
                <option value="places">Places</option>
                <option value="books">Books</option>
                <option value="movies">Movies</option>
                <option value="restaurants">Restaurants</option>
                <option value="music">Music</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <button 
              type="submit" 
              className="button primary-button"
              disabled={creating || !newListName.trim()}
            >
              {creating ? 'Creating...' : 'Create List'}
            </button>
          </form>
        </div>
      )}

      <div className="content">
        {lists.length === 0 ? (
          <div className="empty-state">
            <p>No lists yet.</p>
            <p className="tip">Create your first list to start organizing!</p>
          </div>
        ) : (
          <div className="lists-grid">
            {lists.map((list) => (
              <div 
                key={list.id} 
                className="list-card"
                onClick={() => navigate(`/lists/${list.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="list-card-header">
                  <h3>{list.name}</h3>
                  <span className="list-category">{list.category}</span>
                </div>
                {list.description && (
                  <p className="list-description">{list.description}</p>
                )}
                <div className="list-meta">
                  <span className="item-count">{list.item_count} item{list.item_count !== 1 ? 's' : ''}</span>
                  <span className="list-date">
                    Created {new Date(list.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Lists

