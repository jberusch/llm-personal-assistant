#!/bin/bash
# Start both the API server and React dev server

echo "🚀 Starting Focus Assistant Web UI"
echo ""

# Start API server in background
echo "Starting API server on http://localhost:5555..."
python3 api_server.py &
API_PID=$!

# Give API server a moment to start
sleep 2

# Start React dev server
echo "Starting React app on http://localhost:5173..."
cd web
npm run dev

# Cleanup: kill API server when React dev server exits
kill $API_PID 2>/dev/null

