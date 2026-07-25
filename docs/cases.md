# Steer Cases

Real examples of a human steering an AI agent in daily work.
Collected from direct interaction with a personal AI assistant (Hermes).

Format: **Agent** / **Task** / **Trigger** / **Steer** / **Type** / **Could prompt fix this?** / **Result**

---

## Case 001 — Memory Integration via Cron, Not Code Change

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Give the agent persistent emotional/contextual memory across sessions
**Trigger:** Agent proposed modifying the system prompt ingestion pipeline or adding a memory plugin — both requiring gateway-level code changes, with risk of breaking KV cache or introducing state bugs.
**Steer:** "Don't touch the agent. Use cron to periodically read the memory database, extract relevant context, and write it into a marked section of the agent's soul prompt file. The agent reads the file on every session start — it'll just see the memory as part of its prompt, no code changes needed."
**Type:** Lateral-architecture (agent defaults to "modify the pipeline," human sees "use existing file I/O that's already there")
**Could prompt template fix this?** No — requires recognizing that the system *already* reads a file on boot, and that a cron job can inject content into that file without touching any agent code. This is not a "better instruction" problem. This is a "see the system from outside" problem.
**Result:** ✅ Zero code changes to the agent. Cron writes to SOUL.md every hour. Agent reads it on session start. Memory is persistent. KV cache is untouched. The solution is 4 lines of bash.

**Why this case matters:** This is the purest example of agent steer. The agent was trapped in "I need to modify the codebase" thinking. The human said "don't modify anything — just write to a file that the agent already reads." This kind of lateral thinking — finding the path of least resistance that happens to be invisible from inside the system — is exactly what makes human judgment valuable in agent workflows.

---

## Case 002 — Unnecessary Git Pull in Backup Script

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Fix a cron backup script that was failing with exit code 128
**Trigger:** Agent proposed changing `git pull --rebase` to `git pull --rebase --autostash`, adding an extra flag to handle dirty working trees. It accepted the assumption that pulling was necessary.
**Steer:** "Why are we pulling at all? This repo exists only to push backups. There's nothing upstream to pull." The agent had all the context — it knew the repo was a backup-only mirror — but didn't apply that knowledge to question the premise.
**Type:** Over-engineering (agent fixed the symptom instead of questioning the need for the operation)
**Could prompt template fix this?** No — requires understanding the *purpose* of the repo (push-only backup vs bidirectional sync), which was already in the agent's context but not applied to the troubleshooting path.
**Result:** ✅ Removed one line. Script fixed with a deletion, not a workaround.

---

## Case 003 — Right Tool for Anti-Bot Pages

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Scrape Google's CAPTCHA-protected flight results and Bilibili video pages
**Trigger:** Agent defaulted to built-in browser tools (puppeteer MCP) for web scraping, getting blocked immediately on Cloudflare-fronted sites. Agent kept retrying with different launch options instead of switching approach.
**Steer:** "Use the stealth scraper. We already have one running puppeteer-extra with stealth plugin. It's the first choice for any anti-bot site — not the fallback."
**Type:** Tool-myopia (agent had a superior tool available but defaulted to the generic one because it was "built-in")
**Could prompt template fix this?** Partially — a system prompt rule could say "prefer stealth scraper for scraping." But the agent had the knowledge that anti-bot sites exist and that the built-in browsers get blocked; it just didn't connect the dots in real time.
**Result:** ✅ Stealth scraper used for FlightAware, Bilibili, Google Flights. All pages rendered correctly. The skill documentation was updated so future sessions don't need this steer.
