# Web Search Feature

## Overview

The Focus Assistant now includes a DuckDuckGo web search command that lets you search the web directly from the interactive interface, with arrow key navigation to browse results.

## Installation

### Python Dependencies

The required dependency is already in `requirements.txt`:

```bash
pip install duckduckgo_search>=6.0.0,<7.0.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Terminal Browser (Recommended)

For the best experience, install a terminal browser to view results without leaving the terminal:

**macOS:**
```bash
brew install w3m
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install w3m
```

**Linux (RHEL/CentOS/Fedora):**
```bash
sudo yum install w3m
```

If no terminal browser is installed, URLs will open in your system's default browser.

## Usage

### Basic Web Search

```bash
/search web <query>
```

This will search DuckDuckGo and return the first 10 results by default.

**Example:**
```bash
/search web python tutorials
```

### Custom Number of Results

You can specify how many results you want (max 25):

```bash
/search web <query> results:N
```

**Examples:**
```bash
/search web machine learning results:5
/search web best coffee in SF results:15
```

### History Search (Original Feature)

The original semantic search has been moved to:

```bash
/search history <query>
```

This searches your local notes, tasks, and projects.

**Example:**
```bash
/search history things to read
```

### Default Behavior

For backward compatibility, if you don't specify `web` or `history`, it defaults to history search:

```bash
/search grad school  # same as /search history grad school
```

## Features

### Terminal Browser Support

When you select a result, it opens in a terminal browser (w3m, lynx, or elinks) if available, keeping you in the terminal. If no terminal browser is installed, it falls back to your system's default browser.

**Supported terminal browsers (in order of preference):**
1. **w3m** (recommended) - Fast, feature-rich, excellent text rendering
2. **lynx** - Classic, reliable, widely available
3. **elinks** - Modern features, good Unicode support

### Arrow Key Navigation

After running a web search, you'll see a list of results that you can navigate with:
- **↑/↓ arrows**: Navigate through results
- **Enter**: Open the selected result in terminal browser (or system browser if not installed)
- **Esc**: Cancel without opening anything

### Result Display

Each result shows:
- Title (truncated to 80 characters if needed)
- Interactive selection interface

### Fallback Mode

If the `pick` library is not installed, the command falls back to numbered selection where you type the number of the result you want to open.

## Command Structure

The `/search` command now has three modes:

1. **Web Search**: `/search web <query> [results:N]`
   - Searches DuckDuckGo
   - Returns N results (default 10, max 25)
   - Arrow key navigation to select and open

2. **History Search**: `/search history <query>`
   - Semantic search of your local data
   - Searches notes, tasks, projects
   - Returns relevant matches with similarity scores

3. **Legacy Mode**: `/search <query>`
   - Defaults to history search
   - Maintains backward compatibility

## Implementation Details

### Dependencies

- `ddgs>=9.8.0` - DuckDuckGo search library (renamed from duckduckgo-search)
- `pick>=2.2.0` - Arrow key navigation (already installed)
- `webbrowser` - Standard library for opening URLs

### Code Location

All search functionality is in `interactive.py`:
- `cmd_search_router()` - Routes between web and history search
- `cmd_search_web()` - Implements DuckDuckGo search with arrow navigation
- `cmd_search_history()` - Original semantic search (renamed from cmd_search)

### Error Handling

The implementation includes graceful error handling for:
- Missing dependencies (shows install instructions)
- No search results (clear message)
- Invalid selections (error message)
- Network issues (exception caught and displayed)

## Examples

### Quick Web Search
```bash
> /search web rust programming
```

Returns ~10 results, navigate with arrows, press Enter to open in browser.

### Limited Results
```bash
> /search web latest AI news results:3
```

Returns only 3 results for a quick glance.

### Search Your History
```bash
> /search history project ideas
```

Searches your local notes and tasks for "project ideas" with semantic matching.

## ⚠️ Important: DuckDuckGo Rate Limits

**DuckDuckGo aggressively rate limits automated searches.** You may encounter rate limits after just 2-3 searches.

### Why This Happens

- DuckDuckGo detects and limits automated requests to prevent abuse
- Even 2-3 searches in quick succession can trigger rate limiting
- Rate limits typically last 1-2 minutes

### What To Do

1. **Wait 1-2 minutes** between searches
2. **Use sparingly** - save web search for important lookups
3. **Use `/search history`** to search your local notes/tasks instead
4. **Alternative**: Open a regular browser for frequent web searches

### Automatic Retry

The command automatically retries up to 3 times with increasing delays. If it still fails:

```
⚠️  DuckDuckGo rate limit reached
DuckDuckGo limits automated searches. Try again in 1-2 minutes.
Tip: Use /search history to search your local notes instead.
```

## Tips

1. **Install w3m**: For the best experience, install w3m to view results in the terminal
2. **Be specific**: More specific queries return better results
3. **Use results parameter**: For quick lookups, use `results:3` or `results:5`
4. **Arrow keys**: Much faster than typing numbers
5. **Cancel anytime**: Press Esc if you change your mind
6. **Terminal browser shortcuts**: In w3m, press `q` to quit, `B` to go back, `/` to search
5. **Use history search**: `/search history` doesn't have rate limits

## w3m Keyboard Shortcuts

Once you've opened a result in w3m, here are essential shortcuts:

| Key | Action |
|-----|--------|
| `q` | Quit w3m |
| `B` | Back (previous page) |
| `Tab` | Next link |
| `Shift+Tab` | Previous link |
| `Enter` | Follow link |
| `/` | Search in page |
| `n` | Next search result |
| `Space` | Page down |
| `b` | Page up |
| `<` or `>` | Scroll horizontally |
| `H` | Help (full shortcut list) |

## Help

To see help in the interactive interface:

```bash
/help
```

The search commands are documented in the "Search & Projects" section.

