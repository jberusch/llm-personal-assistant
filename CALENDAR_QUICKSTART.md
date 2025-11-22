# Google Calendar & Gmail Integration - Quick Start

I've added full Google Calendar **and Gmail** integration to your Focus Assistant! 📅 ✉️

## ✅ What's Been Implemented

### New Commands

**View Calendar Events:**
```bash
./focus calendar              # Today
./focus calendar tomorrow     # Tomorrow
./focus calendar weekend      # This weekend
./focus calendar week         # This week
```

**Create Events:**
```bash
./focus schedule "Team meeting tomorrow at 2pm"
./focus schedule "Dentist Friday at 10am"
```

**Interactive Mode:**
```bash
./focus
> /calendar weekend
> /schedule lunch with Sarah next Tuesday at noon
> what do I have this weekend?
```

**Inbox Superpowers:**
```bash
./focus inbox           # Show unread Gmail messages
./focus email 1         # Read the first unread email
./focus reply 1         # Draft & send a reply with AI
./focus archive 1 2 3   # Archive multiple emails at once
./focus cleanup         # Auto-detect newsletters and archive them
```

### Automatic Integration

- **Morning Routine** now shows today's calendar events
- **Chat Assistant** knows your calendar schedule when answering questions
- **Natural Language** works everywhere: "am I free tomorrow afternoon?"
- **Inbox Assistant** can summarize unread email, draft replies, and help clear newsletters

## 🚀 Getting Started

### 1. Install Dependencies (Already Done ✓)

The required Google Calendar libraries have been installed:
- `google-auth`
- `google-auth-oauthlib` 
- `google-auth-httplib2`
- `google-api-python-client`

### 2. Set Up Google Calendar & Gmail (5 minutes)

Follow the detailed guide: **[GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)**

Quick summary:
1. Create a Google Cloud project
2. Enable Google Calendar API
3. Enable Gmail API
4. Create OAuth credentials
5. Download credentials JSON file
6. Save it to `~/.focus_assistant/google_credentials.json`
7. Run `./focus calendar` to authenticate (this now covers Gmail too)

### 3. First Authentication

The first time you run a calendar command, your browser will open for authentication:

```bash
./focus calendar
```

- Sign in to Google
- Click "Advanced" → "Go to Focus Assistant (unsafe)"
- Grant calendar access
- Done! The token is saved for future use

## 📝 What Gets Stored

- **Credentials**: `~/.focus_assistant/google_credentials.json` (you download this)
- **Auth Token**: `~/.focus_assistant/google_token.pickle` (auto-generated)

Both are stored locally and secure.

## 🎯 Try It Out

Once set up, try:

```bash
# View your events
./focus calendar today
./focus calendar weekend

# Create an event
./focus schedule "Coffee with friend tomorrow at 3pm"

# Morning routine
./focus morning
# Now shows today's calendar events!

# Email triage
./focus inbox
./focus email 1
./focus reply 1
./focus cleanup

# Natural conversation
./focus
> what do I have tomorrow?
> schedule team sync Friday at 2pm
> am I free this weekend?
> any unread emails I should prioritize?
```

## ⚠️ Before Setup

Until you complete the Google integration:
- Calendar & Gmail commands will show a "not configured" message
- Everything else works normally
- This is completely optional!

## 🔧 Troubleshooting

If you see errors, check:
1. Credentials file is at correct location: `~/.focus_assistant/google_credentials.json`
2. Google Calendar API is enabled in Google Cloud Console
3. You added yourself as a test user in OAuth consent screen

See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) for detailed troubleshooting.

## 🎉 Benefits

Once configured:
- See your schedule without leaving the terminal
- Create events with natural language
- The assistant knows when you're busy
- Morning routine includes today's calendar
- View unread emails, draft replies, and archive newsletters
- Plan your day and your inbox from the same CLI
- Never miss an appointment or important email!

Ready to set it up? Start with [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)!

