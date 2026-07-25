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

**Why this case matters:** This is the purest example of agent steer. The agent was trapped in "I need to modify the codebase" thinking. The human said "don't modify anything — just write to a file that the agent already reads." This kind of lateral thinking is exactly what makes human judgment valuable: seeing the existing system from outside, finding the path of least resistance that happens to be invisible from inside.

---

## Case 002 — OOM Kill Without Restart

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Diagnose why SSH and HY2 tunnel disconnected
**Trigger:** Agent explored AWS incident reports, tailed sshd logs, found no network issues. Frozen on "everything looks fine" while missing the kernel-level event.
**Steer:** "Check dmesg for OOM killer." → Agent found `oom-kill:constraint=CONSTRAINT_NONE … task=hermes, pid=100908` — the gateway process had been killed by the kernel, then auto-restarted by systemd 5 seconds later. Root cause found in 30 seconds.
**Type:** Scope-blindness (agent searched network/logs/processes but never the kernel ring buffer)
**Could prompt template fix this?** No — knowing to check `dmesg` for OOM requires architectural intuition about what a "network dropped + SSH disconnected + everything looks fine" pattern actually means: a process was killed, not a network failure.
**Result:** ✅ Root cause identified. Agent then killed 6 unnecessary services (cups, fwupd, ModemManager, etc.), freed ~100MB RAM.

---

## Case 003 — Unnecessary Git Pull in Backup Script

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Fix a cron backup script that was failing with exit code 128
**Trigger:** Agent proposed changing `git pull --rebase` to `git pull --rebase --autostash`, adding complexity to handle a case that shouldn't exist.
**Steer:** "We don't need to pull at all. It's a backup repo, not a sync repo. Just push."
**Type:** Over-engineering (agent defaulted to "fix the pull" instead of "why are we pulling")
**Could prompt template fix this?** No — requires understanding the *purpose* of the repo (backup-only, not bidirectional sync), which is contextual knowledge the agent has access to but didn't apply.
**Result:** ✅ Removed the pull line. Script fixed with one deletion, not one addition.

---

## Case 004 — Web Search API Landscape

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Research whether Google provides search APIs for AI agents
**Trigger:** Agent found Google's Custom Search JSON API is shutting down Jan 2027, listed alternatives (Brave, SerpAPI, etc.). But missed the bigger story: Google killed its public API while keeping internal ones for Gemini.
**Steer:** "Is there a narrative here? Google dogfooding its own search API for Gemini while cutting off external access."
**Type:** Perspective-gap (agent compiled facts but missed the irony/narrative)
**Could prompt template fix this?** No — requires human judgment to recognize "these three disconnected facts form a story," not just a list.
**Result:** ✅ Agent reframed from "here are 5 alternatives" to "Google's hypocrisy: they use their own search API for Gemini but won't let you."

---

## Case 005 — Human-as-API Moral Shock

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Explain what CAPTCHA-solving APIs are
**Trigger:** Agent correctly identified CapSolver, 2Captcha, Anti-Captcha as legitimate businesses. But user was morally unsettled — "this is like 40k servitors." Agent was factual but missed the depth of the reaction.
**Steer:** User wanted the agent to *feel* the weight of "humans packaged as API endpoints," not just describe it. The conversation spiraled into RentAHuman, WURK, Human API — all real companies doing exactly this.
**Type:** Empathy-gap (agent was technically accurate but couldn't match the user's visceral "this is Warhammer 40k in real life" reaction without being prompted deeper)
**Could prompt template fix this?** No — emotional resonance requires shared context between human and agent, not a better instruction set.
**Result:** ✅ Conversation evolved from a query answer into a shared moral exploration.

---

## Case 006 — Design Philosophy Clash

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Help build a business idea for "AI agent steering as a service"
**Trigger:** Agent produced a full business plan, landing page, MCP server, and Telegram relay. User's other AI assistant (GLM) pointed out this was premature — user should be writing an essay and doing small experiments, not building a platform.
**Steer:** "GLM says we're jumping too fast. Put the landing page aside. Make this an open-source experiment, not a company."
**Type:** Pace-correction (agent defaulted to "full send" when user should have been in "exploration" mode)
**Could prompt template fix this?** Partially — a prompt flag like "I'm exploring, not building" might have helped. But the human needed the external voice (GLM) to trigger the course correction, not just a different agent mode.
**Result:** ✅ Pivoted from "Backstop AI startup" to "agent-steer open-source experiment."

---

## Case 007 — Git SSH Auth Without the Right Token

**Date:** 2026-07-25
**Agent:** Hermes (ds v4 pro)
**Task:** Push the agent-steer repo to GitHub
**Trigger:** GitHub PAT was expired. SSH deploy key was repo-specific (hermesAgentMemoryVault only). Agent tried both, got stuck.
**Steer:** "Ask Louis for a fresh token. Classic PAT, 7-day expiry, full repo scope."
**Type:** Tool-stuck (agent had the "ask user for credential" capability but hesitated)
**Could prompt template fix this?** No — requires knowing when to stop troubleshooting and say "I need a new credential from you."
**Result:** ✅ User provided token, push succeeded, repo live at github.com/LouisYang841/agent-steer

---
