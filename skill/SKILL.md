# تول — Claude Integration Skill

When the user asks me to generate content, prompts, reports, or presentations, I should:

## 1. CLI Mode
Run تول commands via the CLI at `~/Claude/Projects/تول/`:

- `python3 ~/Claude/Projects/تول/cli/main.py content "<topic>"`
- `python3 ~/Claude/Projects/تول/cli/main.py prompt "<task>"`
- `python3 ~/Claude/Projects/تول/cli/main.py report "<title>"`
- `python3 ~/Claude/Projects/تول/cli/main.py present "<title>" --slides N`

## 2. Direct Generation Mode
If the user is talking to me (Claude/Big Pickle), I can generate HTML directly using my built-in skills (deck-*, article-*, card-*) which produce richer output. تول is the orchestrator; I'm the engine.

## 3. Web Dashboard
The dashboard runs on `http://localhost:8000` via:
```bash
uvicorn api.main:app --reload --port 8000
```

## 4. Telegram Bot
Start the bot:
```bash
python3 bot/telegram.py
```

## Available Engines
| Engine | Function |
|--------|----------|
| content | HTML carousel + social post |
| prompt | AI prompt generation |
| report | HTML report |
| present | HTML presentation |
| status | AI provider limits |
