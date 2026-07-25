#!/usr/bin/env python3
"""
Backstop AI — Test Client
===========================
Simulates an AI agent calling for help, then waits for a human to respond.

Usage:
  python test_client.py "I'm trying to install Docker" "apt-get says 'no such package'"
"""

import sys
import time
import requests

BACKSTOP_URL = "http://localhost:8765"

def test_assist(context: str, stuck_on: str):
    """Simulate an agent getting stuck."""
    print(f"\n🤖 Agent: 'I'm stuck!'\n   Context: {context}\n   Blocked: {stuck_on}\n")

    # POST request
    resp = requests.post(f"{BACKSTOP_URL}/assist", json={
        "context": context,
        "stuck_on": stuck_on,
        "agent_name": "TestAgent-v0"
    })
    result = resp.json()
    request_id = result["request_id"]
    print(f"📨 Request queued: {request_id}")
    print(f"⏳ Waiting for human assistant (on Telegram)...\n")

    # Poll for response
    start = time.time()
    dots = 0
    while time.time() - start < 300:
        resp = requests.get(f"{BACKSTOP_URL}/assist/{request_id}")
        data = resp.json()

        if data["status"] == "resolved":
            print(f"\n✅ HUMAN RESPONDED (in {time.time() - start:.1f}s):")
            print(f"   Assistant: {data['assistant']}")
            print(f"   Guidance:  {data['guidance']}\n")
            return
        elif data["status"] == "timeout":
            print("\n⏰ Timeout — no human responded.\n")
            return

        dots = (dots + 1) % 4
        print(f"\r   Waiting{'.' * dots}   ", end="", flush=True)
        time.sleep(2)

    print("\n⏰ Global timeout.\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_client.py '<context>' '<stuck_on>'")
        sys.exit(1)

    # Check server is up
    try:
        health = requests.get(f"{BACKSTOP_URL}/health", timeout=3)
        print(f"🔌 Server status: {health.json()}")
    except Exception:
        print("❌ Server not running! Start with: bash start.sh")
        sys.exit(1)

    test_assist(sys.argv[1], sys.argv[2])
