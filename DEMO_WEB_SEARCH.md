# Web Search Demo

## Quick Demo: How It Works

> **Note**: Install w3m for the best experience: `brew install w3m` (macOS) or `sudo apt install w3m` (Linux)
> This allows you to view search results in the terminal without switching to a browser.

### 1. Basic Web Search

```bash
> /search web python tutorials
```

**Output:**
```
────────────────────────────────────────────────────────────────────────────
> /search web python tutorials
────────────────────────────────────────────────────────────────────────────

🌐 Web Search Results for: python tutorials

Use ↑/↓ arrows to navigate, Enter to open in browser, Esc to cancel

→ Python Tutorial
  Learn Python - Free Interactive Python Tutorial
  The Python Tutorial — Python 3.14.0 documentation
  Python Tutorial
  Algorithms Tutorials – Real Python
  
[User presses ↓ twice, then Enter]

Opening: The Python Tutorial — Python 3.14.0 documentation
https://docs.python.org/3/tutorial/index.html

[Page opens in w3m terminal browser - user can read documentation without leaving terminal]
[Press 'q' to quit w3m and return to Focus Assistant]
```

### 2. Limited Results

```bash
> /search web latest AI news results:3
```

**Output:**
```
────────────────────────────────────────────────────────────────────────────
> /search web latest AI news results:3
────────────────────────────────────────────────────────────────────────────

🌐 Web Search Results for: latest AI news

Use ↑/↓ arrows to navigate, Enter to open in browser, Esc to cancel

→ Latest developments in artificial intelligence
  AI News Today - Breaking Stories
  The Future of AI - Latest Updates

[User selects first result]

Opening: Latest developments in artificial intelligence
https://example.com/ai-news

✓ Opened in browser
```

### 3. History Search (Local Data)

```bash
> /search history things to read
```

**Output:**
```
────────────────────────────────────────────────────────────────────────────
> /search history things to read
────────────────────────────────────────────────────────────────────────────

🔍 Search Results for: things to read

📔 Journal Entries

2024-11-20 • morning • 87% match
Need to read that article on productivity systems...

2024-11-15 • note • 82% match
Found an interesting book recommendation: "Deep Work"...

✓ Tasks

○ Read "Atomic Habits" by James Clear (75% match)
  Status: inbox

📁 Projects

• Reading List (91% match)
Curated list of books and articles to read

Found 4 total results
```

### 4. Default Behavior (Backward Compatible)

```bash
> /search project ideas
```

Automatically uses history search (searches local data, not the web).

## Visual Flow

```
┌─────────────────────────────────────────────┐
│  Focus Assistant Interactive Mode           │
└─────────────────────────────────────────────┘
              │
              ▼
    User types: /search web <query>
              │
              ▼
    ┌─────────────────────┐
    │ Query DuckDuckGo    │
    │ (max 10-25 results) │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Display results     │
    │ in pick interface   │
    └─────────────────────┘
              │
              ▼
    User navigates with ↑/↓
              │
              ▼
    User presses Enter
              │
              ▼
    ┌─────────────────────┐
    │ Open URL in browser │
    └─────────────────────┘
```

## Command Comparison

### Web Search (NEW)
- **Purpose**: Search the internet
- **Scope**: Entire web via DuckDuckGo
- **Command**: `/search web <query> [results:N]`
- **Output**: Clickable list of web results
- **Opens in**: Terminal browser (w3m/lynx/elinks) or system browser
- **Use case**: "Find latest tutorials", "Look up documentation"

### History Search (EXISTING)
- **Purpose**: Search your personal data
- **Scope**: Local notes, tasks, projects
- **Command**: `/search history <query>` or `/search <query>`
- **Output**: Relevant content from your journals
- **Use case**: "What did I say about X?", "Find notes on Y"

## Tips for Best Results

1. **Install Terminal Browser**: `brew install w3m` to stay in the terminal
2. **Be Specific**: `python web scraping tutorial` > `python`
3. **Limit Results**: Use `results:5` for quick lookups
4. **Use History for Personal Data**: Don't search web for your own notes
5. **Keyboard Navigation**: Arrow keys are faster than typing numbers
6. **w3m shortcuts**: Press `q` to quit, `Tab` to navigate links, `/` to search

## Common Use Cases

### Research
```bash
/search web machine learning algorithms results:8
```

### Quick Lookup
```bash
/search web python datetime format string results:3
```

### Documentation
```bash
/search web react hooks documentation
```

### News
```bash
/search web tech news today results:5
```

### Finding Your Notes
```bash
/search history machine learning notes
```

## Error Handling Examples

### No Results
```bash
> /search web asdfghjklzxcvbnm

No results found for 'asdfghjklzxcvbnm'
```

### Missing Dependency
```bash
> /search web python

ddgs library not installed.
Install it with: pip install ddgs
```

### Empty Query
```bash
> /search web

Usage: /search web <query> [results:N]
Example: /search web python tutorials results:5
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` | Move up in results list |
| `↓` | Move down in results list |
| `Enter` | Open selected result |
| `Esc` | Cancel without opening |

## Integration with Workflow

### Typical Session
```bash
> /morning                           # Start your day
> /tasks                            # Check what's on your plate
> /search web react best practices  # Research while working
> /note                             # Quick note about findings
> /search history react notes       # Review what you've learned
> /evening                          # Reflect on the day
```

### Research Workflow
```bash
# Search the web for information
> /search web quantum computing basics results:5

# Take notes after reading
> /note Just learned about qubits and superposition

# Later, find your notes
> /search history quantum computing
```

## Terminal Browser Benefits

Using w3m (or lynx/elinks) keeps you in your workflow:
- ✅ **Stay focused**: No context switching to GUI browser
- ✅ **Fast**: Instant startup, minimal resources
- ✅ **Keyboard-driven**: Navigate with vim-like shortcuts
- ✅ **Distraction-free**: Text-only, no ads or popups
- ✅ **Works over SSH**: Even on remote servers

### When to Use System Browser

For sites that need JavaScript or complex interactions:
- Interactive web apps
- Sites with heavy CSS layouts
- Video content
- Complex forms

If w3m doesn't render something well, just close it and re-run the search, then open in your system browser.

## Next Steps

1. **Install w3m**: `brew install w3m` or `sudo apt install w3m`
2. **Try it out**: `/search web your favorite topic`
3. **Adjust results**: Add `results:3` or `results:15`
4. **Compare**: Try `/search history` for local data
5. **Integrate**: Use in your daily workflow

---

**Requirements**: 
- `duckduckgo_search>=6.0.0,<7.0.0` (in requirements.txt)
- `pick>=2.2.0` (in requirements.txt) 
- `w3m` (recommended): `brew install w3m`

