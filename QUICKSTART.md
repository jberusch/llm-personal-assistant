# Quick Start Guide

Get up and running with Focus Assistant in 2 minutes.

## Installation

```bash
# 1. Navigate to the project directory
cd /Users/joe/llm-personal-assistant

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Set your API key (choose one method)

# Method A: Via command
./focus config --key your_anthropic_api_key_here

# Method B: Via environment variable
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Get your API key at: https://console.anthropic.com/

**Note:** The examples below use `./focus` assuming you're in the project directory. To run from anywhere, see installation options in README.md

## Your First Day

### 1. Morning (5-10 minutes)
```bash
./focus morning
```

Answer 5 reflection questions:
- Sleep quality and energy level
- How you're feeling
- Your ONE main priority
- What you're avoiding
- What would bring meaning/joy

The assistant will help you create a focused plan.

### 2. Throughout the Day
```bash
./focus chat
```

Use chat to:
- Add tasks: "remind me tomorrow to pay rent"
- Get guidance: "what should I focus on?"
- Check tasks: type `tasks`
- Quick exit: type `quit`

Or add tasks quickly:
```bash
./focus add "call mom tomorrow"
./focus add "finish report by friday"
```

### 3. Evening (5 minutes)
```bash
./focus evening
```

Reflect on:
- What you accomplished
- What got in your way
- Overall feelings about the day
- One thing for tomorrow

## Quick Tips

- **Morning routine sets context** - The assistant remembers your goals all day
- **Chat is your primary interface** - Just talk naturally
- **Tasks flow from conversation** - No need to think "should I add this as a task?"
- **View tasks anytime**: `focus tasks`
- **Mark complete**: `focus done`

## Example Natural Language Tasks

```bash
./focus add "remind me tomorrow to pay rent"
./focus add "call mom next week"
./focus add "schedule dentist appointment in 3 days"
./focus add "submit report on friday"
./focus add "buy groceries"
```

The system automatically:
- Extracts the task description
- Parses the due date
- Categorizes (today, upcoming, inbox)

## Commands Cheat Sheet

```bash
./focus morning       # Start your day
./focus chat          # Main interaction mode
./focus add "task"    # Quick task add
./focus tasks         # View task board
./focus done          # Mark task complete
./focus evening       # End your day
./focus stats         # View statistics
./focus config        # Configuration
```

## Data Location

All your data is stored locally at:
```
~/.focus_assistant/
  ├── config.json           # API key, settings
  ├── tasks.json            # All tasks
  └── journal/
      └── YYYY-MM-DD.md     # Daily journals (Markdown!)
```

**Obsidian Users:** Your journals are already in Obsidian-ready format! See `OBSIDIAN.md` for integration guide.

## Edit Your Journal

```bash
./focus log                     # Open today's journal in web editor
./focus log 2025-11-20          # Open specific date in web editor
```

Opens a full-featured web editor with:
- Live markdown preview
- Editable view of your entire day
- Morning/evening reflections, chat history, and notes
- Save with Cmd/Ctrl+S

## Troubleshooting

**"No API key found"**
- Run: `./focus config --key YOUR_KEY`
- Or set: `export ANTHROPIC_API_KEY=your_key`

**"command not found: focus"**
- Use `./focus` from the project directory
- Or add the project to your PATH (see README.md)

**"Module not found"**
- Run: `pip3 install -r requirements.txt` from the project directory

**Want to reset everything?**
- Delete: `~/.focus_assistant/` directory

## Next Steps

After using it for a few days, you might want to:
- Review your journal entries in `~/.focus_assistant/journal/`
- Check patterns in your morning reflections
- See which tasks you complete vs avoid

Future features will include:
- Semantic search across all your entries
- Web UI for visualization
- Focus monitoring and intervention
- Project auto-detection from your language

## Support

Questions or issues? Check the main README.md for detailed documentation.

Happy focusing! 🎯

