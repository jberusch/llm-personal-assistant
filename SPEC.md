# Focus Assistant - Product Specification

## Current Status: MVP Phase Complete ✅
**Last Updated:** 2024-11-21

The CLI-based MVP is functional and ready for daily use. Focus now on daemon conversion, web UI, and semantic search.

---

## Architecture Evolution

### Phase 1: CLI MVP (✅ COMPLETE)
**Current implementation** - Fully functional command-line tool

**What's Working:**
- `./focus morning` - 5-question morning routine with AI day planning
- `./focus chat` - Interactive conversation with context awareness
- `./focus add "task"` - Natural language task parsing
- `./focus tasks` - Task board (today/upcoming/inbox)
- `./focus done` - Mark tasks complete
- `./focus evening` - Evening reflection with stats
- `./focus config` - API key configuration

**Storage:**
- Local JSON in `~/.focus_assistant/`
- Schema designed for Supabase migration
- Full conversation history saved for future embeddings
- Tasks include metadata for project auto-detection

**Model:** Claude Sonnet 4.5 (`claude-sonnet-4-5`)

### Phase 2: Background Daemon (🔄 NEXT)
**Goal:** Always-running process accessible via global hotkey

**Technical Approach:**
```python
# Daemon architecture
core_daemon:
  description: "Always-running background process like Claude Code"
  interface: 
    - System-wide hotkey (Cmd+Shift+Space?) opens floating input
    - Natural language commands
    - Stays out of the way until summoned
    - Menu bar icon with quick actions
  
  implementation:
    - Use rumps (macOS menu bar app)
    - pynput for global hotkey detection
    - Floating window with PyQt6 or Tauri
    - Launch on startup via LaunchAgent
  
  commands:
    - "morning" → starts daily flow
    - "show tasks" → opens web UI to task view
    - "note" → opens web UI to markdown editor
    - "what did I say about [topic]" → semantic search + inline response
    - "remind me to [X] tomorrow" → saves task
    - "I'm feeling distracted" → coaching response
    - "actually, be more encouraging today" → adjusts tone
```

**Implementation Steps:**
1. Create daemon.py with rumps menu bar app
2. Add global hotkey listener (Cmd+Shift+Space)
3. Build floating input window (simple PyQt6)
4. Refactor existing CLI commands into daemon API
5. Create LaunchAgent plist for auto-start
---

## Natural Language Control System

### Personality Adjustment (🔄 PARTIAL)
**Current:** Basic personality prompt in config
**Next:** Real-time tone modification via chat

```python
personality_adjustment:
  # Real-time tone modification via chat
  examples:
    - "be pushier about my goals" → increases intervention frequency
    - "I need a gentler approach today" → softens reminders
    - "stop reminding me about exercise" → removes topic
    - "treat writing as my #1 priority" → reweights suggestions
  
  storage:
    # Maintains personality.json that evolves
    {
      "tone": "firm_but_kind",
      "intervention_frequency": "2_hours",
      "current_priorities": ["writing", "grad_school"],
      "avoid_topics": [],
      "encouragement_level": 7,
      "last_updated": "2024-11-21T10:30:00Z",
      "adjustments_history": []
    }
```

**Implementation TODO:**
- Add `personality.json` to storage layer
- Create `PersonalityManager` class to handle adjustments
- Parse personality adjustment intents from chat
- Update system prompt dynamically based on settings
- Store adjustment history for trend analysis
### Command Interface Flow (🔄 NEXT)

```python
# Always listening via global hotkey
class FocusAssistant:
    def parse_natural_command(self, text):
        """
        Routes to appropriate action:
        - Questions → search knowledge base (semantic search)
        - Commands → execute action (morning, tasks, etc.)
        - Statements → save to knowledge base
        - Emotional → adjust approach (personality tuning)
        
        Uses Claude to classify intent, then routes to handlers.
        """
        
    def contextual_response(self):
        """
        Knows what you're working on via:
        - Time since last interaction
        - Current time vs. your usual patterns
        - Recent emotional indicators from morning/evening entries
        - Active tasks and deadlines
        
        Uses this context to:
        - Suggest what to work on now
        - Detect procrastination patterns
        - Offer encouragement at low points
        """
```

