# Google Custom Search API Implementation

## Overview

Successfully implemented Google Custom Search API as the primary web search engine, with DuckDuckGo as a fallback. This solves the aggressive rate limiting issues with DuckDuckGo.

## Benefits

✅ **100 free searches/day** (vs DuckDuckGo's ~2-3)  
✅ **Better search quality** (Google's algorithm)  
✅ **More reliable** (no aggressive rate limiting)  
✅ **Automatic fallback** (DuckDuckGo if not configured)  
✅ **Easy setup** (~5 minutes)

---

## Files Created

### 1. `google_search.py`
New module for Google Custom Search API integration.

**Key Components:**
- `GoogleSearchClient` class - Handles API requests
- `search()` method - Performs searches and returns formatted results
- Error handling for quota limits, auth failures, etc.
- Singleton pattern for client instance

**Features:**
- Formats results to match DuckDuckGo format (for consistency)
- Handles up to 10 results per request (Google CSE API limit)
- Comprehensive error messages

### 2. `GOOGLE_SEARCH_SETUP.md`
Detailed setup guide with:
- Step-by-step instructions
- Screenshots references
- Troubleshooting section
- Comparison table (Google vs DuckDuckGo)
- Security best practices

---

## Files Modified

### 1. `config.py`

**Added:**
```python
# New config keys
"google_search_api_key": None
"google_search_cx_id": None

# New methods
get_google_search_key() -> Optional[str]
set_google_search_key(api_key: str)
get_google_search_cx() -> Optional[str]
set_google_search_cx(cx_id: str)
```

**Supports:**
- Configuration file storage
- Environment variable fallback (`GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_CX_ID`)

### 2. `interactive.py`

**Added:**
- `_search_with_google()` method - Handles Google Search with arrow key navigation
- Updated `cmd_search_web()` - Checks for Google config first, falls back to DuckDuckGo
- Enhanced `cmd_config()` - Interactive setup for Google Search

**Flow:**
```
/search web query
    ↓
Check if Google configured?
    ↓ Yes           ↓ No
Use Google    Use DuckDuckGo
                (show tip)
```

**Error Handling:**
- Quota exceeded → clear message
- Auth failed → check credentials
- Network errors → helpful guidance

### 3. `main.py`

**Added CLI Options:**
```bash
--google-search-key YOUR_KEY
--google-search-cx YOUR_CX_ID
```

**Interactive Config:**
- Added Google Search section to config flow
- Shows masked credentials
- Prompts for setup

---

## Usage

### Option 1: Command Line Setup

```bash
./focus config \
  --google-search-key "AIzaSy..." \
  --google-search-cx "a1b2c3d4e5..."
```

### Option 2: Interactive Setup

```bash
./focus

> /config
# Select option 2 (Google Search)
# Enter your API key and CX ID
```

### Option 3: Environment Variables

```bash
export GOOGLE_SEARCH_API_KEY="your_key"
export GOOGLE_SEARCH_CX_ID="your_cx_id"
```

### Searching

```bash
> /search web python tutorials
```

If Google is configured:
```
🌐 Web Search Results for: python tutorials
Powered by Google Custom Search
```

If Google is NOT configured:
```
Tip: Configure Google Search for better results: /config

🌐 Web Search Results for: python tutorials
[Uses DuckDuckGo as fallback]
```

---

## Technical Details

### API Integration

**Library**: `google-api-python-client` (already in requirements.txt)

**Endpoint**: Custom Search API v1

**Request Format:**
```python
service.cse().list(
    q=query,
    cx=search_engine_id,
    num=num_results  # max 10
).execute()
```

**Response Format:**
```python
{
    'items': [
        {
            'title': 'Page Title',
            'link': 'https://example.com',
            'snippet': 'Description...'
        }
    ]
}
```

### Error Handling

| Error Code | User Message |
|------------|--------------|
| 429 | "Quota exceeded. Used 100 free searches today." |
| 403 | "Authentication failed. Check your credentials." |
| Network | "Check your internet connection." |
| Other | "Google Search error: {details}" |

### Fallback Logic

```python
if google_configured:
    use_google_search()
else:
    show_tip("Configure Google Search: /config")
    use_duckduckgo_fallback()
```

### Result Display

Both Google and DuckDuckGo results use the same UI:
- Arrow key navigation (via `pick` library)
- Numbered fallback if `pick` not installed
- Open in default browser on selection

---

## Configuration Storage

### Config File: `~/.focus_assistant/config.json`

```json
{
    "anthropic_api_key": "sk-ant-...",
    "openai_api_key": "sk-...",
    "google_search_api_key": "AIzaSy...",
    "google_search_cx_id": "a1b2c3d4e5...",
    "assistant_personality": "...",
    "ai_triage_enabled": true
}
```

### Environment Variables (Alternative)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_SEARCH_API_KEY=AIzaSy...
GOOGLE_SEARCH_CX_ID=a1b2c3d4e5...
```

---

## Testing

### Manual Test

```bash
# 1. Configure (if not done)
./focus config --google-search-key "YOUR_KEY" --google-search-cx "YOUR_CX"

# 2. Start interactive mode
./focus

# 3. Test search
> /search web rust programming language

# 4. Verify it says "Powered by Google Custom Search"
```

### Verify Configuration

```bash
./focus

> /config
# Should show Google Search as "✓" if configured
```

---

## Migration Path

### For Existing Users

No breaking changes! DuckDuckGo still works as fallback.

**Recommended:**
1. Set up Google Search (5 minutes)
2. Test with `/search web test query`
3. Enjoy 100 free searches/day

**Optional:**
If you prefer DuckDuckGo (despite rate limits), just don't configure Google Search.

---

## Limitations

### Google Custom Search API

- **10 results max per request** (API limitation)
- **100 free searches/day** (then paid: $5 per 1000)
- **Requires setup** (~5 minutes)

### DuckDuckGo (Fallback)

- **~2-3 searches before rate limit** (very restrictive)
- **Rate limits last 1-2 minutes**
- **No setup required** (works out of box)

---

## Comparison

| Feature | Google Search API | DuckDuckGo |
|---------|------------------|------------|
| Daily free searches | 100 | ~2-3 |
| Rate limiting | Generous | Aggressive |
| Search quality | Excellent | Good |
| Setup time | 5 minutes | 0 minutes |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Cost (after free) | $5/1000 | Free |
| **Recommendation** | ✅ **Primary** | ⚠️ **Fallback** |

---

## Security Considerations

### What's Stored

- API keys in `~/.focus_assistant/config.json`
- File permissions: 600 (user read/write only)

### What's Transmitted

**To Google:**
- Search queries
- Your IP address
- Timestamp

**NOT transmitted:**
- Your notes, tasks, or journal entries
- Other Focus Assistant data
- Conversations with the AI

### Best Practices

1. ✅ Restrict API key to Custom Search API only
2. ✅ Don't share API key publicly
3. ✅ Monitor usage in Google Cloud Console
4. ✅ Rotate keys periodically (every 6-12 months)

---

## Future Enhancements

Potential improvements:

1. **Result caching** - Cache results for repeated queries
2. **Safe search** - Add safe search toggle
3. **Date filters** - Search within date ranges
4. **Domain filtering** - Search specific domains
5. **Image search** - Add image search support
6. **Multiple engines** - Support Brave Search, Bing, etc.

---

## Troubleshooting

### "Still using DuckDuckGo after setup"

**Check:**
1. Run `/config` - is Google Search shown as "✓"?
2. Verify API key is correct (no extra spaces)
3. Verify CX ID is correct
4. Check API is enabled in Cloud Console

### "Quota exceeded immediately"

**Possible causes:**
1. You've used 100 searches today (wait until tomorrow)
2. Another app is using the same API key
3. Clock on your computer is wrong

**Solution:**
- Check usage: https://console.cloud.google.com/apis/dashboard
- Create a new project and API key if needed

### "Authentication failed"

**Check:**
1. API key is valid and not revoked
2. Custom Search API is enabled
3. API key is restricted to Custom Search API
4. CX ID matches your search engine

---

## Success Criteria

✅ All criteria met:

- [x] Google Custom Search API integrated
- [x] Configuration methods added (CLI + interactive)
- [x] Automatic fallback to DuckDuckGo
- [x] Error handling for quota/auth issues
- [x] Setup guide created
- [x] No breaking changes
- [x] No linter errors
- [x] Same UX (arrow key navigation)
- [x] Clear user feedback (shows which engine)

---

## Summary

**What Changed:**
- Added Google Custom Search as primary web search engine
- DuckDuckGo remains as automatic fallback
- Configuration via `/config` or CLI flags
- Comprehensive setup guide

**User Impact:**
- **Better**: 100 free searches/day (vs 2-3)
- **More reliable**: No aggressive rate limiting
- **Higher quality**: Google's search algorithm
- **No breaking changes**: Everything still works

**Setup Time:** ~5 minutes  
**Cost:** $0 (free tier)  
**Recommendation:** ✅ Highly recommended for anyone using `/search web`

---

See `GOOGLE_SEARCH_SETUP.md` for detailed setup instructions!

