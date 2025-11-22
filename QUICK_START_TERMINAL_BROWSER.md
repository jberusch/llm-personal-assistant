# Quick Start: Terminal Browser for Web Search

## Install w3m (One Command!)

```bash
# macOS
brew install w3m

# Linux (Debian/Ubuntu)
sudo apt install w3m
```

## Try It Out

```bash
# Start Focus Assistant
python main.py

# Or in interactive mode
python interactive.py

# Search the web
> /search web python tutorials

# Use arrow keys to select a result, press Enter
# Page opens in w3m - read without leaving terminal!
# Press 'q' to quit w3m and return to assistant
```

## Essential w3m Shortcuts

- `q` - Quit and return to assistant
- `Tab` - Next link
- `Enter` - Follow link
- `/` - Search in page
- `Space` - Page down
- `b` - Page up
- `H` - Full help

## No w3m? No Problem!

If w3m isn't installed, results will automatically open in your regular browser (Chrome, Firefox, Safari, etc.). The feature works either way!

## More Info

- See `TERMINAL_BROWSER_SETUP.md` for detailed setup
- See `WEB_SEARCH_FEATURE.md` for full feature documentation
- See `DEMO_WEB_SEARCH.md` for usage examples