**Current:** Manual command routing in CLI
**Next:** Intelligent intent classification + contextual awareness
---

## Token Optimization Strategy (📋 PLANNED)

### Local Cache & Embeddings
```yaml
local_cache:
  - Last 30 days of entries stored locally ✅ (already doing JSON storage)
  - Embeddings cached indefinitely (TODO: add embedding generation)
  - Common queries pre-computed (TODO: implement)
  - Only hit API for complex synthesis (TODO: implement query router)

embedding_strategy:
  - Use OpenAI text-embedding-3-small (cheaper, good quality)
  - Or sentence-transformers locally (free, slower)
  - Generate embeddings on:
    - Each chat message
    - Morning/evening reflections
    - Tasks with rich context
  - Store in Supabase with pgvector extension
```

### Smart Context via RAG
```yaml
smart_context:
  - Don't send full history every time ✅ (currently loads today's chat only)
  - Use RAG to find relevant chunks (TODO: implement semantic search)
  - Summarize old entries, keep recent verbose (TODO: implement)
  - "Memory compression" weekly (TODO: background job)
  
implementation:
  tools:
    - ChromaDB for local vector storage (or Supabase pgvector)
    - LangChain for RAG pipeline
    - Background job for weekly compression
  
  query_flow:
    1. User asks: "what did I say about grad school?"
    2. Generate query embedding
    3. Vector search finds top 10 relevant chunks
    4. Send only those chunks + question to Claude
    5. Claude synthesizes answer from context
```
---

## Interaction Examples (Target UX)

### Via Global Hotkey (Daemon Mode - Future)
```bash
[Cmd+Shift+Space opens floating input]

> I keep getting distracted by email
"I notice this is the third time this week. 
 Want to try time-boxing email to 2pm-3pm? 
 I can remind you if you open it outside that window."

> be less preachy
"Got it, I'll dial back the advice."
[Personality adjustment saved]

> show me everything about grad school
[Opens web UI with semantic search results + timeline]

> what's my main goal today?
"Finishing the product spec. You're 2 hours in, on track."
[Pulls from morning reflection]

> I'm overwhelmed
"Let's break this down. What's the smallest next step? 
 (Also, you felt this way last Tuesday and pushed through by taking a walk.)"
[Uses semantic search to find similar past situations]
```

### Via CLI (Current MVP)
```bash
# Morning routine
./focus morning
# Answers 5 questions, gets AI day plan

# Throughout the day
./focus chat
> remind me tomorrow to call mom
📝 I detected a task: "call mom"
   Due: tomorrow
Add this task? [y/n]: y
✓ Task added

# View tasks anytime
./focus tasks

# Evening reflection
./focus evening
```
---

## Web UI Components (📋 PLANNED)

### Technology Stack (Proposed)
- **Backend:** FastAPI (Python) - easy integration with existing code
- **Frontend:** Next.js + TypeScript + Tailwind
- **Real-time:** Supabase real-time subscriptions
- **Deployment:** Local-first (runs on localhost:3000), optional cloud deploy

### Views

#### 1. Task Board
```yaml
task_board:
  layout: Kanban-style columns (Today | Upcoming | Inbox | Done)
  features:
    - Drag to reprioritize
    - Click task → modal with:
      - Full details + edit
      - Related notes/conversations
      - History (created, modified, completed)
    - Filter by project (auto-detected)
    - Search tasks
    - Quick add via floating button
  
  data_flow:
    - Reads from ~/.focus_assistant/tasks.json (or Supabase)
    - WebSocket updates when CLI makes changes
    - Bidirectional sync
```

