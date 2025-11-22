# Focus Assistant 🎯

Your personal productivity coach powered by Claude AI. A CLI tool to help you plan your day, manage tasks, and stay focused.

## Features

- **Morning Routine**: Start your day with a structured reflection that helps you identify priorities
- **Interactive Chat**: Talk naturally with your AI coach throughout the day
- **Smart Task Management**: Add tasks with natural language ("remind me tomorrow to pay rent")
- **Google Calendar Integration** (optional): View events, schedule meetings, get calendar-aware responses
- **Evening Reflection**: Review your day and prepare for tomorrow
- **Context-Aware**: The assistant remembers your morning goals and helps keep you on track

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd llm-personal-assistant
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Run the tool (choose one method):

**Method A: Run directly from the project directory**
```bash
./focus config --key YOUR_ANTHROPIC_API_KEY
./focus morning
```

**Method B: Add to your PATH (optional)**
```bash
# Add this line to your ~/.zshrc or ~/.bashrc:
export PATH="$PATH:/Users/joe/llm-personal-assistant"

# Then reload your shell:
source ~/.zshrc

# Now you can run from anywhere:
focus morning
```

**Method C: Create an alias (optional)**
```bash
# Add this to your ~/.zshrc or ~/.bashrc:
alias focus='/Users/joe/llm-personal-assistant/focus'

# Then reload your shell:
source ~/.zshrc
```

4. Configure your API key:
```bash
./focus config --key YOUR_ANTHROPIC_API_KEY
```

Or set it as an environment variable:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

### Morning Routine
Start your day with a structured reflection:
```bash
./focus morning
```

This will ask you questions about:
- How you slept and your energy level
- How you're feeling about the day
- Your main priority
- What you're avoiding
- What would bring joy or meaning

Then it helps you create a focused plan for the day.

### Chat
Have ongoing conversations throughout the day:
```bash
./focus chat
```

In the chat:
- Ask for help prioritizing tasks
- Create tasks naturally: "remind me tomorrow to call mom"
- Get suggestions: "what should I focus on?"
- Type `tasks` to see your task board
- Type `quit` to exit

### Task Management

Add tasks with natural language:
```bash
./focus add "remind me tomorrow to pay rent"
./focus add "call mom next week"
./focus add "buy groceries"
```

View your tasks:
```bash
./focus tasks              # View in terminal
./focus tasks gui          # Open web GUI with checkboxes
```

The GUI mode opens a beautiful web interface where you can check off tasks with a single click!

Mark tasks as complete:
```bash
./focus done
```

### Calendar Integration (Optional)

Connect your Google Calendar to view events and schedule meetings!

**Setup** (5 minutes, one-time):  
See **[GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)** for detailed setup instructions.

**View events:**
```bash
./focus calendar                 # Today's events
./focus calendar tomorrow        # Tomorrow's events
./focus calendar weekend         # This weekend
./focus calendar week            # This week
```

**Create events:**
```bash
./focus schedule "Team meeting tomorrow at 2pm"
./focus schedule "Dentist Friday at 10am"
```

**In chat mode, ask naturally:**
```bash
./focus
> what do I have this weekend?
> am I free tomorrow afternoon?
> schedule lunch with Sarah next Tuesday at noon
```

The assistant automatically knows your calendar and includes it when answering questions!

### Evening Reflection
End your day with reflection:
```bash
./focus evening
```

Review what you accomplished, what got in your way, and set one priority for tomorrow.

### Other Commands

View statistics:
```bash
./focus stats
```

Configure settings:
```bash
./focus config
```

## How It Works

### Data Storage
All data is stored locally in `~/.focus_assistant/`:
- `config.json` - Your API key and preferences
- `tasks.json` - All your tasks
- `journal/YYYY-MM-DD.md` - Daily journal entries in Markdown format (Obsidian-ready!)

### Obsidian Integration
Your journals are stored as beautiful, human-readable Markdown files that work perfectly with Obsidian! See [OBSIDIAN.md](OBSIDIAN.md) for integration guide.

### Future-Proof Design
The data structure is designed for future expansion:
- **Obsidian Integration**: ✅ Journals already in Markdown format - works today!
- **Supabase**: For cloud sync and web interface
- **Embeddings**: For semantic search of your past thoughts
- **Web UI**: All methods are structured to easily add a web frontend

### Edit Your Journal
```bash
./focus log                     # Open today's journal in web editor
./focus log 2025-11-20          # Open specific date in web editor
```

The `/log` command opens a beautiful web-based markdown editor where you can view and edit your entire daily journal with live preview.

### Migrating from JSON
If you have existing JSON journals, run:
```bash
python3 migrate_to_markdown.py
```
This converts all journals to Markdown and archives the JSON files.

## Workflow

The ideal workflow:

1. **Morning**: `./focus morning` - Plan your day
2. **Throughout the day**: `./focus chat` - Check in, add tasks, get guidance
3. **Evening**: `./focus evening` - Reflect and prepare for tomorrow

## Requirements

- Python 3.8+
- Anthropic API key (get one at https://console.anthropic.com/)

## Privacy

All your data is stored locally on your machine. The only external API call is to Claude (Anthropic) for AI assistance.

## License

MIT
