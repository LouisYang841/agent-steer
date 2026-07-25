#!/usr/bin/env python3
"""
Backstop AI — Telegram Relay
==============================
Long-polling Telegram bot that watches for human assistant responses.
When Louis replies "/backstop <id> <guidance>", it resolves the request.

Run: python relay.py &
"""

import re
import time
from pathlib import Path
import requests

import yaml
from pathlib import Path

_api_keys = yaml.safe_load(Path("/home/ubuntu/.hermes/credentials/api_keys.yaml").read_text())
TELEGRAM_BOT_TOKEN = _api_keys["TELEGRAM_BOT_TOKEN"]
BACKSTOP_URL = "http://localhost:8765"
HUMAN_CHAT_ID = 732113076

# ── Parse /backstop command ──
BACKSTOP_RE = re.compile(r'^/backstop\s+(\S+)\s+(.+)', re.DOTALL)


def resolve_request(request_id: str, guidance: str):
    """Tell the Backstop server that a human has responded."""
    try:
        resp = requests.post(
            f"{BACKSTOP_URL}/assist/{request_id}/resolve",
            params={"guidance": guidance, "assistant": "Louis"},
            timeout=5
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Relay] Failed to resolve {request_id}: {e}")
        return False


def poll_telegram(offset: int = 0):
    """Long-poll Telegram for new messages."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30, "allowed_updates": ["message"]}

    try:
        resp = requests.get(url, params=params, timeout=35)
        resp.raise_for_status()
        data = resp.json()

        if not data["ok"]:
            return offset

        for update in data["result"]:
            offset = max(offset, update["update_id"] + 1)

            msg = update.get("message", {})
            chat_id = msg.get("chat", {}).get("id", 0)
            text = msg.get("text", "")

            # Only respond to Louis
            if chat_id != HUMAN_CHAT_ID:
                continue

            match = BACKSTOP_RE.match(text)
            if match:
                request_id = match.group(1)
                guidance = match.group(2).strip()

                print(f"[Relay] Resolving {request_id}: {guidance[:80]}...")
                if resolve_request(request_id, guidance):
                    # Send confirmation
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": HUMAN_CHAT_ID,
                            "text": f"✅ Resolved `{request_id}` — agent notified.",
                            "parse_mode": "MarkdownV2"
                        },
                        timeout=5
                    )

        return offset

    except Exception as e:
        print(f"[Relay] Poll error: {e}")
        time.sleep(5)
        return offset


if __name__ == "__main__":
    print("[Relay] Backstop Telegram relay starting...")
    print(f"[Relay] Watching chat {HUMAN_CHAT_ID} for /backstop commands")

    last_offset = 0
    while True:
        try:
            last_offset = poll_telegram(last_offset)
        except KeyboardInterrupt:
            print("[Relay] Shutting down.")
            break
        except Exception as e:
            print(f"[Relay] Unexpected error: {e}")
            time.sleep(10)