#### 2. Markdown Editor
```yaml
markdown_editor:
  layout: Split view (editor | preview)
  features:
    - Daily note auto-opened (YYYY-MM-DD.md)
    - Side panel shows related past notes (semantic search)
    - Inline search: [[topic]] shows preview tooltip
    - Wikilink support [[another note]]
    - Auto-save every 30s
    - Full markdown support + syntax highlighting
  
  integration:
    - Saved to ~/.focus_assistant/notes/
    - Indexed for semantic search
    - Can reference tasks: [[task:uuid]]
```

#### 3. Knowledge Graph (Advanced)
```yaml
knowledge_graph:
  visualization: Force-directed graph (d3.js or react-force-graph)
  features:
    - Visual clusters of your thoughts (topics auto-detected)
    - Timeline slider to see evolution
    - Click node → all mentions across journal/notes/tasks
    - Zoom/pan/filter by date range
    - Color-coded by topic/project
  
  data_source:
    - Embeddings clustered via UMAP/t-SNE
    - Connections = semantic similarity
    - Node size = frequency of mention
```

#### 4. Search Interface
```yaml
search:
  type: Semantic search (not just keyword)
  features:
    - Single search bar (like Spotlight)
    - Results grouped by type (tasks, notes, journal entries)
    - Shows context snippet with highlighting
    - Timeline view option
    - Export results as markdown
  
  examples:
    - "feeling overwhelmed" → finds all similar emotional states
    - "grad school decisions" → finds discussions across time
    - "writing goals" → tasks + notes + reflections
```
---

## Implementation Status

### MVP Phase - CLI (✅ COMPLETE)
- [x] Morning routine with 5 reflection questions
- [x] AI-powered day planning using morning context
- [x] Interactive chat interface
- [x] Natural language task parsing ("remind me tomorrow to...")
- [x] Task management (add, view, complete)
- [x] Task categorization (today, upcoming, inbox)
- [x] Evening reflection with stats
- [x] Local JSON storage with future-proof schema
- [x] Full conversation history saved
- [x] Context-aware AI (remembers morning goals + tasks)
- [x] API key configuration
- [x] Beautiful terminal UI with Rich

**Files Created:**
- `main.py` - CLI entry point
- `assistant.py` - Claude API integration
- `chat.py` - Interactive chat interface
- `tasks.py` - Task management with NLP
- `routines.py` - Morning/evening flows
- `storage.py` - Data persistence layer
- `config.py` - Configuration management
- `focus` - Executable script
- `requirements.txt`, `setup.py`, `README.md`, `QUICKSTART.md`

### Phase 2 - Daemon + Web UI (🔄 NEXT)
- [ ] Background daemon process
- [ ] Global hotkey listener (Cmd+Shift+Space)
- [ ] Menu bar app (macOS)
- [ ] Floating input window
- [ ] LaunchAgent for auto-start
- [ ] FastAPI backend server
- [ ] Web UI - Task board
- [ ] Web UI - Markdown editor
- [ ] WebSocket for real-time sync

### Phase 3 - Semantic Search (📋 PLANNED)
- [ ] Generate embeddings for all content
- [ ] Set up vector database (ChromaDB or Supabase pgvector)
- [ ] Implement semantic search
- [ ] RAG pipeline for "what did I say about X?" queries
- [ ] Related notes suggestions
- [ ] Project auto-detection from language patterns

### Phase 4 - Advanced Features (📋 PLANNED)
- [ ] Personality adjustment system
- [ ] Proactive check-ins based on time patterns
- [ ] Knowledge graph visualization
- [ ] Weekly compression/summarization
- [ ] Pattern detection (procrastination, energy levels)
- [ ] Supabase migration for cloud sync

### V1 - Enhancement Features
- [ ] Voice input option
- [ ] Calendar integration
- [ ] Auto-generated user profile
- [ ] Mobile companion app
- [ ] Export/import data

### V2 - Agent Features
- [ ] Email drafting agent
- [ ] Code/document starter agent
- [ ] Research agent (web scraping)
- [ ] Weekly insights email
- [ ] Goal tracking and progress reports

---

## Implementation Timeline

