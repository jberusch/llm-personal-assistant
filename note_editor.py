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

