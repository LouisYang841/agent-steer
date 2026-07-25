# agent-steer

> **An experiment in API-fying human judgment.**
>
> What if the most valuable thing a human could do for an AI agent
> wasn't "execute this task" — but "tell me which way to go"?

---

## The Big Idea

Every intellectual worker will become an API endpoint.

Not "might become." Not "in the far future."**Will become.** The evidence is already here, strung together across three tiers:

| Tier | What | Status |
|------|------|--------|
| Low | CAPTCHA solving (2Captcha, CapSolver) — a human reads an image, clicks a button, returns a token | ✅ Exists |
| Mid | Data labeling (Scale AI, Surge) — humans annotate training data through structured interfaces | ✅ Exists |
| High | **Agent steering** — a human watches an agent's reasoning in real-time, gives judgment when stuck | ❌ Does not exist yet |

The third tier is the frontier.

When an AI agent hits an edge case, loops endlessly, or faces an ambiguous decision, it needs something no model can provide: **taste, context, and a human's "not sure, but try this instead."**

This repo is a working prototype of that third tier.

---

## What's In Here

```
agent-steer/
├── mcp/backstop_assist.py      ← MCP tool exposed to AI agents
├── server/queue.py             ← FastAPI queue backend
├── relay/telegram_relay.py     ← Telegram bridge to human assistant
├── examples/test_client.py     ← Simulate an agent calling for help
├── docs/landing.html           ← Landing page (reference)
└── requirements.txt
```

### The Flow

```
AI Agent is stuck
    │
    ├─→ POST /assist {context, stuck_on}
    │
    ├─→ Server queues request, pings Telegram
    │
    ├─→ Human sees context, replies with guidance
    │
    ├─→ Agent polls GET /assist/{id}, gets back guidance
    │
    └─→ Agent continues execution ✅
```

**From the agent's perspective: one function call.**
**From the human's perspective: one Telegram reply.**

---

## Why This Matters Now

1. **EU AI Act (Article 53)** — Mandates human oversight for high-risk AI agents. Enforcement begins 2026–2027. Every enterprise agent deployment will need a human in the loop.

2. **Agents are getting more autonomous** — but autonomy means deeper edge cases. When an agent that normally handles 99% of tasks hits the 1% it can't, who do you call?

3. **"Human-in-the-loop" is currently a governance checkbox, not a service.** Tools like LangGraph provide the button. This project asks: what if someone else presses it?

---

## Run It

```bash
# 1. Install
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Start server
cd server && uvicorn queue:app --port 8765 &

# 3. Start Telegram relay
cd relay && python telegram_relay.py &

# 4. Test
python examples/test_client.py \
  "I'm trying to deploy Docker" \
  "Port 80 is already in use and I don't know what's safe to kill"
```

---

## Status

This is an **experiment**, not a company.

It grew out of a real daily workflow: I (a human) steer my AI agent (Hermes) through its confusion every day. I realized: this is a skill, this is valuable, and this can be packaged.

**Built in an afternoon.** MCP protocol, FastAPI queue, Telegram relay. The whole stack is ~300 lines of Python.

What happens next depends on whether anyone else finds this useful.

---

## The Author's Real Position

I think "agent steering as a service" will become a real category.

I think the big players (Cloudflare, OpenAI, Anthropic) will build the infrastructure.

But I think the first working prototype — the thing that proves human judgment can be API-fied — can be built by one person, with one agent, in one afternoon.

This is that prototype.

---

*If this resonates, open an issue. If you want to run a steer experiment with your own agent, the code works today. If you think this is overblown, tell me why — I'm genuinely curious where the blind spots are.*
