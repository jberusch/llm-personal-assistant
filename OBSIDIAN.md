# Obsidian Integration Guide

Your Focus Assistant journals are now stored in Obsidian-ready Markdown format! This guide shows you how to integrate them with Obsidian for a powerful personal knowledge system.

## Quick Setup

### Option 1: Symlink (Recommended)

Create a symbolic link from your Obsidian vault to the journal directory:

```bash
# Navigate to your Obsidian vault
cd ~/Documents/MyVault  # Adjust path to your vault

# Create a symlink
ln -s ~/.focus_assistant/journal/ "Focus Assistant"

# Now you'll see a "Focus Assistant" folder in Obsidian with all your journals!
```

### Option 2: Copy/Sync

Set up a script to periodically copy journals to your Obsidian vault:

```bash
#!/bin/bash
# sync-focus-to-obsidian.sh
rsync -av ~/.focus_assistant/journal/*.md ~/Documents/MyVault/Focus/
```

## Journal Format

Your daily journals use this structure:

```markdown
---
date: 2025-11-21
day: Friday
energy: 8
tags: [daily, journal]
---

# Friday, November 21, 2025

## Morning Reflection
[Your morning Q&A]

## Chat History
[Timestamped conversations]

## Evening Reflection
[Your evening review]
```

## Task Board Export (Manual Refresh)

Run the export command whenever you want your current task board inside the vault:

```bash
./focus export obsidian                      # Generates TASKS.md
./focus export obsidian --include-completed  # Adds up to 20 recent completions
```

This writes `~/.focus_assistant/journal/TASKS.md`, which rides along with the same symlink/rsync as your daily notes. Treat it as **read-only** in Obsidian—re-run the command to refresh instead of editing the file directly.

Each task entry includes Dataview-friendly metadata (`status::`, `id::`, etc.) so you can query or visualize tasks however you like inside Obsidian.

## Obsidian Features

### YAML Frontmatter

Query your data with Dataview:

```dataview
TABLE energy, day
FROM "Focus Assistant"
WHERE energy > 7
SORT date DESC
```

### Daily Notes Integration

Configure Obsidian's Daily Notes plugin:

1. Settings → Daily notes
2. Set folder: `Focus Assistant/`
3. Set format: `YYYY-MM-DD`
4. Set template: (create a template matching the format)

Now `Cmd+D` will open today's focus journal!

### Backlinks & Graph View

- Type `[[2025-11-20]]` to link to previous days
- Use graph view to see connections between entries
- Search across all your reflections instantly

### Tags

Your journals auto-include `#daily` and `#journal` tags. Add more inline:

```markdown
Making progress on this project. #productive #flow

Feeling distracted by social media. #distracted
```

Then use tag pane to find patterns.

### Dataview Queries

**High Energy Days:**
```dataview
LIST
FROM "Focus Assistant"
WHERE energy >= 8
SORT date DESC
LIMIT 10
```

**Recent Reflections:**
```dataview
TABLE date, day, energy
FROM "Focus Assistant"
WHERE date >= date(today) - dur(7 days)
```

**Days You Avoided Something:**
```dataview
TABLE file.link as "Day"
FROM "Focus Assistant"
WHERE contains(file.content, "avoiding")
SORT date DESC
```

## Advanced Usage

### Templates

Create a daily note template at `Templates/Daily Focus.md`:

```markdown
---
date: {{date:YYYY-MM-DD}}
day: {{date:dddd}}
energy: 
tags: [daily, journal]
---

# {{date:dddd, MMMM DD, YYYY}}

## Morning Reflection

**How did you sleep? Energy level:**

**Feeling going into today:**

**One thing for success:**

**Avoiding:**

**What would bring joy:**

---

## Notes

---

## Evening Reflection

**Accomplished today:**

**What got in my way:**

**Overall feeling:**

**Tomorrow's focus:**
```

### Semantic Search (Coming Soon)

Once embeddings are implemented, you'll be able to:

1. Ask: "What did I say about grad school decisions?"
2. Get: All relevant journal entries ranked by similarity
3. See: Timeline of your thinking on that topic

### Mobile Access

1. Install Obsidian mobile app
2. Sync vault (Obsidian Sync or iCloud)
3. Read/edit your journals on the go
4. Changes sync back to your focus assistant

## Tips

1. **Morning routine in Obsidian:** Use Obsidian's daily note instead of `./focus morning` if you prefer
2. **Rich formatting:** Add images, code blocks, tables to your journals
3. **Linked notes:** Reference other notes: `[[Project Ideas]]`, `[[Book Notes/Atomic Habits]]`
4. **Custom CSS:** Style your daily journals with custom CSS snippets
5. **Plugins:** Try Calendar, Dataview, Charts for visualization

## File Locations

```
~/.focus_assistant/
├── journal/
│   ├── 2025-11-21.md        # Your journals (Obsidian-ready)
│   ├── 2025-11-22.md
│   └── archive/              # Old JSON files (backup)
│       └── 2025-11-21.json
└── tasks.json                # Tasks (still JSON)
```

## Troubleshooting

**Q: Journals don't show up in Obsidian**
- Check the symlink: `ls -la ~/Documents/MyVault/`
- Verify path: `ls ~/.focus_assistant/journal/`

**Q: Can I edit journals in Obsidian?**
- Yes! Changes are saved to the markdown file
- Focus assistant will read them back correctly
- Be careful not to break the format structure

**Q: What about tasks?**
- Tasks remain in JSON for programmatic access
- Future: May add task.md files with `[[task-uuid]]` links

**Q: Can I use a different vault structure?**
- Absolutely! Organize however you like
- The format is standard markdown

## Future Enhancements

Coming soon:
- Auto-generated wikilinks between related entries
- Task references in journals: `[[task:pay-rent]]`
- Project auto-detection with automatic folder creation
- Weekly/monthly summary notes
- Embedding-based "similar entries" section

---

**Enjoy your enhanced journaling system!** 🎯

Your thoughts are now in a format that grows with you - searchable, linkable, and future-proof.

