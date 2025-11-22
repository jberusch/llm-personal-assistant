# Google Calendar Setup Guide

This guide will help you connect your Focus Assistant to Google Calendar **and Gmail** in about 5 minutes.

## Quick Overview

You'll need to:
1. Create a Google Cloud project (free)
2. Enable the Google Calendar API
3. Download credentials
4. Run the assistant to authenticate

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"** (or select an existing project)
3. Enter a project name (e.g., "Focus Assistant") and click **Create**
4. Wait a few seconds for the project to be created

### Step 2: Enable Google Calendar API

1. In the Google Cloud Console, make sure your new project is selected (check the dropdown at the top)
2. Go to **APIs & Services > Library** (or click [this link](https://console.cloud.google.com/apis/library))
3. Search for **"Google Calendar API"**
4. Click on **Google Calendar API** in the results
5. Click the **Enable** button

### Step 3: Enable Gmail API

1. Still in the same project, go back to **APIs & Services > Library**
2. Search for **"Gmail API"**
3. Click **Enable**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services > Credentials** (or click [this link](https://console.cloud.google.com/apis/credentials))
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**

#### Configure OAuth Consent Screen (if prompted)

If this is your first time, you'll need to configure the OAuth consent screen:

1. Click **"CONFIGURE CONSENT SCREEN"**
2. Choose **"External"** (unless you have a Google Workspace account)
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: Focus Assistant
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **"Save and Continue"**
6. **Scopes**: Click **"Save and Continue"** (we'll add them later)
7. **Test users**: Click **"+ ADD USERS"** and add your email address
8. Click **"Save and Continue"**
9. Click **"Back to Dashboard"**

> **403 / access_denied error?**  
> If Google says *"the app is being tested and only developer-approved testers can use it"*, it means your Google account is not listed under **Test users** on the OAuth consent screen. Add the email address you use to sign in to Google (Step 7) and try again.

> **Already connected calendar but adding Gmail now?**  
> Delete `~/.focus_assistant/google_token.pickle` so the new Gmail permissions can be applied the next time you authenticate.

#### Create OAuth Client ID

Now create the credentials:

1. Go back to **APIs & Services > Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Choose **"Desktop app"** as the application type
4. Name it "Focus Assistant Desktop"
5. Click **"Create"**
6. A dialog will appear with your credentials - click **"OK"**

### Step 5: Download Credentials

1. On the Credentials page, find your newly created OAuth 2.0 Client ID
2. Click the **download icon** (⬇️) on the right side
3. A JSON file will download (named something like `client_secret_xxxxx.json`)

### Step 6: Move Credentials File

Move the downloaded JSON file to your Focus Assistant directory:

```bash
# Navigate to your Focus Assistant directory
cd /Users/joe/llm-personal-assistant

# Move the downloaded file (adjust the path to match your download)
mv ~/Downloads/client_secret_*.json ~/.focus_assistant/google_credentials.json
```

Or manually:
1. Rename the file to `google_credentials.json`
2. Move it to `~/.focus_assistant/google_credentials.json`

### Step 7: Authenticate

Now run the Focus Assistant with a calendar command:

```bash
./focus calendar
```

Or in interactive mode:

```bash
./focus
> /calendar
```

**What happens:**
1. A browser window will open
2. Google will ask you to sign in (if not already signed in)
3. Google will show a warning that the app isn't verified - this is normal!
   - Click **"Advanced"**
   - Click **"Go to Focus Assistant (unsafe)"**
4. Grant permission to access your calendar
5. You'll see "The authentication flow has completed"
6. Close the browser window

**You're done!** The assistant is now connected to your calendar. You won't need to do this again - the token is saved.

## Using Calendar Features

### View Events

```bash
# Command line
./focus calendar                 # Today's events
./focus calendar tomorrow       # Tomorrow's events
./focus calendar weekend        # This weekend
./focus calendar week           # This week

# Interactive mode
./focus
> /calendar today
> /calendar weekend
```

### Create Events

```bash
# Command line
./focus schedule "Team meeting tomorrow at 2pm"
./focus schedule "Dentist appointment Friday at 10am"

# Interactive mode
./focus
> /schedule lunch with Sarah next Tuesday at noon
```

### Natural Language Questions

The assistant now knows about your calendar:

```
> what do I have tomorrow?
> do I need to do anything this weekend?
> when is my next meeting?
> am I free Friday afternoon?
```

### Morning Routine Integration

Your morning routine will automatically show today's calendar events along with your tasks!

## Troubleshooting

### "Credentials file not found"

Make sure the file is at: `~/.focus_assistant/google_credentials.json`

```bash
ls -la ~/.focus_assistant/google_credentials.json
```

### "Access denied" or "403 error"

Make sure you:
1. Enabled the Google Calendar API
2. Added yourself as a test user in the OAuth consent screen

### "Token has been expired or revoked"

Delete the token and re-authenticate:

```bash
rm ~/.focus_assistant/google_token.pickle
./focus calendar
```

### Browser doesn't open automatically

If the browser doesn't open, look for a URL in the terminal output and paste it into your browser manually.

### Still having issues?

Check:
1. Your Google Cloud project is selected (dropdown at top of console)
2. Google Calendar API is enabled (should show "API enabled" badge)
3. OAuth credentials are "Desktop app" type (not "Web application")
4. You added yourself as a test user
5. The JSON file is properly named and in the right location

## Security & Privacy

- **Data storage**: Tokens are stored locally in `~/.focus_assistant/google_token.pickle`
- **Access**: Only you can access your calendar through this app
- **Permissions**: The app only requests calendar access, nothing else
- **Standard OAuth**: Same authentication method used by Gmail, Drive, etc.
- **Revoke access**: Go to [Google Account > Security > Third-party apps](https://myaccount.google.com/permissions) to revoke access anytime

## Updating Timezone

By default, events are created in `America/Los_Angeles` timezone. To change this:

Edit `google_integration.py` and find this section:

```python
'timeZone': 'America/Los_Angeles',
```

Change it to your timezone (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`).

## What Next?

Once configured, the Google integration works seamlessly:

- ✅ Morning routine shows today's calendar events
- ✅ Assistant knows your schedule when you ask questions  
- ✅ Create events with natural language
- ✅ View events without leaving the terminal
- ✅ Review unread Gmail messages with `/inbox`
- ✅ Draft replies with `/reply` and bulk clean newsletters with `/cleanup`

Enjoy your calendar- and email-aware assistant! 📅✉️

