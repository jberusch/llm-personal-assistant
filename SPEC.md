# LLM Personal Assistant MVP

## Architecture Overview

Build a Python CLI app with these core modules:

- `main.py` - CLI entry point using Click
- `assistant.py` - Claude API integration and conversation management
- `tasks.py` - Task management with natural language parsing
- `routines.py` - Morning/evening routine flows
- `storage.py` - Data layer (JSON now, designed for Supabase later)
- `config.py` - Configuration and API key management

## Data Storage Strategy

Local JSON files in `~/.focus_assistant/`:

- `tasks.json` - All tasks with metadata (date, priority, project hints)
- `journal/YYYY-MM-DD.json` - Daily entries (morning + evening + chat history)
- `config.json` - API key and user preferences

**Design considerations for future migration:**

- Structure JSON to mirror future Supabase schema
- Include `id`, `created_at`, `updated_at` fields
- Save full conversation history for future embedding generation
- Use consistent field names that pgvector will expect

## Core Features

### 1. Morning Routine (`focus morning`)

Interactive flow with these questions:

1. How did you sleep? Energy level (1-10)?
2. How are you feeling going into today?
3. What's THE one thing that would make today a success?
4. What are you avoiding that needs attention?
5. What would bring joy/meaning today?

After Q&A, show existing tasks and help prioritize the day using Claude to synthesize responses into an actionable plan.

### 2. Task Management

- `focus add "task text"` - Quick add with natural language date parsing
  - "remind me tomorrow to pay rent" → task for tomorrow
  - "call mom next week" → task for next Monday
- `focus tasks` - Show beautiful task board (today, upcoming, inbox)
- Tasks stored with metadata for future project auto-detection

### 3. Chat Interface (`focus chat`)

Primary interaction mode:

- Continuous conversation with context from morning routine
- Seamlessly add tasks: "remind me to do X" automatically creates task
- Ask questions: "what should I focus on?" gets prioritized suggestions
- Type `tasks` to see task board without leaving chat
- Type `done` or `/quit` to exit
- Claude remembers morning goals and gently reminds when relevant

### 4. Evening Review (`focus evening`)

Reflection questions:

1. What did you accomplish today?
2. What got in your way?
3. How do you feel about the day?
4. What's one thing for tomorrow?

Saves to journal with task completion stats.

## Technical Implementation

### Dependencies

```
anthropic>=0.18.0
click>=8.1.0
rich>=13.7.0
python-dateutil>=2.8.0
pydantic>=2.5.0
```

### Claude Integration

- Use Claude 3.5 Sonnet for natural language understanding
- System prompt: "You are a focused productivity coach. Be firm but kind. Remember the user's daily goals and gently challenge distractions."
- Maintain conversation context within each session
- Parse task creation intents from natural conversation

### CLI Structure

```
focus morning          # Start day routine
focus chat            # Open chat session
focus add "text"      # Quick task add
focus tasks           # View task board
focus evening         # End day review
focus config          # Set API key
```

## Future-Proofing

Code structure to support easy addition of:

- **Embeddings**: Save full message text in separate field for future embedding
- **Supabase migration**: Storage layer is abstracted, swap JSON for Supabase client
- **Web UI**: API-like methods in storage layer for future FastAPI backend
- **Semantic search**: Include message metadata (timestamp, type, topics) from day one

## Key User Experience

The workflow should feel natural:

1. Morning: Have conversation about the day → get clarity and plan
2. Throughout day: Pop into chat for quick task adds or priority checks
3. Evening: Reflect and prep tomorrow

Chat is the primary interface - tasks flow naturally from conversation rather than feeling like separate todo list management.