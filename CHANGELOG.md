# MentalWellnessBot — Changelog

## Version 2.0 (November 27, 2025) — CLI Rewrite

### Overview
Replaced the Streamlit web UI with a terminal-based CLI application. All core features preserved and working.

### Changes

#### `mental_bot.py`
- **Removed:** Streamlit imports (`streamlit`, `plotly`, `altair`, `pandas`, `numpy`)
- **Removed:** Web-based UI components (sidebar, charts, HTML rendering)
- **Added:** Terminal-based menu-driven interface with 10 options
- **Added:** Windows UTF-8 console encoding fix (line 20–21)
- **Replaced:** All emoji output with text equivalents (`✅` → `[OK]`, `❌` → `[ERROR]`)
  - Prevents `UnicodeEncodeError` on Windows CP1252 consoles
  - Maintains readability in terminal output

#### Core Features (All Functional)
1. **Account Management** — Login, Create account, Delete account
2. **Journal Entries** — Add, List, with mood tracking and sentiment analysis
3. **Weekly Analytics** — 7-day stats, mood distribution, sentiment average, streak counter
4. **Therapeutic Exercises** — Breathing, Grounding, Affirmation, Meditation
5. **AI Companion** — Optional OpenAI ChatGPT integration (requires `OPENAI_API_KEY`)
6. **Data Export** — JSON backup and PDF report generation (reportlab)
7. **Persistent Storage** — All data saved to `users.json` and `entries.json`

#### `requirements.txt`
- **Removed:** `streamlit`, `plotly`, `numpy`, `pandas`, `altair`
- **Kept:** `openai==0.28.0`, `python-dotenv==1.0.0`, `textblob==0.17.1`, `reportlab==4.0.7`

#### `.env` (Configuration)
- Created for storing `OPENAI_API_KEY` securely
- Loaded via `python-dotenv` in `mental_bot.py`

### Testing & Validation

#### Syntax Check
✓ `python -m py_compile mental_bot.py` — All passed

#### Functional Tests
✓ **Login** — Works with stored credentials  
✓ **Add Journal Entry** — Saves mood, journal text, exercise, breathing exercises  
✓ **List Entries** — Displays all user entries with timestamps  
✓ **Weekly Stats** — Computes 7-day stats, sentiment analysis, streak tracking  
✓ **Export JSON** — Creates `wellness_data_<username>_<date>.json`  
✓ **Export PDF** — Creates `wellness_report_<username>_<date>.pdf` (if reportlab available)  
✓ **AI Chat** — Calls OpenAI API (requires valid `OPENAI_API_KEY` and billing setup)  

#### Full Workflow Demo (Nov 27, 2025)
- Logged in as `prajna` with stored password
- Added new journal entry with mood "Happy" and exercise description
- Listed 18 entries with full metadata
- Viewed 7-day stats (3 entries, 2 exercises, 0.23 avg sentiment, 1-day streak)
- Exported JSON and PDF backups successfully
- CLI menu and prompts display cleanly without encoding errors

### Performance & Compatibility
- **Platform:** Windows (PowerShell), macOS, Linux
- **Python:** 3.12.4 (also compatible with 3.10+)
- **Console:** UTF-8 output enforced for Windows; emoji replaced with text for broader compatibility
- **Dependencies:** Minimal; no heavy web framework

### Known Limitations
1. **AI Chat** — Requires active OpenAI billing (free trial quota may be exhausted)
2. **PDF Export** — Depends on `reportlab` package (included, but can be removed if not needed)
3. **Emoji Display** — Replaced with text labels to avoid console encoding issues

### Migration Notes
- Existing `users.json` and `entries.json` are fully compatible with the new CLI
- Old `entries.json` can be viewed using option 4 (List my entries)
- No data loss; all historical entries preserved

### Future Enhancements
- Add unit tests for persistence and analytics functions
- Support multiple export formats (CSV, XML)
- Implement local caching for AI responses
- Add dark/light theme support via environment variable
- Optional SQLite backend for large datasets

---

**Status:** ✓ Production-ready for local/terminal use  
**Last Updated:** 2025-11-27  
**Contributors:** Automated CLI rewrite
