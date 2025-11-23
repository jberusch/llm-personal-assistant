import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

function ListDetail() {
  const { listId } = useParams()
  const navigate = useNavigate()
  const [listData, setListData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  
  // Form state
  const [itemTitle, setItemTitle] = useState('')
  const [itemDescription, setItemDescription] = useState('')
  const [itemTags, setItemTags] = useState('')
  const [itemNotes, setItemNotes] = useState('')
  const [itemAddress, setItemAddress] = useState('')
  const [itemUrl, setItemUrl] = useState('')
  const [saving, setSaving] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5555'

  const fetchListData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setListData(data)
    } catch (e) {
      setError(e.message)
      console.error('Error fetching list data:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchListData()
  }, [listId])

  const resetForm = () => {
    setItemTitle('')
    setItemDescription('')
    setItemTags('')
    setItemNotes('')
    setItemAddress('')
    setItemUrl('')
    setEditingItem(null)
    setShowAddForm(false)
  }

  const handleAddItem = async (e) => {
    e.preventDefault()
    if (!itemTitle.trim()) return

    setSaving(true)
    try {
      // Build metadata
      const metadata = {}
      if (itemTags.trim()) {
        metadata.tags = itemTags.split(',').map(tag => tag.trim()).filter(Boolean)
      }
      if (itemNotes.trim()) {
        metadata.notes = itemNotes.trim()
      }
      if (itemAddress.trim()) {
        metadata.address = itemAddress.trim()
      }
      if (itemUrl.trim()) {
        metadata.url = itemUrl.trim()
      }

      const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: itemTitle,
          description: itemDescription,
          metadata: metadata
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to add item')
      }

      await fetchListData()
      resetForm()
    } catch (error) {
      alert(`Error adding item: ${error.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleEditItem = (item) => {
    setEditingItem(item)
    setItemTitle(item.title)
    setItemDescription(item.description || '')
    setItemTags((item.metadata?.tags || []).join(', '))
    setItemNotes(item.metadata?.notes || '')
    setItemAddress(item.metadata?.address || '')
    setItemUrl(item.metadata?.url || item.metadata?.google_maps_url || '')
    setShowAddForm(true)
  }

  const handleUpdateItem = async (e) => {
    e.preventDefault()
    if (!editingItem || !itemTitle.trim()) return

    setSaving(true)
    try {
      const metadata = {}
      if (itemTags.trim()) {
        metadata.tags = itemTags.split(',').map(tag => tag.trim()).filter(Boolean)
      }
      if (itemNotes.trim()) {
        metadata.notes = itemNotes.trim()
      }
      if (itemAddress.trim()) {
        metadata.address = itemAddress.trim()
      }
      if (itemUrl.trim()) {
        metadata.url = itemUrl.trim()
      }

      const response = await fetch(`${API_BASE_URL}/api/lists/items/${editingItem.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: itemTitle,
          description: itemDescription,
          metadata: metadata
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to update item')
      }

      await fetchListData()
      resetForm()
    } catch (error) {
      alert(`Error updating item: ${error.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteItem = async (itemId) => {
    if (!confirm('Are you sure you want to delete this item?')) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/lists/items/${itemId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to delete item')
      }

      await fetchListData()
    } catch (error) {
      alert(`Error deleting item: ${error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading list data...</div>
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

  if (!listData) {
    return (
      <div className="container">
        <div className="error">List not found</div>
      </div>
    )
  }

  const { list, items } = listData

  return (
    <div className="container">
      <div className="header">
        <div className="header-with-back">
          <button className="back-button" onClick={() => navigate('/lists')}>
            ← Back to Lists
          </button>
          <div>
            <h1>📋 {list.name}</h1>
            {list.description && <p>{list.description}</p>}
            <p className="list-meta-info">
              <span className="list-category-badge">{list.category}</span>
              <span className="item-count">{items.length} item{items.length !== 1 ? 's' : ''}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="content">
        <div className="add-item-section">
          {!showAddForm ? (
            <button 
              className="button primary-button"
              onClick={() => setShowAddForm(true)}
            >
              + Add Item
            </button>
          ) : (
            <form onSubmit={editingItem ? handleUpdateItem : handleAddItem} className="item-form">
              <h3>{editingItem ? 'Edit Item' : 'Add New Item'}</h3>
              
              <div className="form-group">
                <label htmlFor="itemTitle">Title *</label>
                <input
                  id="itemTitle"
                  type="text"
                  placeholder="Item name"
                  value={itemTitle}
                  onChange={(e) => setItemTitle(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="itemDescription">Description</label>
                <textarea
                  id="itemDescription"
                  placeholder="Optional description"
                  value={itemDescription}
                  onChange={(e) => setItemDescription(e.target.value)}
                  rows="3"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="itemTags">Tags</label>
                  <input
                    id="itemTags"
                    type="text"
                    placeholder="comma, separated, tags"
                    value={itemTags}
                    onChange={(e) => setItemTags(e.target.value)}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="itemAddress">Address</label>
                  <input
                    id="itemAddress"
                    type="text"
                    placeholder="Location address"
                    value={itemAddress}
                    onChange={(e) => setItemAddress(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="itemUrl">URL</label>
                <input
                  id="itemUrl"
                  type="url"
                  placeholder="https://..."
                  value={itemUrl}
                  onChange={(e) => setItemUrl(e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="itemNotes">Notes</label>
                <textarea
                  id="itemNotes"
                  placeholder="Additional notes"
                  value={itemNotes}
                  onChange={(e) => setItemNotes(e.target.value)}
                  rows="3"
                />
              </div>
              
              <div className="form-actions">
                <button 
                  type="submit" 
                  className="button primary-button"
                  disabled={saving || !itemTitle.trim()}
                >
                  {saving ? 'Saving...' : (editingItem ? 'Update Item' : 'Add Item')}
                </button>
                <button 
                  type="button"
                  className="button secondary-button"
                  onClick={resetForm}
                  disabled={saving}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {items.length === 0 ? (
          <div className="empty-state">
            <p>No items yet.</p>
            <p className="tip">Add your first item to start building this list!</p>
          </div>
        ) : (
          <div className="items-list">
            {items.map((item) => (
              <div key={item.id} className="item-card">
                <div className="item-header">
                  <h3>{item.title}</h3>
                  <div className="item-actions">
                    <button 
                      className="icon-button edit-button"
                      onClick={() => handleEditItem(item)}
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button 
                      className="icon-button delete-button"
                      onClick={() => handleDeleteItem(item.id)}
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                
                {item.description && (
                  <p className="item-description">{item.description}</p>
                )}
                
                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <div className="item-metadata">
                    {item.metadata.tags && item.metadata.tags.length > 0 && (
                      <div className="metadata-field">
                        <span className="metadata-label">Tags:</span>
                        <div className="tags">
                          {item.metadata.tags.map((tag, idx) => (
                            <span key={idx} className="tag">#{tag}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {item.metadata.address && (
                      <div className="metadata-field">
                        <span className="metadata-label">📍</span>
                        <span>{item.metadata.address}</span>
                      </div>
                    )}
                    
                    {(item.metadata.url || item.metadata.google_maps_url) && (
                      <div className="metadata-field">
                        <span className="metadata-label">🔗</span>
                        <a 
                          href={item.metadata.url || item.metadata.google_maps_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                        >
                          {item.metadata.url || item.metadata.google_maps_url}
                        </a>
                      </div>
                    )}
                    
                    {item.metadata.notes && (
                      <div className="metadata-field notes">
                        <span className="metadata-label">Notes:</span>
                        <span>{item.metadata.notes}</span>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="item-footer">
                  <span className="item-date">
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  {item.updated_at !== item.created_at && (
                    <span className="item-date">
                      Updated {new Date(item.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ListDetail

