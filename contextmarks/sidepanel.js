let allBookmarks = [];

// Load and display bookmarks
async function loadBookmarks() {
  const result = await chrome.storage.local.get(['bookmarks']);
  allBookmarks = result.bookmarks || [];
  displayBookmarks(allBookmarks);
  updateStats();
}

// Display bookmarks
function displayBookmarks(bookmarks) {
  const list = document.getElementById('bookmarksList');
  const emptyState = document.getElementById('emptyState');
  
  if (bookmarks.length === 0) {
    list.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }
  
  emptyState.style.display = 'none';
  
  list.innerHTML = bookmarks.map(bookmark => {
    const date = new Date(bookmark.timestamp);
    const formattedDate = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    
    const favicon = bookmark.favicon 
      ? `<img src="${bookmark.favicon}" class="favicon" alt="">`
      : '<div class="favicon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></div>';
    
    const tags = bookmark.tags && bookmark.tags.length > 0
      ? `<div class="tags">${bookmark.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}</div>`
      : '';
    
    return `
      <div class="bookmark-card" data-id="${bookmark.id}">
        <div class="bookmark-header">
          ${favicon}
          <div style="flex: 1; min-width: 0;">
            <div class="bookmark-title">${bookmark.title}</div>
            <div class="bookmark-url">${bookmark.url}</div>
          </div>
        </div>
        
        <div class="bookmark-context">
          ${bookmark.context}
        </div>
        
        <div class="bookmark-footer">
          <div style="flex: 1;">
            ${tags}
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <span class="timestamp">${formattedDate}</span>
            <div class="actions">
              <button class="btn-icon btn-delete" data-id="${bookmark.id}" title="Delete">🗑️</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  
  // Add click handlers
  document.querySelectorAll('.bookmark-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (!e.target.closest('.btn-delete')) {
        const bookmark = bookmarks.find(b => b.id === card.dataset.id);
        if (bookmark) {
          window.open(bookmark.url, '_blank');
        }
      }
    });
  });
  
  // Add delete handlers
  document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.dataset.id;
      if (confirm('Delete this bookmark?')) {
        await deleteBookmark(id);
      }
    });
  });
}

// Update statistics
function updateStats() {
  document.getElementById('totalCount').textContent = allBookmarks.length;
  
  const uniqueTags = new Set();
  allBookmarks.forEach(b => {
    if (b.tags) {
      b.tags.forEach(tag => uniqueTags.add(tag));
    }
  });
  document.getElementById('tagCount').textContent = uniqueTags.size;
}

// Delete bookmark
async function deleteBookmark(id) {
  allBookmarks = allBookmarks.filter(b => b.id !== id);
  await chrome.storage.local.set({ bookmarks: allBookmarks });
  displayBookmarks(allBookmarks);
  updateStats();
}

// Search functionality
document.getElementById('searchInput').addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  
  if (!query) {
    displayBookmarks(allBookmarks);
    return;
  }
  
  const filtered = allBookmarks.filter(bookmark => {
    return bookmark.title.toLowerCase().includes(query) ||
           bookmark.context.toLowerCase().includes(query) ||
           bookmark.url.toLowerCase().includes(query) ||
           (bookmark.tags && bookmark.tags.some(tag => tag.toLowerCase().includes(query)));
  });
  
  displayBookmarks(filtered);
});

// Export data
document.getElementById('exportBtn').addEventListener('click', () => {
  const dataStr = JSON.stringify(allBookmarks, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `context-bookmarks-${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
});

// Initialize
loadBookmarks();
