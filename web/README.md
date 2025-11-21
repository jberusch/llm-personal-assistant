# Focus Assistant Web UI

React frontend for Focus Assistant.

## Development

```bash
# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The app will run on http://localhost:5173

## API Server

The web UI needs the Flask API server running. From the parent directory:

```bash
python3 api_server.py
```

The API server runs on http://localhost:5555

## Routes

- `/tasks` - Tasks board with checkboxes
- `/projects` - Projects list
- `/projects/:id` - Project detail view
