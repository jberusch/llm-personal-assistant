# Embeddings and Projects Setup Guide

This guide will help you set up the new semantic search and project management features.

## Prerequisites

You need two API keys:
1. **Anthropic API Key** - For the Claude assistant (already configured if you're using the app)
2. **OpenAI API Key** - For embeddings and semantic search (new requirement)

## Installation Steps

### 1. Install New Dependencies

```bash
cd /Users/joe/llm-personal-assistant
pip install -r requirements.txt
```

This will install:
- `openai>=1.0.0` - For generating text embeddings
- `chromadb>=0.4.0` - Local vector database for semantic search
- `tiktoken>=0.5.0` - Token counting for embeddings

### 2. Configure OpenAI API Key

Get your OpenAI API key from: https://platform.openai.com/api-keys

Then configure it:

```bash
# Option 1: Interactive configuration
./focus config

# Option 2: Direct command
./focus config --openai-key YOUR_OPENAI_API_KEY

# Option 3: Environment variable
export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

### 3. Index Existing Data

Run this command once to generate embeddings for all your existing journals and tasks:

```bash
./focus index
```

This will:
- Parse all your journal markdown files
- Generate embeddings for morning/evening reflections
- Generate embeddings for chat history
- Generate embeddings for all tasks
- Generate embeddings for all projects

The indexing process may take a few minutes depending on how much data you have.

## New Features

### 1. Semantic Search (`/search`)

Search across all your notes, tasks, and projects using natural language.

**Usage in Chat:**

```bash
./focus chat

> /search things I should read
> /search grad school decisions
> /search feeling overwhelmed
```

The search understands meaning, not just keywords. For example:
- Searching "things to read" will find mentions of "books", "articles", "papers", etc.
- Searching "feeling stressed" will find related emotions like "anxious", "overwhelmed", etc.

**What Gets Searched:**
- Journal entries (morning reflections, evening reflections, chat history)
- Tasks (active and completed)
- Projects (name and description)

### 2. Project Management

Projects help you organize related tasks. When you create a task, the system suggests relevant projects based on semantic similarity.

**Creating Projects:**

Projects are created automatically when you add tasks:

```bash
# Via CLI
./focus add "Write thesis introduction"

# The system will ask:
# "No projects yet. Would you like to create one for this task?"
# or show suggestions like:
# "Suggested projects:
#   1. Thesis - PhD dissertation work
#   2. Writing - All writing tasks
#   3. Create new project
#   n. No project"
```

**Viewing Projects:**

```bash
# In chat
./focus chat
> /projects

# Or programmatically
python3 -c "from storage import storage; print([p.name for p in storage.load_projects()])"
```

### 3. Auto-Embedding

New content is automatically embedded:
- When you add a task → embedding is generated immediately
- When you complete morning routine → morning reflection is embedded
- When you chat → user messages are embedded
- When you complete evening routine → evening reflection is embedded

This means search results are always up-to-date without running `./focus index` again.

## How It Works

### Embeddings

Embeddings are mathematical representations of text that capture semantic meaning. Similar concepts have similar embeddings, allowing the system to find related content even if the exact words don't match.

- **Model:** OpenAI's `text-embedding-3-small` (1536 dimensions)
- **Cost:** ~$0.02 per 1M tokens (very cheap)
- **Storage:** Local ChromaDB in `~/.focus_assistant/embeddings/`

### Project Suggestions

When you add a task:
1. The task text is converted to an embedding
2. The system searches for similar project embeddings
3. Top 3 most similar projects are suggested
4. You can choose one, create a new project, or skip

This means as you use the system, it gets better at suggesting the right projects for new tasks.

## Cost Estimates

### One-time Indexing
- 100 journal entries × 200 words = ~$0.002
- 50 tasks × 20 words = ~$0.0001
- 10 projects × 50 words = ~$0.00005
- **Total: Less than $0.01 for initial setup**

### Ongoing Usage
- Each task added: ~$0.00001
- Each journal entry: ~$0.0001
- Each search query: ~$0.00001
- **Estimated monthly cost: $0.05 - $0.20** (depends on usage)

## Troubleshooting

### "OpenAI API key not configured"
- Run `./focus config --openai-key YOUR_KEY`
- Or set `OPENAI_API_KEY` environment variable

### "No results found" when searching
- Make sure you ran `./focus index` to index existing data
- New content should be automatically indexed, but check that your API key is configured

### "No module named 'chromadb'"
- Run `pip install -r requirements.txt` to install dependencies

### Embeddings not working
- Check that API key is set: `./focus config`
- Try running `./focus index` again
- Check `~/.focus_assistant/embeddings/` exists and has write permissions

## Privacy & Data

- **All embeddings are stored locally** in `~/.focus_assistant/embeddings/`
- **Your data never leaves your machine** except to generate embeddings via OpenAI API
- **OpenAI's policy:** Embeddings API does not use your data for training
- **ChromaDB:** Fully local, no cloud component

## Examples

### Example 1: Finding Reading Material

```bash
./focus chat
> /search things I should read

# Results might include:
# - Journal entry where you mentioned a book recommendation
# - Task "Read 'Deep Work' by Cal Newport"
# - Chat message about an article you wanted to save
```

### Example 2: Reviewing Past Decisions

```bash
./focus chat
> /search decisions about grad school

# Results might include:
# - Morning reflections where you weighed pros/cons
# - Evening reflections about meetings with advisors
# - Tasks related to application deadlines
```

### Example 3: Project Organization

```bash
./focus add "Outline chapter 3"

# System suggests:
# 1. Thesis - PhD dissertation work (similarity: 0.92)
# 2. Writing - All writing tasks (similarity: 0.78)
# 3. Create new project
# n. No project

# Choose option 1 to assign to "Thesis" project
```

## Next Steps

After setup, you can:
1. Try searching your existing data: `./focus chat` → `/search [query]`
2. Add a task and see project suggestions: `./focus add "your task"`
3. View your projects: `./focus chat` → `/projects`
4. Continue using the assistant normally - all new content is automatically embedded

---

**Questions or issues?** Check the main [README.md](README.md) or [SPEC.md](SPEC.md) for more information.

