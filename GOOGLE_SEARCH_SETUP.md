# Google Custom Search API Setup

Setting up Google Custom Search gives you **100 free searches per day** with much better reliability than DuckDuckGo's aggressive rate limiting.

## Quick Overview

You need two things:
1. **API Key** - From Google Cloud Console (free tier: 100 searches/day)
2. **CX ID** - Custom Search Engine ID (from Programmable Search Engine)

Total time: ~5-10 minutes

---

## Step 1: Get Your API Key

### 1.1 Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 1.2 Create a Project (if you don't have one)

1. Click the project dropdown at the top
2. Click "New Project"
3. Name it something like "Focus Assistant" or "Personal Search"
4. Click "Create"

### 1.3 Enable Custom Search API

1. Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com
2. Make sure your project is selected
3. Click "Enable"

### 1.4 Create API Key

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "API key"
3. Copy the API key that appears
4. **Important**: Click "Restrict Key" for security:
   - Under "API restrictions", select "Restrict key"
   - Check only "Custom Search API"
   - Click "Save"

✅ **Save this API key** - you'll need it in Step 3

---

## Step 2: Create Custom Search Engine

### 2.1 Go to Programmable Search Engine

Visit: https://programmablesearchengine.google.com/

### 2.2 Create a New Search Engine

1. Click "Add" or "Create a new search engine"
2. Fill in the form:
   - **Search engine name**: "Focus Assistant Web Search"
   - **What to search**: Select "Search the entire web"
   - **Search settings**: Leave default
3. Click "Create"

### 2.3 Get Your CX ID

1. After creation, you'll see your search engine listed
2. Click on it to see details
3. Look for "Search engine ID" or "cx"
4. It looks like: `a1b2c3d4e5f6g7h8i`

✅ **Save this CX ID** - you'll need it in Step 3

---

## Step 3: Configure Focus Assistant

### Option A: Command Line

```bash
./focus config --google-search-key YOUR_API_KEY --google-search-cx YOUR_CX_ID
```

### Option B: Interactive

```bash
./focus

> /config
```

Then select option 2 (Google Search) and enter your credentials.

---

## Step 4: Test It!

```bash
./focus

> /search web python tutorials
```

You should see:
```
🌐 Web Search Results for: python tutorials
Powered by Google Custom Search
```

If you see "Powered by Google Custom Search", it's working! 🎉

---

## Troubleshooting

### Error: "Authentication failed"

**Problem**: API key or CX ID is incorrect

**Solution**:
1. Double-check you copied the full API key (no extra spaces)
2. Verify the CX ID from programmablesearchengine.google.com
3. Make sure Custom Search API is enabled in Cloud Console

### Error: "Quota exceeded"

**Problem**: You've used your 100 free searches today

**Solution**:
1. Wait until tomorrow (quota resets daily)
2. Or upgrade to paid plan (very cheap: $5 per 1000 additional queries)

### Still Using DuckDuckGo?

If you see "Tip: Configure Google Search..." it means:
- Google Search is not configured, OR
- Your credentials are invalid

Run `/config` again to check your settings.

---

## Free Tier Limits

| Feature | Free Tier |
|---------|-----------|
| Searches per day | 100 |
| Cost | $0 |
| Rate limiting | Very generous |
| Quality | Excellent |

**Note**: 100 searches/day is plenty for personal use. If you need more:
- $5 per 1,000 additional queries
- First 10,000 queries each day are charged

---

## Privacy & Security

### What Google Sees

When you search:
- Your search query
- Your IP address
- Timestamp

### What Google Doesn't See

- Your Focus Assistant data (notes, tasks, journal)
- Other commands you run
- Your conversations with the AI

### Security Best Practices

1. **Restrict your API key** to only Custom Search API
2. **Don't share** your API key publicly
3. **Rotate keys periodically** (every 6-12 months)
4. **Monitor usage** at: https://console.cloud.google.com/apis/dashboard

---

## Comparison: Google vs DuckDuckGo

| Feature | Google Search API | DuckDuckGo |
|---------|------------------|------------|
| Free searches/day | 100 | ~2-3 |
| Rate limiting | Generous | Very aggressive |
| Search quality | Excellent | Good |
| Setup required | Yes (~5 min) | No |
| Reliability | Very high | Low |
| **Recommendation** | ✅ **Use this** | ⚠️ Fallback only |

---

## Environment Variables (Alternative)

Instead of storing in config, you can use environment variables:

```bash
export GOOGLE_SEARCH_API_KEY="your_api_key_here"
export GOOGLE_SEARCH_CX_ID="your_cx_id_here"
```

Add to your `~/.zshrc` or `~/.bashrc` to make permanent.

---

## Need Help?

### Useful Links

- **API Console**: https://console.cloud.google.com/
- **Create Search Engine**: https://programmablesearchengine.google.com/
- **API Documentation**: https://developers.google.com/custom-search/v1/overview
- **Pricing**: https://developers.google.com/custom-search/v1/overview#pricing

### Common Questions

**Q: Do I need a credit card?**
A: No, the free tier doesn't require a credit card.

**Q: Will I be charged?**
A: Not for the first 100 searches per day. After that, you can choose to upgrade or just stop.

**Q: Can I use multiple search engines?**
A: Yes! Create different CX IDs for different purposes. But one is enough for Focus Assistant.

**Q: What if I don't want to set this up?**
A: No problem! DuckDuckGo will still work as a fallback. Just be aware of the rate limits (2-3 searches before rate limiting).

---

## Summary

1. ✅ Enable Custom Search API in Google Cloud Console
2. ✅ Create API key and restrict it
3. ✅ Create search engine at programmablesearchengine.google.com
4. ✅ Get your CX ID
5. ✅ Run `./focus config` and enter credentials
6. ✅ Test with `/search web your query`

**Result**: Reliable web search with 100 free searches per day! 🎉

