# Google Places API Setup

Find nearby places (cafes, restaurants, bars, etc.) with ratings, reviews, hours, and more!

## Quick Overview

**Good News**: If you've already set up Google Custom Search or Google Calendar/Gmail, you can reuse your existing Google Cloud project!

**What You Need:**
- Google API Key (can reuse from Custom Search!)
- Places API enabled (~1 click)

**Free Tier**: $200/month credit = ~5,000-10,000 place searches
**Setup Time**: 2 minutes (if you already have a project)

---

## Option A: Reuse Existing API Key (EASIEST)

If you've already set up Google Custom Search:

### Step 1: Enable Places API

1. Go to: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
2. Make sure your existing project is selected
3. Click "Enable"

### Step 2: Test It!

Your existing API key should already work:

```bash
./focus

> /places cafe nearby
```

That's it! No new API key needed.

---

## Option B: Start from Scratch

If you don't have a Google Cloud project yet:

### Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Click project dropdown → "New Project"
3. Name it: "Focus Assistant"
4. Click "Create"

### Step 2: Enable Places API

1. Go to: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
2. Make sure your project is selected
3. Click "Enable"

### Step 3: Create API Key

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "API key"
3. Copy the API key
4. (Recommended) Click "Restrict Key":
   - Under "API restrictions", select "Restrict key"
   - Check "Places API" and "Custom Search API"
   - Click "Save"

### Step 4: Configure Focus Assistant

```bash
./focus config --google-search-key YOUR_API_KEY
```

Or interactively:

```bash
./focus

> /config
# Select option 2 (Google Search)
# Enter your API key
```

### Step 5: Test It!

```bash
> /places pizza in hayes valley
```

---

## Usage Examples

### Basic Search

```bash
> /places cafe nearby
```

Shows cafes near you with ratings, hours, and prices.

### Specific Location

```bash
> /places pizza in hayes valley
> /places bars on fillmore
> /places coffee shop mission district
```

### What You'll See

```
📍 Places Near You

1. Blue Bottle Coffee ⭐⭐⭐⭐ 4.5 (328 reviews)
2. Sightglass Coffee ⭐⭐⭐⭐⭐ 4.6 (445 reviews)
3. Ritual Coffee Roasters ⭐⭐⭐⭐ 4.4 (892 reviews)

[Use arrows to select, Enter for details]
```

### Place Details

When you select a place:

```
☕ Blue Bottle Coffee

⭐⭐⭐⭐ 4.5 stars (328 reviews)
📍 315 Linden St, San Francisco, CA 94102
📞 (415) 896-4343
🕐 Open now
💰 $$
🌐 bluebottlecoffee.com

Actions:
  1. Open in Google Maps
  2. Save to notes
  3. Back to results
```

---

## Free Tier Limits

| Feature | Free Tier |
|---------|-----------|
| Monthly credit | $200 |
| Approximate searches | 5,000-10,000 |
| Text Search (basic) | $17 per 1,000 requests |
| Place Details | $17 per 1,000 requests |
| **Cost for typical use** | **$0** (well within free tier) |

**Example**: 
- 10 searches/day × 30 days = 300 searches/month
- Cost: ~$5 (way under $200 free tier)

---

## Troubleshooting

### "Google Places requires a Google API key"

**Solution**: Run `/config` and set up your Google API key.

### "Make sure Places API is enabled"

**Solution**:
1. Go to: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
2. Click "Enable"
3. Wait 1-2 minutes for it to propagate

### "API quota exceeded"

**Problem**: You've used more than $200 worth of requests this month (very unlikely for personal use).

**Solution**:
1. Check usage: https://console.cloud.google.com/apis/dashboard
2. If legitimate, consider enabling billing (but free tier should be plenty)

### No results found

**Common causes**:
- Query is too specific
- Location doesn't have those businesses
- Try broader terms: "cafe" instead of "blue bottle coffee"

---

## Privacy & Data

### What Google Sees

When you search:
- Your search query ("cafe nearby")
- Your IP address (used to approximate location)
- Timestamp

### What Google Doesn't See

- Your Focus Assistant notes, tasks, journal
- Other commands you run
- Conversations with the AI

### Location Data

The API uses your **IP address** to approximate location for "nearby" searches. It does NOT:
- Access your GPS
- Track your movements
- Store your location history

You can also specify locations manually: `/places pizza in hayes valley`

---

## Comparison: Places API vs Web Search

| Feature | Places API | Web Search |
|---------|-----------|------------|
| Purpose | Local businesses | General web info |
| Data quality | Structured (ratings, hours, etc.) | Unstructured (web pages) |
| Real-time info | Yes (hours, open/closed) | No |
| Ratings & reviews | Yes | No |
| Phone & address | Yes | Sometimes |
| **Best for** | **Finding places** | **Finding information** |

Use `/places` for local businesses, `/search web` for everything else!

---

## Advanced Tips

### Combine with Tasks

```bash
> /places sushi restaurant mission

# Select a place, choose option 2 (Save to notes)
# Then:

> /add Try Sushi Place on Valencia tomorrow
```

### Save Favorites

When you find a good place:
1. Select it
2. Choose "Save to notes"
3. Later: `/search history sushi` to find it

### Open Directly in Maps

Select any place and choose "Open in Google Maps" to:
- Get directions
- See photos
- Read reviews
- Call the business

---

## API Pricing Details

For transparency, here's the actual pricing:

| Request Type | Cost per 1,000 |
|-------------|---------------|
| Text Search (basic) | $17.00 |
| Nearby Search | $17.00 |
| Place Details (basic) | $17.00 |
| Place Details (contact) | $3.00 |
| Place Details (atmosphere) | $3.00 |

**Free monthly credit**: $200

**Typical usage** (10 searches/day):
- 300 text searches: $5.10
- 300 place details: $5.10
- **Total: ~$10/month** (covered by free $200)

You'd need to do **100 searches per day** to exceed the free tier!

---

## FAQ

**Q: Do I need a separate API key from Custom Search?**
A: No! The same API key works for both. Just enable Places API in your project.

**Q: Will this work without an API key?**
A: No, Places API requires authentication (unlike DuckDuckGo which tries to work without auth but has rate limits).

**Q: Can I search for specific businesses?**
A: Yes! `/places blue bottle coffee san francisco`

**Q: Does it use my GPS location?**
A: No, it uses your IP address to approximate location for "nearby" searches.

**Q: What if I travel?**
A: The "nearby" results will update based on your current IP address location.

**Q: Can I search in other cities?**
A: Yes! Just specify: `/places pizza in new york`

---

## Useful Links

- **Enable Places API**: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
- **API Dashboard**: https://console.cloud.google.com/apis/dashboard
- **Credentials**: https://console.cloud.google.com/apis/credentials
- **Pricing**: https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
- **Documentation**: https://developers.google.com/maps/documentation/places/web-service/overview

---

## Summary

1. ✅ Enable Places API in Google Cloud Console
2. ✅ Use your existing API key (or create one)
3. ✅ Configure with `/config`
4. ✅ Try: `/places cafe nearby`

**Result**: Rich local business data with ratings, hours, reviews, and more! 🗺️

