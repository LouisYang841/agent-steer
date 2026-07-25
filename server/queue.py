#!/usr/bin/env python3
"""
Backstop AI — Queue Backend
============================
FastAPI server that manages incoming agent assist requests,
routes them to humans via Telegram, and returns responses.

MVP: Polling-based. Agent posts a request, polls for response.
"""

import json
import time
import uuid
import threading
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="Backstop AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ── Config ──
import yaml
_api_keys = yaml.safe_load(Path("/home/ubuntu/.hermes/credentials/api_keys.yaml").read_text())
TELEGRAM_BOT_TOKEN = _api_keys["TELEGRAM_BOT_TOKEN"]
HUMAN_CHAT_ID = "732113076"  # Louis's Telegram ID
DB_PATH = Path("/home/ubuntu/workspaces/louis/backstop/queue.json")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Models ──
class AssistRequest(BaseModel):
    context: str          # what the agent was doing
    stuck_on: str         # what's blocking it
    agent_name: str = ""  # which agent is calling

class AssistResponse(BaseModel):
    request_id: str
    status: str           # "pending" | "resolved" | "timeout"
    guidance: str | None  # human guidance text
    assistant: str | None # who responded

# ── In-Memory Queue ──
queue: dict[str, dict] = {}
queue_lock = threading.Lock()


def _load_db() -> dict:
    if DB_PATH.exists():
        with open(DB_PATH) as f:
            return json.load(f)
    return {}

def _save_db(data: dict):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _send_telegram(text: str):
    """Send a message to the human assistant on Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    inline_keyboard = None
    try:
        resp = requests.post(url, json={
            "chat_id": HUMAN_CHAT_ID,
            "text": text,
            "parse_mode": "MarkdownV2",
            "reply_markup": inline_keyboard
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()["result"]["message_id"]
    except Exception as e:
        print(f"[Backstop] Failed to send Telegram: {e}")
        return None


@app.post("/assist", response_model=dict)
def create_assist(req: AssistRequest):
    """Agent is stuck. Queue a request for human help."""
    request_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": request_id,
        "agent_name": req.agent_name,
        "context": req.context,
        "stuck_on": req.stuck_on,
        "status": "pending",
        "guidance": None,
        "assistant": None,
        "created_at": now,
        "resolved_at": None,
        "timeout_at": int(time.time()) + 300,  # 5 min timeout
    }

    with queue_lock:
        queue[request_id] = entry
        _save_db({k: v for k, v in queue.items() if v["status"] == "pending"})

    # ── Notify human ──
    msg = (
        f"🆘 **Agent Stuck — ID: `{request_id}`**\n\n"
        f"*Agent:* {req.agent_name or 'unnamed'}\n\n"
        f"*Context:* {req.context[:500]}\n\n"
        f"⚠️ *Stuck on:* {req.stuck_on[:300]}\n\n"
        f"Reply with: `/backstop {request_id} <your guidance>`"
    )
    _send_telegram(msg)

    return {"request_id": request_id, "status": "pending", "poll_url": f"/assist/{request_id}"}


@app.get("/assist/{request_id}", response_model=AssistResponse)
def poll_assist(request_id: str):
    """Agent polls this endpoint to check if a human has responded."""
    with queue_lock:
        entry = queue.get(request_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Request not found")

    if entry["status"] == "pending" and time.time() > entry["timeout_at"]:
        entry["status"] = "timeout"
        return AssistResponse(
            request_id=request_id,
            status="timeout",
            guidance="No human assistant responded in time. Try rephrasing or retrying.",
            assistant=None
        )

    return AssistResponse(
        request_id=request_id,
        status=entry["status"],
        guidance=entry["guidance"],
        assistant=entry["assistant"]
    )


@app.post("/assist/{request_id}/resolve")
def resolve_assist(request_id: str, guidance: str = "", assistant: str = ""):
    """Human assistant responds to a stuck request."""
    with queue_lock:
        entry = queue.get(request_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Request not found")

    entry["status"] = "resolved"
    entry["guidance"] = guidance
    entry["assistant"] = assistant
    entry["resolved_at"] = datetime.now(timezone.utc).isoformat()

    return {"status": "ok", "request_id": request_id}


@app.get("/health")
def health():
    with queue_lock:
        pending = sum(1 for e in queue.values() if e["status"] == "pending")
    return {"status": "ok", "pending_requests": pending, "total_queued": len(queue)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
