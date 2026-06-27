# Học Tiếng Việt — Southern Vietnamese flashcards

A spaced-repetition app for learning **Southern-dialect (giọng miền Nam)**
Vietnamese: letters → numbers → conversation. Django + HTMX, FSRS scheduling,
optional Southern-voice audio via FPT.AI.

## Quick start

```bash
make setup     # create venv, install deps, build DB, load content
make run       # start the dev server → http://127.0.0.1:8000
```

That's it. The app runs fully **text + IPA only** with no API key.

## Southern audio (optional)

Real Southern pronunciation comes from FPT.AI's Southern voices:

```bash
cp .env.example .env
# put your free key from https://fpt.ai/ into FPT_API_KEY
```

Synthesized clips are cached under `media/audio_cache/` — each phrase hits the
API at most once.

## How it's organized

| Path | What |
|------|------|
| `content/*.yaml` | **Source of truth** for cards (committed to git) |
| `learning/models.py` | `Deck`, `Card`, `Review` |
| `learning/srs.py` | FSRS scheduler wrapper (grade → next due date) |
| `learning/dialect.py` | Southern rules: d/gi/v→y, r kept, hỏi/ngã merge |
| `learning/audio.py` | FPT.AI client + local cache |
| `learning/templates/` | HTMX study loop (one card partial at a time) |

**The DB is derived data.** `db.sqlite3` is gitignored; anyone clones the repo
and runs `make setup` to build their own local DB from the migrations + YAML.

## Make targets

```
make setup    install deps, migrate, seed
make run      migrate + seed + start server
make seed     reload content from YAML
make test     run the test suite
make clean    delete local DB + cached audio
```

## Roadmap

- [x] M1 — content + study page + flip cards
- [x] M2 — FSRS scheduling + grade buttons + SQLite progress
- [ ] M3 — wire FPT.AI Southern audio (code ready; needs API key)
- [ ] M4 — tone visualizations, more decks
- [ ] M5 — 🎤 record-and-compare pronunciation (pitch overlay)
```
