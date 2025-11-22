# Terminal Browser Setup for Web Search

## Overview

The Focus Assistant web search feature now opens results in a **terminal browser** (w3m, lynx, or elinks) when available, keeping you in your workflow without switching to a GUI browser.

## Why Terminal Browsers?

- ✅ **Stay in terminal**: No context switching
- ✅ **Fast**: Instant startup (<0.1s vs 5-10s for GUI browsers)
- ✅ **Lightweight**: ~5MB memory vs 100-200MB
- ✅ **Keyboard-driven**: Navigate with shortcuts
- ✅ **Distraction-free**: No ads, popups, or tracking
- ✅ **Works anywhere**: Even over SSH

## Installation

### macOS

```bash
brew install w3m
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install w3m
```

### Linux (RHEL/CentOS/Fedora)

```bash
sudo yum install w3m
```

### Alternative Browsers

If w3m isn't available, the assistant will try:
1. **lynx** - Classic, widely available
2. **elinks** - Modern features

Install alternatives:
```bash
# macOS
brew install lynx

# Linux
sudo apt install lynx
```

### Fallback

If no terminal browser is installed, results will open in your system's default browser automatically.

## Quick Start

1. **Install w3m** (see above)
2. **Search**: `/search web python tutorials`
3. **Select result**: Use arrow keys and press Enter
4. **Read in terminal**: Page opens in w3m
5. **Return to assistant**: Press `q` to quit w3m

## w3m Essential Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit (return to Focus Assistant) |
| `Tab` | Next link |
| `Shift+Tab` | Previous link |
| `Enter` | Follow link |
| `/` | Search in page |
| `n` | Next search result |
| `Space` | Page down |
| `b` | Page up |
| `B` | Back to previous page |
| `H` | Full help |

## Usage Flow

```bash
# In Focus Assistant interactive mode
> /search web rust programming

# Arrow keys to select result
→ The Rust Programming Language
  Learn Rust - Rust Programming Language
  Rust Book - Getting Started

# Press Enter - opens in w3m

[Reading documentation in w3m terminal browser]
[Press 'q' when done]

# Back in Focus Assistant
> /note Just learned about ownership in Rust
```

## When to Use System Browser

Terminal browsers work great for:
- ✅ Documentation (Python docs, MDN, etc.)
- ✅ Blog posts and articles
- ✅ Stack Overflow answers
- ✅ GitHub README files
- ✅ News articles

Use system browser for:
- ❌ Interactive web apps
- ❌ Sites requiring JavaScript
- ❌ Video content
- ❌ Complex forms
- ❌ Heavy CSS layouts

If w3m doesn't render well, just press `q` to quit and open in your regular browser.

## Tips

1. **Tab navigation**: Use `Tab` to jump between links quickly
2. **Search**: Press `/` to find text on the page
3. **Multiple tabs**: Open links in background with `Ctrl+t`
4. **Save page**: Press `S` to save HTML
5. **View source**: Press `\` to view page source
6. **Help**: Press `H` anytime for full shortcuts

## Troubleshooting

### w3m not found

```bash
# Check if installed
which w3m

# If not found, install it
brew install w3m  # macOS
sudo apt install w3m  # Linux
```

### Page doesn't render well

Some sites require JavaScript or have complex layouts. Just press `q` to quit w3m - the assistant will fall back to your system browser if you run the search again.

### Can't navigate

If you're stuck, press `q` to quit w3m and return to the assistant.

## Configuration (Optional)

Create `~/.w3m/config` for custom settings:

```
# Show tabs
display_link_number 1

# Color support
color 1

# Use external browser for some content
urimethodmap file:///usr/local/etc/w3m/urimethodmap
```

## Comparison: Terminal vs GUI Browser

| Feature | w3m | browsh | GUI Browser |
|---------|-----|--------|-------------|
| Startup | 0.1s | 5-10s | 1-2s |
| Memory | ~5MB | ~200MB | ~100MB |
| JavaScript | ❌ | ✅ | ✅ |
| Text quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Stay in terminal | ✅ | ✅ | ❌ |

## Further Reading

- [w3m Manual](http://w3m.sourceforge.net/MANUAL)
- [Lynx Documentation](https://lynx.invisible-island.net/)
- [Terminal Browser Comparison](https://en.wikipedia.org/wiki/Text-based_web_browser)

## Questions?

Type `/help` in the interactive assistant for more information about web search commands.

