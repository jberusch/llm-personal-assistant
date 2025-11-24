# Gemini Web Search - Setup & Usage

## Overview

The `/search web` command now uses **Gemini 1.5 Pro with web grounding** to search the web in real-time and provide AI-synthesized answers with citations.

### Why Gemini?

- ✅ **Real-time web grounding** - Searches the web directly
- ✅ **Better answers** - AI synthesizes information from multiple sources
- ✅ **Automatic citations** - Sources are linked inline
- ✅ **No rate limits** - Unlike DuckDuckGo's aggressive rate limiting
- ✅ **One API call** - Simpler and faster than search + synthesis
- ✅ **More context** - Not limited to 10 search results

## Setup (2 minutes)

### 1. Get a Google AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Get API key"**
3. Create a new API key or use an existing project
4. Copy the API key

**Note**: If you already have a Google API key for Google Custom Search or Google Calendar, you can reuse it!

### 2. Configure Focus Assistant

```bash
./focus
> /config
```

When prompted, paste your Google API key.

**Or set via environment variable:**

```bash
export GOOGLE_SEARCH_API_KEY="your-api-key-here"
```

### 3. Install Gemini Library

```bash
pip install google-generativeai
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Web Search

```bash
> /search web python async programming best practices
```

**Output:**
```
🌐 Web Search: python async programming best practices

Python's async programming uses the async/await syntax introduced in Python 3.5. 
Here are the key best practices:

1. Use async/await for I/O-bound operations [1]
2. Avoid blocking the event loop with CPU-intensive tasks [2]
3. Use asyncio.gather() for concurrent operations [1][3]
4. Handle exceptions properly with try/except in async functions [2]

Sources:
[1] Real Python - Async IO in Python
    https://realpython.com/async-io-python/
[2] Python Documentation - asyncio
    https://docs.python.org/3/library/asyncio.html
[3] Async Best Practices
    https://example.com/async-best-practices
```

### Ask Anything

Unlike traditional search, you can ask questions naturally:

```bash
> /search web what's the difference between asyncio and threading in python

> /search web how do i deploy a flask app to heroku

> /search web best restaurants in san francisco with outdoor seating

> /search web latest news about artificial intelligence
```

### Technical Queries

Perfect for programming questions:

```bash
> /search web how to use rust lifetimes

> /search web react hooks vs class components performance

> /search web docker compose networking best practices
```

## How It Works

1. **You ask** a question or search query
2. **Gemini searches** the web in real-time using Google Search
3. **AI synthesizes** information from multiple sources
4. **Citations included** - See which sources informed each fact
5. **Answer displayed** in markdown format with clickable links

## Advantages Over Traditional Search

| Feature | Gemini Web Search | Traditional Search |
|---------|-------------------|-------------------|
| Format | Natural language answer | List of links |
| Sources | Multiple sources synthesized | Must click through each |
| Citations | Inline with [1], [2] | None |
| Context | Full understanding | Snippet only |
| Speed | One result | Multiple clicks |
| Rate limits | None (reasonable usage) | DuckDuckGo: 2-3 searches |

## API Limits & Costs

### Free Tier

Google AI Studio provides a generous free tier:
- **60 requests per minute**
- **1,500 requests per day**
- **1 million requests per month**

More than enough for personal use!

### Paid Tier

If you exceed the free tier:
- Very affordable pricing
- Pay only for what you use
- See [pricing details](https://ai.google.dev/pricing)

## Examples

### Research

```bash
> /search web what are the main approaches to prompt engineering
```

Get a comprehensive overview with citations instead of clicking through 10 articles.

### Current Events

```bash
> /search web latest developments in quantum computing 2024
```

Real-time information, not limited to training data cutoff.

### Technical Help

```bash
> /search web how to fix rust borrow checker errors
```

Synthesized advice from multiple Stack Overflow answers and documentation.

### Local Information

```bash
> /search web best coffee shops in hayes valley san francisco
```

Combines reviews, recommendations, and current information.

## Troubleshooting

### "Gemini library not installed"

```bash
pip install google-generativeai
```

### "Gemini API authentication failed"

1. Check your API key: `/config`
2. Verify it's valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Make sure you have the "Generative Language API" enabled

### "API quota exceeded"

You've exceeded the free tier limits. Either:
- Wait until tomorrow (daily limit resets)
- Upgrade to paid tier (very affordable)
- Use less frequently

### No results / Empty response

The query might be too vague. Try:
- Being more specific
- Asking a clear question
- Including relevant keywords

## Comparison to Old Implementation

### Before (DuckDuckGo + Claude)

```
User query → DuckDuckGo API → 10 search results → Claude synthesis → Answer
```

**Problems:**
- ❌ DuckDuckGo rate limits after 2-3 searches
- ❌ Two API calls (slower, more expensive)
- ❌ Limited to snippet previews
- ❌ No real-time grounding

### Now (Gemini with Grounding)

```
User query → Gemini (searches web internally) → Answer with citations
```

**Benefits:**
- ✅ One API call
- ✅ No rate limits (reasonable usage)
- ✅ Real-time web access
- ✅ Better quality answers
- ✅ Automatic citation extraction

## Tips

1. **Be specific** - Better queries get better answers
2. **Ask questions** - "How do I..." works better than keyword spam
3. **Use for research** - Perfect for learning new topics
4. **Check sources** - Click through citations to verify information
5. **Combine with /note** - Save interesting findings immediately

## Integration with Workflow

```bash
# Research while working
> /search web rust async best practices

# Take notes on findings
> /note Learned about tokio runtime and async fn syntax

# Later, search your notes
> /search history rust async

# See your saved learnings
```

## Privacy

- Your queries are sent to Google's Gemini API
- Google's privacy policy applies
- Queries may be used to improve the service
- See [Google AI Privacy](https://ai.google.dev/terms) for details

## Help

Type `/help` in the interactive interface to see all search commands.

## Feedback

The web search now uses cutting-edge AI with real-time grounding. It's a huge improvement over traditional search APIs!

Try it out: `./focus` → `/search web your question here`