### Completed (Week 0)
✅ CLI MVP fully functional
✅ All core commands working
✅ Data storage architecture in place

### Week 1: Daemon Foundation
- [ ] Create daemon.py with rumps
- [ ] Implement global hotkey
- [ ] Build floating input UI (PyQt6)
- [ ] Refactor CLI commands into daemon API
- [ ] Test background process

### Week 2: Web UI - Tasks
- [ ] Set up FastAPI backend
- [ ] Create Next.js frontend
- [ ] Build task board view
- [ ] Implement drag-and-drop
- [ ] Add task CRUD operations via web
- [ ] WebSocket updates

### Week 3: Web UI - Notes + Search
- [ ] Markdown editor component
- [ ] Daily notes auto-creation
- [ ] Basic text search
- [ ] Integration with daemon

### Week 4: Semantic Search
- [ ] Add sentence-transformers or OpenAI embeddings
- [ ] Generate embeddings for existing data
- [ ] Set up vector store
- [ ] Implement RAG query pipeline
- [ ] Build search interface

### Week 5: Polish + Deploy
- [ ] Personality adjustment system
- [ ] Pattern detection
- [ ] Performance optimization
- [ ] Documentation
- [ ] User testing

---

## Data Architecture

### Current Storage (MVP)
```
~/.focus_assistant/
├── config.json              # API key, preferences
├── tasks.json               # All tasks with metadata
└── journal/
    └── YYYY-MM-DD.json      # Daily entries (morning, evening, chat)
```

**Task Schema:**
```json
{
  "id": "uuid",
  "text": "task description",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "due_date": "ISO timestamp or null",
  "completed": false,
  "completed_at": "ISO timestamp or null",
  "status": "inbox|today|someday|completed",
  "project_hints": []  // For future auto-detection
}
```

**Journal Entry Schema:**
```json
{
  "id": "uuid",
  "date": "YYYY-MM-DD",
  "entry_type": "morning|evening|chat",
  "timestamp": "ISO timestamp",
  "question": "optional",
  "response": "full text content",
  "metadata": {
    "role": "user|assistant",
    "energy_level": 7,
    "detected_topics": [],
    "sentiment": 0.3
  }
}
```

### Future: Supabase Schema
```sql
-- Tables for cloud sync
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  due_date TIMESTAMP,
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  status TEXT CHECK (status IN ('inbox', 'today', 'someday', 'completed')),
  project_hints TEXT[],
  embedding VECTOR(1536)  -- pgvector for semantic search
);

CREATE TABLE journal_entries (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  entry_type TEXT CHECK (entry_type IN ('morning', 'evening', 'chat')),
  timestamp TIMESTAMP DEFAULT NOW(),
  question TEXT,
  response TEXT NOT NULL,
  metadata JSONB,
  embedding VECTOR(1536)  -- pgvector for semantic search
);

CREATE TABLE personality_settings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  tone TEXT DEFAULT 'firm_but_kind',
  intervention_frequency INTERVAL DEFAULT '2 hours',
  current_priorities TEXT[],
  avoid_topics TEXT[],
  encouragement_level INTEGER CHECK (encouragement_level BETWEEN 1 AND 10),
  settings JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_journal_user_date ON journal_entries(user_id, date);
CREATE INDEX idx_journal_embedding ON journal_entries USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_tasks_embedding ON tasks USING ivfflat (embedding vector_cosine_ops);
```

### Migration Strategy (JSON → Supabase)
```python
# migration.py
class DataMigration:
    def migrate_to_supabase(self):
        """
        1. Read all local JSON files
        2. Generate embeddings for existing content
        3. Upload to Supabase
        4. Verify data integrity
        5. Switch config to use Supabase
        6. Keep local backup
        """
        pass
    
    def bidirectional_sync(self):
        """
        Keep local + cloud in sync:
        - Local changes → push to Supabase
        - Cloud changes → pull to local
        - Conflict resolution (last-write-wins)
        """
        pass
```

---

## Key Technical Decisions

### Why These Tools?

