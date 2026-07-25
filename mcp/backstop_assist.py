#!/usr/bin/env python3
"""
Backstop AI — MCP Server
=========================
MCP tool: backstop_assist(context, stuck_on) → human_guidance

Agents call this when they're stuck and need a human to unblock them.
The request is routed through the Backstop queue, a human sees it on Telegram,
responds with guidance, and the agent gets back the response.

Usage in MCP config.yaml:
  - name: backstop
    command: uv
    args: [run, --directory, /home/ubuntu/workspaces/louis/backstop, mcp_server.py]
"""

import sys
import time
import json
import os

# ── Try FastMCP, fall back to stdio JSON-RPC ──
try:
    from mcp.server.fastmcp import FastMCP
    USE_FASTMCP = True
except ImportError:
    USE_FASTMCP = False

BACKSTOP_URL = os.environ.get("BACKSTOP_URL", "http://localhost:8765")
POLL_INTERVAL = 2  # seconds between polls
MAX_WAIT = 300     # max seconds to wait for human


def call_backstop(context: str, stuck_on: str, agent_name: str = "", max_wait: int = MAX_WAIT) -> dict:
    """Send a stuck request to Backstop, poll until human responds or timeout."""
    import urllib.request
    import urllib.error

    # POST the assist request
    payload = json.dumps({
        "context": context,
        "stuck_on": stuck_on,
        "agent_name": agent_name
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKSTOP_URL}/assist",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            request_id = result["request_id"]
    except Exception as e:
        return {"success": False, "error": f"Failed to create assist request: {e}"}

    # Poll for response
    start = time.time()
    while time.time() - start < max_wait:
        try:
            with urllib.request.urlopen(f"{BACKSTOP_URL}/assist/{request_id}", timeout=5) as resp:
                result = json.loads(resp.read().decode())

                if result["status"] == "resolved":
                    return {
                        "success": True,
                        "guidance": result["guidance"],
                        "assistant": result["assistant"],
                        "request_id": request_id,
                        "wait_seconds": round(time.time() - start, 1)
                    }
                elif result["status"] == "timeout":
                    return {
                        "success": False,
                        "error": result.get("guidance", "No human responded in time"),
                        "request_id": request_id
                    }
        except Exception:
            pass

        time.sleep(POLL_INTERVAL)

    return {"success": False, "error": "Timed out waiting for human", "request_id": request_id}


# ── FastMCP mode ──
if USE_FASTMCP:
    mcp = FastMCP("Backstop AI")

    @mcp.tool()
    async def backstop_assist(context: str, stuck_on: str, agent_name: str = "") -> str:
        """
        CALL WHEN YOU ARE STUCK. A human assistant will see your context and
        give you guidance to unblock you.

        Args:
            context: What you were trying to do (e.g., "I was installing nginx")
            stuck_on: What's blocking you (e.g., "Port 80 already in use, I don't know how to resolve this")
            agent_name: Optional identifier for the calling agent

        Returns:
            Human guidance text to help you continue.
        """
        result = call_backstop(context, stuck_on, agent_name)
        if result["success"]:
            return result["guidance"]
        return f"[Backstop: {result['error']}]"


# ── Stdio JSON-RPC fallback ──
else:
    def handle_request(method: str, params: dict) -> dict:
        if method == "tools/list":
            return {
                "tools": [{
                    "name": "backstop_assist",
                    "description": "When you are stuck and need a human to help you decide or unblock you. A human assistant will see your context and reply with guidance.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "What the agent was trying to do"
                            },
                            "stuck_on": {
                                "type": "string",
                                "description": "What is blocking the agent"
                            },
                            "agent_name": {
                                "type": "string",
                                "description": "Optional agent name for logging"
                            }
                        },
                        "required": ["context", "stuck_on"]
                    }
                }]
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            if tool_name == "backstop_assist":
                result = call_backstop(
                    args.get("context", ""),
                    args.get("stuck_on", ""),
                    args.get("agent_name", "")
                )
                return {"content": [{"type": "text", "text": json.dumps(result)}]}
        return {"error": f"Unknown method: {method}"}

    def main():
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                method = request.get("method", "")
                params = request.get("params", {})
                request_id = request.get("id")

                result = handle_request(method, params)
                response = {"jsonrpc": "2.0", "result": result, "id": request_id}
                print(json.dumps(response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -1, "message": str(e)},
                    "id": request.get("id") if 'request' in dir() else None
                }
                print(json.dumps(error_response), flush=True)

    if __name__ == "__main__":
        main()
