# Changelog

## [0.2.0] - 2025-11-21 - Markdown Journal Storage

### 🎉 Major Changes

#### Markdown Journal Format
- **Journals now in Markdown**: All daily journals are now saved as `.md` files instead of `.json`
- **Obsidian-ready**: YAML frontmatter, clean formatting, wikilink support
- **Human-readable**: Open and read your journals in any text editor
- **Backward compatible**: Can still read old JSON journals

#### Migration Tool
- **`migrate_to_markdown.py`**: Converts existing JSON journals to Markdown
- Automatically archives original JSON files
- Verifies migration success
- Preserves all data and structure

#### /daily-note Command
- View your daily journal in beautifully formatted markdown
- Usage: `./focus daily-note` or `./focus daily-note 2025-11-20`
- Shows YAML frontmatter, morning reflection, chat history, and evening reflection
- Available in both command-line mode

#### Documentation
- **OBSIDIAN.md**: Complete integration guide for Obsidian users
- Updated README.md with Markdown storage info
- Updated QUICKSTART.md with new format details

### ✨ Features

- YAML frontmatter for queryable metadata (date, day, energy, tags)
- Timestamped chat history with clear user/assistant labels
- Beautiful formatting for morning/evening reflections
- Section markers for easy parsing
- Tag support for categorization

### 🔧 Technical Changes

- `storage.py`: New markdown writer and parser
- `_format_markdown_journal()`: Converts data to markdown
- `_parse_markdown_journal()`: Parses markdown back to structured data
- File extension changed from `.json` to `.md`
- Backward compatibility maintained for JSON files
- `main.py`: Added `daily-note` command

### 📝 Markdown Format Example

```markdown
---
date: 2025-11-21
day: Friday
energy: 8
tags: [daily, journal]
---

# Friday, November 21, 2025

## Morning Reflection
**Question**
Answer

## Chat History
### 12:06 PM
**You:** message
**Assistant:** response

## Evening Reflection
**Question**
Answer
```

### 🎯 Why This Matters

1. **Immediate Obsidian integration** - No waiting for future features
2. **Semantic search ready** - Clean text chunks for embeddings
3. **Human-first** - Your data is readable, not just machine-parseable
4. **Future-proof** - Markdown is universal and timeless

### 📦 What Stayed the Same

- Tasks remain in JSON format (better for programmatic access)
- All CLI commands work exactly the same
- Config file unchanged
- API integration unchanged
- Morning/evening routines unchanged

### 🚀 Next Steps

With markdown storage in place, semantic search becomes much easier:
- Parse markdown journals
- Generate embeddings
- Build RAG pipeline
- Search: "What did I say about grad school?"

---

## [0.1.0] - 2025-11-21 - MVP Release

### Initial Features

- Morning routine with 5 reflection questions
- AI-powered day planning
- Interactive chat interface
- Natural language task parsing
- Task management (today/upcoming/inbox)
- Evening reflection with stats
- Claude API integration
- Beautiful terminal UI with Rich
- Local JSON storage

