"""Flask API server for Focus Assistant web UI."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from storage import storage
from tasks import task_manager
from projects import project_manager


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow React dev server to call APIs
    
    # Tasks endpoints
    
    @app.route('/api/tasks')
    def get_tasks():
        """Get all tasks organized by category."""
        today_tasks = task_manager.get_today_tasks()
        upcoming_tasks = task_manager.get_upcoming_tasks()
        inbox_tasks = task_manager.get_inbox_tasks()
        
        return jsonify({
            'today': [task_to_dict(t) for t in today_tasks],
            'upcoming': [task_to_dict(t) for t in upcoming_tasks],
            'inbox': [task_to_dict(t) for t in inbox_tasks]
        })
    
    @app.route('/api/tasks', methods=['POST', 'OPTIONS'])
    def create_task():
        """Create a new task."""
        if request.method == 'OPTIONS':
            return '', 204
        try:
            data = request.get_json()
            text = data.get('text', '').strip()
            project_id = data.get('project_id')
            due_date_str = data.get('due_date')
            
            if not text:
                return jsonify({'error': 'Task text is required'}), 400
            
            # Parse due date if provided
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    return jsonify({'error': 'Invalid due date format. Use YYYY-MM-DD'}), 400
            
            # Create task
            task = task_manager.add_task(text, due_date=due_date, project_id=project_id)
            
            return jsonify({
                'success': True,
                'task': task_to_dict(task)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tasks/<task_id>/complete', methods=['POST', 'OPTIONS'])
    def complete_task(task_id):
        """Mark a task as complete."""
        if request.method == 'OPTIONS':
            return '', 204
        try:
            task_manager.complete_task(task_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Daily Pages endpoints
    
    @app.route('/api/daily-pages', methods=['GET'])
    def get_daily_pages():
        """Get today's daily pages."""
        try:
            journal = storage.load_journal()
            daily_pages = journal.get("daily_pages")
            
            return jsonify({
                'content': daily_pages if daily_pages else ''
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/daily-pages', methods=['POST', 'OPTIONS'])
    def save_daily_pages():
        """Save daily pages for today."""
        if request.method == 'OPTIONS':
            return '', 204
        try:
            data = request.get_json()
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'error': 'Content is required'}), 400
            
            # Load journal and add daily pages
            journal = storage.load_journal()
            journal["daily_pages"] = content
            storage.save_journal(journal)
            
            return jsonify({'success': True, 'message': 'Daily pages saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/daily-pages/skip', methods=['POST', 'OPTIONS'])
    def skip_daily_pages():
        """Log a skip for daily pages."""
        if request.method == 'OPTIONS':
            return '', 204
        try:
            data = request.get_json()
            reason = data.get('reason', '').strip()
            word_count = data.get('word_count', 0)
            
            if not reason:
                return jsonify({'error': 'Reason is required'}), 400
            
            # Use daily_pages_editor to log skip
            from daily_pages import daily_pages_editor
            daily_pages_editor.log_skip(reason, word_count)
            
            return jsonify({'success': True, 'message': 'Skip logged'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Notes endpoints
    
    @app.route('/api/notes', methods=['POST', 'OPTIONS'])
    def create_note():
        """Create a new note."""
        if request.method == 'OPTIONS':
            return '', 204
        try:
            data = request.get_json()
            content = data.get('content', '').strip()
            project_id = data.get('project_id')
            
            if not content:
                return jsonify({'error': 'Content is required'}), 400
            
            # Save note to journal
            storage.add_note_to_journal(content, project_id=project_id)
            
            return jsonify({'success': True, 'message': 'Note saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Daily Log endpoint
    
    @app.route('/api/log', methods=['GET'])
    @app.route('/api/log/<date>', methods=['GET'])
    def get_daily_log(date=None):
        """Get comprehensive daily log view."""
        try:
            # Parse date
            if date:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                target_date = datetime.now()
            
            # Load journal
            journal = storage.load_journal(target_date)
            
            # Load tasks for this date
            all_tasks = storage.load_tasks()
            date_str = target_date.strftime("%Y-%m-%d")
            
            today_tasks = [t for t in all_tasks if t.due_date and t.due_date.strftime("%Y-%m-%d") == date_str and not t.completed]
            completed_tasks = [t for t in all_tasks if t.completed_at and t.completed_at.strftime("%Y-%m-%d") == date_str]
            
            return jsonify({
                'date': date_str,
                'intention': journal.get('intention'),
                'daily_pages': journal.get('daily_pages'),
                'morning': journal.get('morning'),
                'notes': journal.get('notes', []),
                'chat_history': journal.get('chat_history', []),
                'tasks': {
                    'today': [task_to_dict(t) for t in today_tasks],
                    'completed': [task_to_dict(t) for t in completed_tasks]
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Projects endpoints
    
    @app.route('/api/projects')
    def get_projects():
        """Get all projects with task/note counts."""
        projects = storage.load_projects()
        
        projects_data = []
        for project in projects:
            # Get task count
            project_tasks = project_manager.get_project_tasks(project.id)
            
            # Get note count
            project_notes = project_manager.get_project_notes(project.id)
            
            # Get last activity
            last_activity = get_project_last_activity(project.id)
            
            projects_data.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'color': project.color,
                'task_count': len(project_tasks),
                'note_count': len(project_notes),
                'last_activity': last_activity.isoformat() if last_activity else None
            })
        
        # Sort by last activity
        projects_data.sort(key=lambda p: p['last_activity'] or '', reverse=True)
        
        return jsonify({'projects': projects_data})
    
    @app.route('/api/projects/<project_id>')
    def get_project(project_id):
        """Get detailed project data including tasks and notes."""
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get tasks
        all_tasks = storage.load_tasks()
        project_tasks = [t for t in all_tasks if t.project_id == project_id]
        tasks_data = [task_to_dict(t) for t in project_tasks]
        
        # Get notes
        project_notes = project_manager.get_project_notes(project_id)
        
        return jsonify({
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'color': project.color
            },
            'tasks': tasks_data,
            'notes': project_notes
        })
    
    # Lists endpoints
    
    @app.route('/api/lists')
    def get_lists():
        """Get all lists."""
        from lists import list_manager
        
        lists = list_manager.get_all_lists()
        lists_data = []
        
        for lst in lists:
            items = list_manager.get_list_items(lst.name)
            lists_data.append({
                'id': lst.id,
                'name': lst.name,
                'description': lst.description,
                'category': lst.category,
                'created_at': lst.created_at.isoformat(),
                'updated_at': lst.updated_at.isoformat(),
                'item_count': len(items)
            })
        
        return jsonify({'lists': lists_data})
    
    @app.route('/api/lists/<list_id>')
    def get_list(list_id):
        """Get a specific list with its items."""
        from lists import list_manager
        
        lst = list_manager.get_list_by_id(list_id)
        if not lst:
            return jsonify({'error': 'List not found'}), 404
        
        items = list_manager.get_list_items(lst.name)
        items_data = []
        
        for item in items:
            items_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'metadata': item.metadata,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat()
            })
        
        return jsonify({
            'list': {
                'id': lst.id,
                'name': lst.name,
                'description': lst.description,
                'category': lst.category,
                'created_at': lst.created_at.isoformat(),
                'updated_at': lst.updated_at.isoformat()
            },
            'items': items_data
        })
    
    @app.route('/api/lists', methods=['POST', 'OPTIONS'])
    def create_list():
        """Create a new list."""
        if request.method == 'OPTIONS':
            return '', 204
        
        from lists import list_manager
        
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            category = data.get('category', 'general').strip()
            
            if not name:
                return jsonify({'error': 'List name is required'}), 400
            
            lst = list_manager.create_list(name, description, category)
            
            return jsonify({
                'list': {
                    'id': lst.id,
                    'name': lst.name,
                    'description': lst.description,
                    'category': lst.category,
                    'created_at': lst.created_at.isoformat(),
                    'updated_at': lst.updated_at.isoformat()
                }
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/lists/<list_id>/items', methods=['POST', 'OPTIONS'])
    def add_list_item(list_id):
        """Add an item to a list."""
        if request.method == 'OPTIONS':
            return '', 204
        
        from lists import list_manager
        
        try:
            lst = list_manager.get_list_by_id(list_id)
            if not lst:
                return jsonify({'error': 'List not found'}), 404
            
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            metadata = data.get('metadata', {})
            
            if not title:
                return jsonify({'error': 'Item title is required'}), 400
            
            item = list_manager.add_item(
                list_name=lst.name,
                title=title,
                description=description,
                metadata=metadata,
                auto_create_list=False
            )
            
            return jsonify({
                'item': {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'metadata': item.metadata,
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat()
                }
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/lists/items/<item_id>', methods=['PUT', 'OPTIONS'])
    def update_list_item(item_id):
        """Update a list item."""
        if request.method == 'OPTIONS':
            return '', 204
        
        from lists import list_manager
        
        try:
            data = request.get_json()
            
            # Build update dict from provided fields
            updates = {}
            if 'title' in data:
                updates['title'] = data['title'].strip()
            if 'description' in data:
                updates['description'] = data['description'].strip()
            if 'metadata' in data:
                updates['metadata'] = data['metadata']
            
            if not updates:
                return jsonify({'error': 'No fields to update'}), 400
            
            item = list_manager.update_item(item_id, **updates)
            
            if not item:
                return jsonify({'error': 'Item not found'}), 404
            
            return jsonify({
                'item': {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'metadata': item.metadata,
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat()
                }
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/lists/items/<item_id>', methods=['DELETE', 'OPTIONS'])
    def delete_list_item(item_id):
        """Delete a list item."""
        if request.method == 'OPTIONS':
            return '', 204
        
        from lists import list_manager
        
        try:
            success = list_manager.delete_item(item_id)
            
            if not success:
                return jsonify({'error': 'Item not found'}), 404
            
            return jsonify({'success': True})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app


def task_to_dict(task):
    """Convert a Task object to a dictionary."""
    return {
        'id': task.id,
        'text': task.text,
        'completed': task.completed,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
        'created_at': task.created_at.isoformat(),
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'project_id': task.project_id
    }


def get_project_last_activity(project_id):
    """Get the timestamp of most recent activity for a project."""
    latest = None
    
    # Check tasks
    tasks = storage.load_tasks()
    project_tasks = [t for t in tasks if t.project_id == project_id]
    if project_tasks:
        task_dates = [t.updated_at for t in project_tasks if t.updated_at]
        if task_dates:
            latest = max(task_dates) if not latest else max(latest, max(task_dates))
    
    # Check notes
    project_notes = project_manager.get_project_notes(project_id)
    if project_notes:
        for note in project_notes:
            try:
                note_date = datetime.strptime(note['date'], "%Y-%m-%d")
                latest = note_date if not latest else max(latest, note_date)
            except:
                pass
    
    return latest


def start_api_server(port=5555):
    """Start the API server."""
    app = create_app()
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    
    print(f"\n🚀 API Server starting on http://localhost:{port}")
    print(f"   React app should be running on http://localhost:5173\n")
    
    try:
        app.run(host='localhost', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n✓ API server stopped")


if __name__ == '__main__':
    start_api_server()

