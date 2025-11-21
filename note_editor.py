"""Web-based markdown note editor using Flask."""

import webbrowser
import threading
import time
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
from storage import storage


class NoteEditor:
    """Web-based markdown editor for creating notes."""
    
    def __init__(self, port=5555):
        self.port = port
        self.app = Flask(__name__)
        self.saved_note = None
        self.server_thread = None
        self.shutdown_flag = False
        
        # Setup routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/save', 'save', self.save, methods=['POST'])
        
        # Disable Flask logging
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    
    def index(self):
        """Serve the markdown editor page."""
        return render_template_string(EDITOR_TEMPLATE)
    
    def save(self):
        """Handle note saving."""
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Save the note
        try:
            storage.add_note_to_journal(title, content)
            self.saved_note = {'title': title, 'content': content}
            
            # Schedule server shutdown
            threading.Timer(0.5, self.shutdown_server).start()
            
            return jsonify({'success': True, 'message': 'Note saved successfully!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def shutdown_server(self):
        """Shutdown the Flask server."""
        # Use signal-based shutdown which works outside request context
        import os
        import signal
        os.kill(os.getpid(), signal.SIGINT)
    
    def open_editor(self):
        """Open the note editor in the default browser."""
        # Wait a moment for server to start
        time.sleep(0.5)
        webbrowser.open(f'http://localhost:{self.port}')
    
    def run(self):
        """Start the Flask server and open the editor."""
        # Open browser in a separate thread
        threading.Thread(target=self.open_editor, daemon=True).start()
        
        # Run Flask server
        try:
            self.app.run(host='localhost', port=self.port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            pass
        
        return self.saved_note


# HTML Template for the editor
EDITOR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Note - Focus Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .header p {
            opacity: 0.9;
            margin-top: 5px;
            font-size: 14px;
        }
        
        .editor-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 30px;
        }
        
        .editor-pane, .preview-pane {
            display: flex;
            flex-direction: column;
        }
        
        label {
            font-weight: 600;
            margin-bottom: 8px;
            display: block;
            color: #555;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.2s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
            resize: none;
            min-height: 400px;
            transition: border-color 0.2s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .preview {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            background: #fafafa;
            overflow-y: auto;
            min-height: 400px;
            line-height: 1.6;
        }
        
        .preview h1, .preview h2, .preview h3 {
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        .preview h1 { font-size: 24px; }
        .preview h2 { font-size: 20px; }
        .preview h3 { font-size: 18px; }
        
        .preview p {
            margin-bottom: 10px;
        }
        
        .preview code {
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
        
        .preview pre {
            background: #2d2d2d;
            color: #f8f8f8;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 10px 0;
        }
        
        .preview ul, .preview ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        .preview blockquote {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 10px 0;
            color: #666;
            font-style: italic;
        }
        
        .actions {
            padding: 20px 30px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-save {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-save:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-save:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            color: #666;
            font-size: 14px;
        }
        
        .success {
            color: #10b981;
            font-weight: 600;
        }
        
        .error {
            color: #ef4444;
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .editor-container {
                grid-template-columns: 1fr;
            }
            
            .preview-pane {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 New Note</h1>
            <p>Write your thoughts in markdown format</p>
        </div>
        
        <div class="editor-container">
            <div class="editor-pane">
                <label for="title">Note Title *</label>
                <input type="text" id="title" placeholder="Enter a title for your note..." required>
                
                <label for="content">Content (Markdown) *</label>
                <textarea id="content" placeholder="Write your note here using markdown...

Examples:
# Heading 1
## Heading 2

**bold text**
*italic text*

- List item 1
- List item 2

> Quote

`code`"></textarea>
            </div>
            
            <div class="preview-pane">
                <label>Live Preview</label>
                <div class="preview" id="preview">
                    <p style="color: #999; font-style: italic;">Start typing to see preview...</p>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <div class="status" id="status"></div>
            <button class="btn-save" id="saveBtn" onclick="saveNote()">Save Note</button>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        const titleInput = document.getElementById('title');
        const contentInput = document.getElementById('content');
        const preview = document.getElementById('preview');
        const saveBtn = document.getElementById('saveBtn');
        const status = document.getElementById('status');
        
        // Update preview on content change
        contentInput.addEventListener('input', updatePreview);
        titleInput.addEventListener('input', updatePreview);
        
        function updatePreview() {
            const content = contentInput.value;
            const title = titleInput.value;
            
            if (!content && !title) {
                preview.innerHTML = '<p style="color: #999; font-style: italic;">Start typing to see preview...</p>';
                return;
            }
            
            let markdown = '';
            if (title) {
                markdown += '# ' + title + '\\n\\n';
            }
            markdown += content;
            
            preview.innerHTML = marked.parse(markdown);
        }
        
        async function saveNote() {
            const title = titleInput.value.trim();
            const content = contentInput.value.trim();
            
            if (!title) {
                status.textContent = 'Please enter a title';
                status.className = 'status error';
                return;
            }
            
            if (!content) {
                status.textContent = 'Please enter some content';
                status.className = 'status error';
                return;
            }
            
            saveBtn.disabled = true;
            status.textContent = 'Saving...';
            status.className = 'status';
            
            try {
                const response = await fetch('/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title, content })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    status.textContent = '✓ Note saved! Closing editor...';
                    status.className = 'status success';
                    
                    // Close window after a short delay
                    setTimeout(() => {
                        window.close();
                    }, 1000);
                } else {
                    status.textContent = 'Error: ' + data.error;
                    status.className = 'status error';
                    saveBtn.disabled = false;
                }
            } catch (error) {
                status.textContent = 'Error saving note: ' + error.message;
                status.className = 'status error';
                saveBtn.disabled = false;
            }
        }
        
        // Allow Cmd+S / Ctrl+S to save
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 's') {
                e.preventDefault();
                saveNote();
            }
        });
        
        // Focus title on load
        titleInput.focus();
    </script>
</body>
</html>
'''


def open_note_editor():
    """Open the note editor and return the saved note data."""
    editor = NoteEditor()
    return editor.run()


def start_journal_editor(date=None):
    """Start a web server that allows editing today's journal."""
    from datetime import datetime as dt
    from flask import Flask, render_template_string, request, jsonify
    import webbrowser
    import signal
    
    if date is None:
        date = dt.now()
    
    app = Flask(__name__)
    
    # Disable Flask logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    @app.route('/')
    def index():
        """Serve the journal editor page."""
        # Load the current journal
        journal_file = storage.get_journal_file(date)
        content = ""
        
        if journal_file.exists():
            with open(journal_file, 'r') as f:
                content = f.read()
        
        return render_template_string(JOURNAL_EDITOR_TEMPLATE, 
                                     date_str=date.strftime('%A, %B %d, %Y'),
                                     content=content)
    
    @app.route('/save', methods=['POST'])
    def save():
        """Save the edited journal."""
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
        
        try:
            # Save the markdown file directly
            journal_file = storage.get_journal_file(date)
            with open(journal_file, 'w') as f:
                f.write(content)
            
            # Also re-parse and save via storage to update embeddings
            journal_data = storage._parse_markdown_journal(content)
            storage._auto_embed_journal(journal_data, date)
            
            return jsonify({'success': True, 'message': 'Journal saved successfully!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    try:
        app.run(host='localhost', port=5556, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass


# HTML Template for the journal editor
def start_tasks_gui():
    """Start a web server that shows tasks with checkboxes."""
    from flask import Flask, render_template_string, request, jsonify
    from tasks import task_manager
    
    app = Flask(__name__)
    
    # Disable Flask logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    @app.route('/')
    def index():
        """Serve the tasks GUI page."""
        return render_template_string(TASKS_GUI_TEMPLATE)
    
    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        """Get all tasks."""
        today_tasks = task_manager.get_today_tasks()
        upcoming_tasks = task_manager.get_upcoming_tasks()
        inbox_tasks = task_manager.get_inbox_tasks()
        
        return jsonify({
            'today': [{'id': t.id, 'text': t.text, 'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None} for t in today_tasks],
            'upcoming': [{'id': t.id, 'text': t.text, 'due_date': t.due_date.strftime('%a, %b %d') if t.due_date else None} for t in upcoming_tasks],
            'inbox': [{'id': t.id, 'text': t.text} for t in inbox_tasks]
        })
    
    @app.route('/api/tasks/<task_id>/complete', methods=['POST'])
    def complete_task(task_id):
        """Mark a task as complete."""
        try:
            task_manager.complete_task(task_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    try:
        app.run(host='localhost', port=5557, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass


# HTML Template for the tasks GUI
TASKS_GUI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tasks - Focus Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .content {
            background: white;
            padding: 30px;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section:last-child {
            margin-bottom: 0;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .section-header h2 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }
        
        .section-header .count {
            background: #667eea;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .today .section-header h2 { color: #f59e0b; }
        .upcoming .section-header h2 { color: #3b82f6; }
        .inbox .section-header h2 { color: #8b5cf6; }
        
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .task-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: #fafafa;
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .task-item:hover {
            background: #f0f0f0;
            transform: translateX(2px);
        }
        
        .task-item.completing {
            opacity: 0.5;
            transform: scale(0.98);
        }
        
        .task-checkbox {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #667eea;
        }
        
        .task-text {
            flex: 1;
            font-size: 15px;
            line-height: 1.5;
        }
        
        .task-due {
            font-size: 12px;
            color: #999;
            background: #e0e0e0;
            padding: 3px 8px;
            border-radius: 4px;
        }
        
        .empty-state {
            text-align: center;
            padding: 30px;
            color: #999;
            font-style: italic;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        .stats {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 6px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Tasks</h1>
            <p>Check boxes to mark tasks as complete</p>
        </div>
        
        <div class="content">
            <div id="loading" class="loading">Loading tasks</div>
            <div id="tasks" style="display: none;">
                <!-- Today's Tasks -->
                <div class="section today">
                    <div class="section-header">
                        <h2>📌 Today</h2>
                        <span class="count" id="today-count">0</span>
                    </div>
                    <div class="task-list" id="today-list"></div>
                </div>
                
                <!-- Upcoming Tasks -->
                <div class="section upcoming">
                    <div class="section-header">
                        <h2>📅 Upcoming</h2>
                        <span class="count" id="upcoming-count">0</span>
                    </div>
                    <div class="task-list" id="upcoming-list"></div>
                </div>
                
                <!-- Inbox Tasks -->
                <div class="section inbox">
                    <div class="section-header">
                        <h2>📥 Inbox</h2>
                        <span class="count" id="inbox-count">0</span>
                    </div>
                    <div class="task-list" id="inbox-list"></div>
                </div>
                
                <div class="stats" id="stats"></div>
            </div>
        </div>
    </div>
    
    <script>
        let tasks = { today: [], upcoming: [], inbox: [] };
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                tasks = await response.json();
                renderTasks();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('tasks').style.display = 'block';
            } catch (error) {
                document.getElementById('loading').textContent = 'Error loading tasks: ' + error.message;
            }
        }
        
        function renderTasks() {
            renderSection('today', tasks.today, true);
            renderSection('upcoming', tasks.upcoming, true);
            renderSection('inbox', tasks.inbox, false);
            updateStats();
        }
        
        function renderSection(section, taskList, showDue) {
            const listEl = document.getElementById(section + '-list');
            const countEl = document.getElementById(section + '-count');
            
            countEl.textContent = taskList.length;
            
            if (taskList.length === 0) {
                listEl.innerHTML = '<div class="empty-state">No tasks here</div>';
                return;
            }
            
            listEl.innerHTML = taskList.map(task => `
                <div class="task-item" data-task-id="${task.id}">
                    <input 
                        type="checkbox" 
                        class="task-checkbox" 
                        onchange="completeTask('${task.id}')"
                    >
                    <span class="task-text">${escapeHtml(task.text)}</span>
                    ${showDue && task.due_date ? `<span class="task-due">${task.due_date}</span>` : ''}
                </div>
            `).join('');
        }
        
        async function completeTask(taskId) {
            const taskEl = document.querySelector(`[data-task-id="${taskId}"]`);
            taskEl.classList.add('completing');
            
            try {
                const response = await fetch(`/api/tasks/${taskId}/complete`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Remove from UI after animation
                    setTimeout(() => {
                        taskEl.style.transition = 'all 0.3s';
                        taskEl.style.opacity = '0';
                        taskEl.style.transform = 'translateX(20px)';
                        
                        setTimeout(() => {
                            // Remove from data
                            tasks.today = tasks.today.filter(t => t.id !== taskId);
                            tasks.upcoming = tasks.upcoming.filter(t => t.id !== taskId);
                            tasks.inbox = tasks.inbox.filter(t => t.id !== taskId);
                            renderTasks();
                        }, 300);
                    }, 500);
                } else {
                    taskEl.classList.remove('completing');
                    alert('Error completing task');
                }
            } catch (error) {
                taskEl.classList.remove('completing');
                alert('Error: ' + error.message);
            }
        }
        
        function updateStats() {
            const total = tasks.today.length + tasks.upcoming.length + tasks.inbox.length;
            document.getElementById('stats').textContent = `Total: ${total} incomplete tasks`;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load tasks on page load
        loadTasks();
        
        // Refresh tasks every 30 seconds
        setInterval(loadTasks, 30000);
    </script>
</body>
</html>
'''


def start_project_viewer(project_id):
    """Start a web server that displays all project information."""
    from flask import Flask, render_template_string, jsonify, abort
    from projects import project_manager
    from tasks import task_manager
    from storage import storage
    
    app = Flask(__name__)
    
    # Enable Flask logging for debugging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    
    print(f"\n[DEBUG] Starting project viewer for project_id: {project_id}")
    
    @app.route('/project/<pid>')
    def view_project(pid):
        """Serve the project view page."""
        project = project_manager.get_project(pid)
        if not project:
            abort(404)
        
        return render_template_string(PROJECT_VIEW_TEMPLATE, 
                                     project_name=project.name,
                                     project_description=project.description,
                                     project_id=pid)
    
    @app.route('/api/project/<pid>/data')
    def get_project_data(pid):
        """Get all project data (tasks and notes)."""
        try:
            project = project_manager.get_project(pid)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            # Get tasks
            tasks_data = []
            all_tasks = storage.load_tasks()
            project_tasks = [t for t in all_tasks if t.project_id == pid]
            
            for task in project_tasks:
                tasks_data.append({
                    'id': task.id,
                    'text': task.text,
                    'completed': task.completed,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'created_at': task.created_at.strftime('%Y-%m-%d %I:%M %p'),
                    'completed_at': task.completed_at.strftime('%Y-%m-%d %I:%M %p') if task.completed_at else None
                })
            
            # Get notes
            notes_data = []
            project_notes = project_manager.get_project_notes(pid)
            
            for note in project_notes:
                notes_data.append({
                    'title': note['title'],
                    'content': note['content'],
                    'timestamp': note['timestamp'],
                    'date': note['date']
                })
            
            return jsonify({
                'project': {
                    'name': project.name,
                    'description': project.description,
                    'color': project.color
                },
                'tasks': tasks_data,
                'notes': notes_data
            })
        except Exception as e:
            import traceback
            print(f"Error in get_project_data: {e}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tasks/<task_id>/complete', methods=['POST'])
    def complete_task(task_id):
        """Mark a task as complete."""
        try:
            task_manager.complete_task(task_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    try:
        app.run(host='localhost', port=5558, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass


PROJECT_VIEW_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - Focus Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 16px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .section {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .section-header h2 {
            font-size: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .count-badge {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
        }
        
        .task-list, .note-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .task-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px;
            background: #fafafa;
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .task-item:hover {
            background: #f0f0f0;
            transform: translateX(2px);
        }
        
        .task-item.completed {
            opacity: 0.6;
        }
        
        .task-item.completed .task-text {
            text-decoration: line-through;
        }
        
        .task-checkbox {
            width: 20px;
            height: 20px;
            margin-top: 2px;
            cursor: pointer;
            accent-color: #667eea;
            flex-shrink: 0;
        }
        
        .task-details {
            flex: 1;
            min-width: 0;
        }
        
        .task-text {
            font-size: 15px;
            line-height: 1.5;
            margin-bottom: 4px;
            word-wrap: break-word;
        }
        
        .task-meta {
            display: flex;
            gap: 10px;
            font-size: 12px;
            color: #999;
        }
        
        .task-due {
            background: #fef3c7;
            color: #92400e;
            padding: 2px 8px;
            border-radius: 4px;
        }
        
        .note-item {
            padding: 15px;
            background: #fafafa;
            border-left: 4px solid #667eea;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        
        .note-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .note-title {
            font-weight: 600;
            font-size: 15px;
            color: #667eea;
        }
        
        .note-date {
            font-size: 12px;
            color: #999;
            white-space: nowrap;
        }
        
        .note-content {
            font-size: 14px;
            line-height: 1.6;
            color: #555;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .note-content strong {
            font-weight: 600;
            color: #333;
        }
        
        .note-content em {
            font-style: italic;
        }
        
        .note-content code {
            background: #e0e0e0;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 13px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-style: italic;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        .stats {
            grid-column: 1 / -1;
            background: white;
            padding: 20px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        
        .stat-item {
            flex: 1;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        
        @media (max-width: 968px) {
            .content {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-column: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 {{ project_name }}</h1>
            {% if project_description %}
            <p>{{ project_description }}</p>
            {% endif %}
        </div>
        
        <div id="loading" class="loading">Loading project data</div>
        
        <div id="content" class="content" style="display: none;">
            <!-- Tasks Section -->
            <div class="section">
                <div class="section-header">
                    <h2>
                        <span>✅ Tasks</span>
                    </h2>
                    <span class="count-badge" id="task-count">0</span>
                </div>
                <div class="task-list" id="task-list"></div>
            </div>
            
            <!-- Notes Section -->
            <div class="section">
                <div class="section-header">
                    <h2>
                        <span>📝 Notes</span>
                    </h2>
                    <span class="count-badge" id="note-count">0</span>
                </div>
                <div class="note-list" id="note-list"></div>
            </div>
            
            <!-- Stats Section -->
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="active-tasks">0</div>
                    <div class="stat-label">Active Tasks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="completed-tasks">0</div>
                    <div class="stat-label">Completed Tasks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-notes">0</div>
                    <div class="stat-label">Notes</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const projectId = '{{ project_id }}';
        let projectData = {};
        
        async function loadProjectData() {
            try {
                console.log('Loading project data for:', projectId);
                const response = await fetch('/api/project/' + projectId + '/data');
                console.log('Response status:', response.status);
                projectData = await response.json();
                console.log('Project data loaded:', projectData);
                renderProjectData();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'grid';
            } catch (error) {
                console.error('Error loading project:', error);
                document.getElementById('loading').textContent = 'Error loading project: ' + error.message;
            }
        }
        
        function renderProjectData() {
            renderTasks();
            renderNotes();
            updateStats();
        }
        
        function renderTasks() {
            const taskList = document.getElementById('task-list');
            const tasks = projectData.tasks || [];
            
            document.getElementById('task-count').textContent = tasks.filter(t => !t.completed).length;
            
            if (tasks.length === 0) {
                taskList.innerHTML = '<div class="empty-state">No tasks in this project</div>';
                return;
            }
            
            // Sort: incomplete first, then by date
            tasks.sort(function(a, b) {
                if (a.completed !== b.completed) return a.completed ? 1 : -1;
                return new Date(b.created_at) - new Date(a.created_at);
            });
            
            console.log('Rendering', tasks.length, 'tasks');
            
            taskList.innerHTML = tasks.map(function(task) {
                var html = '<div class="task-item ' + (task.completed ? 'completed' : '') + '" data-task-id="' + task.id + '">';
                html += '<input type="checkbox" class="task-checkbox" ';
                if (task.completed) {
                    html += 'checked disabled ';
                }
                html += 'onchange="completeTask(\\'' + task.id + '\\')">';
                html += '<div class="task-details">';
                html += '<div class="task-text">' + escapeHtml(task.text) + '</div>';
                html += '<div class="task-meta">';
                html += '<span>Created ' + task.created_at + '</span>';
                if (task.due_date) {
                    html += '<span class="task-due">Due ' + task.due_date + '</span>';
                }
                if (task.completed_at) {
                    html += '<span>Completed ' + task.completed_at + '</span>';
                }
                html += '</div></div></div>';
                return html;
            }).join('');
        }
        
        function renderNotes() {
            const noteList = document.getElementById('note-list');
            const notes = projectData.notes || [];
            
            document.getElementById('note-count').textContent = notes.length;
            
            if (notes.length === 0) {
                noteList.innerHTML = '<div class="empty-state">No notes in this project yet</div>';
                return;
            }
            
            // Sort by date, most recent first
            notes.sort(function(a, b) {
                var dateA = new Date(a.date + ' ' + a.timestamp);
                var dateB = new Date(b.date + ' ' + b.timestamp);
                return dateB - dateA;
            });
            
            noteList.innerHTML = notes.map(function(note) {
                var html = '<div class="note-item">';
                html += '<div class="note-header">';
                html += '<div class="note-title">' + escapeHtml(note.title) + '</div>';
                html += '<div class="note-date">' + note.date + ' ' + note.timestamp + '</div>';
                html += '</div>';
                html += '<div class="note-content">' + renderMarkdown(note.content) + '</div>';
                html += '</div>';
                return html;
            }).join('');
        }
        
        function updateStats() {
            const tasks = projectData.tasks || [];
            const activeTasks = tasks.filter(t => !t.completed).length;
            const completedTasks = tasks.filter(t => t.completed).length;
            const totalNotes = (projectData.notes || []).length;
            
            document.getElementById('active-tasks').textContent = activeTasks;
            document.getElementById('completed-tasks').textContent = completedTasks;
            document.getElementById('total-notes').textContent = totalNotes;
        }
        
        async function completeTask(taskId) {
            const taskEl = document.querySelector(`[data-task-id="${taskId}"]`);
            const checkbox = taskEl.querySelector('.task-checkbox');
            checkbox.disabled = true;
            
            try {
                const response = await fetch(`/api/tasks/${taskId}/complete`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Reload data to refresh
                    await loadProjectData();
                } else {
                    checkbox.checked = false;
                    checkbox.disabled = false;
                    alert('Error completing task');
                }
            } catch (error) {
                checkbox.checked = false;
                checkbox.disabled = false;
                alert('Error: ' + error.message);
            }
        }
        
        function renderMarkdown(text) {
            // Simple markdown rendering for basic formatting
            var boldRegex = /\*\*(.+?)\*\*/g;
            var italicRegex = /\*(.+?)\*/g;
            var codeRegex = /`(.+?)`/g;
            var newlineRegex = /\n/g;
            
            return text
                .replace(boldRegex, '<strong>$1</strong>')
                .replace(italicRegex, '<em>$1</em>')
                .replace(codeRegex, '<code>$1</code>')
                .replace(newlineRegex, '<br>');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load project data on page load
        console.log('Page loaded, starting to load project data...');
        
        // Use setTimeout to ensure page is fully loaded
        setTimeout(function() {
            loadProjectData();
        }, 100);
        
        // Refresh every 30 seconds
        setInterval(loadProjectData, 30000);
    </script>
</body>
</html>
'''


JOURNAL_EDITOR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ date_str }} - Daily Journal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            flex-shrink: 0;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .header p {
            opacity: 0.9;
            margin-top: 5px;
            font-size: 14px;
        }
        
        .editor-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 30px;
            flex: 1;
            overflow: hidden;
        }
        
        .editor-pane, .preview-pane {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        
        label {
            font-weight: 600;
            margin-bottom: 8px;
            display: block;
            color: #555;
            flex-shrink: 0;
        }
        
        textarea {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
            resize: none;
            transition: border-color 0.2s;
            min-height: 0;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .preview {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            background: #fafafa;
            overflow-y: auto;
            line-height: 1.6;
            min-height: 0;
        }
        
        .preview h1, .preview h2, .preview h3 {
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        .preview h1 { font-size: 24px; }
        .preview h2 { font-size: 20px; }
        .preview h3 { font-size: 18px; }
        
        .preview p {
            margin-bottom: 10px;
        }
        
        .preview code {
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
        
        .preview pre {
            background: #2d2d2d;
            color: #f8f8f8;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 10px 0;
        }
        
        .preview ul, .preview ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        .preview blockquote {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 10px 0;
            color: #666;
            font-style: italic;
        }
        
        .preview hr {
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 20px 0;
        }
        
        .actions {
            padding: 20px 30px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        
        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-save {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-save:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-save:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            color: #666;
            font-size: 14px;
        }
        
        .success {
            color: #10b981;
            font-weight: 600;
        }
        
        .error {
            color: #ef4444;
            font-weight: 600;
        }
        
        @media (max-width: 968px) {
            .editor-container {
                grid-template-columns: 1fr;
            }
            
            .preview-pane {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📓 Daily Journal</h1>
            <p>{{ date_str }}</p>
        </div>
        
        <div class="editor-container">
            <div class="editor-pane">
                <label for="content">Journal (Markdown)</label>
                <textarea id="content" placeholder="Edit your daily journal...">{{ content }}</textarea>
            </div>
            
            <div class="preview-pane">
                <label>Live Preview</label>
                <div class="preview" id="preview"></div>
            </div>
        </div>
        
        <div class="actions">
            <div class="status" id="status">
                <span style="color: #999;">💡 Tip: Press Cmd/Ctrl+S to save</span>
            </div>
            <button class="btn-save" id="saveBtn" onclick="saveJournal()">Save Journal</button>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        const contentInput = document.getElementById('content');
        const preview = document.getElementById('preview');
        const saveBtn = document.getElementById('saveBtn');
        const status = document.getElementById('status');
        
        // Update preview on content change
        contentInput.addEventListener('input', updatePreview);
        
        // Initial preview
        updatePreview();
        
        function updatePreview() {
            const content = contentInput.value;
            
            if (!content) {
                preview.innerHTML = '<p style="color: #999; font-style: italic;">Your journal is empty...</p>';
                return;
            }
            
            preview.innerHTML = marked.parse(content);
        }
        
        async function saveJournal() {
            const content = contentInput.value.trim();
            
            if (!content) {
                status.innerHTML = '<span class="error">Journal cannot be empty</span>';
                return;
            }
            
            saveBtn.disabled = true;
            status.innerHTML = '<span>Saving...</span>';
            
            try {
                const response = await fetch('/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ content })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    status.innerHTML = '<span class="success">✓ Journal saved!</span>';
                    saveBtn.disabled = false;
                } else {
                    status.innerHTML = '<span class="error">Error: ' + data.error + '</span>';
                    saveBtn.disabled = false;
                }
            } catch (error) {
                status.innerHTML = '<span class="error">Error saving journal: ' + error.message + '</span>';
                saveBtn.disabled = false;
            }
        }
        
        // Allow Cmd+S / Ctrl+S to save
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 's') {
                e.preventDefault();
                saveJournal();
            }
        });
        
        // Focus editor on load
        contentInput.focus();
        contentInput.setSelectionRange(contentInput.value.length, contentInput.value.length);
    </script>
</body>
</html>
'''

