# TOOLS.md - Tool Configuration & Notes

> Document tool-specific configurations, gotchas, and credentials here.

---

## Credentials Location

All credentials stored in `.credentials/` (gitignored):
- `example-api.txt` — Example API key

---

## Python

**Status:** ✅ Fixed Configuration (2026-03-01)

**Issue:** Some cron jobs and scripts were calling `python` instead of `python3`, causing "command not found" errors.

**Fix:** Created symlink at `~/.local/bin/python` -> `/opt/homebrew/bin/python3`

**Note:** The system's venvs (~/.openclaw/workspace/venv and ~/.venv/polymarket) already have proper python symlinks.

**Configuration:**
```
Key details about how this tool is configured
```

**Gotchas:**
- Things that don't work as expected
- Workarounds discovered

**Common Operations:**
```bash
# Example command
tool-name --common-flag
```

---

## Writing Preferences

[Document any preferences about writing style, voice, etc.]

---

## What Goes Here

- Tool configurations and settings
- Credential locations (not the credentials themselves!)
- Gotchas and workarounds discovered
- Common commands and patterns
- Integration notes

## Why Separate?

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

---

*Add whatever helps you do your job. This is your cheat sheet.*