**Claude Sonnet 4.5**
- Best-in-class reasoning for coaching/advice
- Long context window (200k tokens)
- Good at JSON parsing for task extraction
- Conversational and empathetic

**Local-First Architecture**
- Privacy: your journal stays on your machine
- Speed: instant access, no latency
- Works offline
- Optional cloud sync when ready

**Python + CLI → Daemon**
- Quick MVP validation with CLI
- Easy to refactor into daemon
- Rich ecosystem (rumps, pynput, PyQt6)
- Same codebase for CLI and daemon

**Next.js + FastAPI**
- Next.js: Modern, fast, great DX
- FastAPI: Python backend integrates with existing code
- Both have excellent WebSocket support
- Easy to deploy locally or to cloud

**pgvector (Supabase)**
- PostgreSQL with vector extension
- Handles both relational + embeddings
- Built-in real-time subscriptions
- Generous free tier

### Alternative Considered

**LLM Providers:**
- ❌ GPT-4: More expensive, less conversational
- ❌ Local (Ollama): Too slow for real-time chat
- ✅ Claude: Best balance

**Vector Stores:**
- ChromaDB: Good for local-only
- Pinecone: Expensive, overkill
- ✅ Supabase pgvector: Best for hybrid local/cloud

**UI Framework:**
- Electron: Too heavy
- Tauri: Rust learning curve
- ✅ PyQt6: Lightweight, native feel

---

## Privacy & Security

### Data Principles
1. **Local-first:** All data stored locally by default
2. **Opt-in sync:** Cloud sync is optional
3. **Encryption:** Local data encrypted at rest (future)
4. **API keys:** Never logged or transmitted except to Anthropic
5. **Export:** Easy full data export at any time

### What Gets Sent to Claude?
- User's messages
- System prompt with today's context
- Recent conversation history (not full history)
- Task summaries (not full task list)

**What's NOT sent:**
- Full journal archive
- Previous days' detailed entries
- Any data marked as private

---

## Future Extensions

### Integrations (V2+)
```yaml
calendar:
  - Sync tasks with Apple Calendar/Google Calendar
  - Auto-create tasks from calendar events
  - Block focus time based on priorities

email:
  - Draft responses based on your communication style
  - Auto-reply to common questions
  - Extract action items → tasks

code_editor:
  - VS Code extension
  - Inline task creation from TODOs
  - Commit message suggestions based on your style

browser:
  - Chrome extension for distraction monitoring
  - Save interesting links with context
  - Block sites during focus time
```

### Advanced AI Features
```yaml
pattern_detection:
  - "You're most productive 9-11am"
  - "Writing tasks take 2x longer than you estimate"
  - "You avoid emails when stressed"

proactive_suggestions:
  - "It's 9am, your peak time. Start with the hard task?"
  - "You haven't checked in on Project X in 3 days"
  - "Similar to last Tuesday when you took a walk?"

auto_journaling:
  - Summarize your day automatically
  - Extract insights from patterns
  - Generate weekly/monthly reviews
```

---

## Success Metrics

### User Engagement
- Daily active usage (morning + evening routine)
- Average chat messages per day
- Task completion rate
- Time to first action each morning

### User Outcomes
- Self-reported stress levels (morning reflection)
- Goal completion rate
- Distraction frequency (when monitoring added)
- User retention (still using after 30 days)

### Technical Performance
- API response time < 2s
- Semantic search results < 500ms
- UI interaction latency < 100ms
- Sync conflicts < 0.1%

---

## Open Questions & Decisions Needed

1. **Embedding provider:** OpenAI or local sentence-transformers?
2. **Web UI hosting:** Local-only or optional cloud deploy?
3. **Multi-device sync:** Priority for V1 or wait?
4. **Voice input:** Worth the complexity in V1?
5. **Mobile app:** Native or PWA?

---

**Document Maintenance:**
- Update this file whenever implementing new features
- Mark items complete with ✅
- Add new sections as architecture evolves
- Keep timeline realistic and updated