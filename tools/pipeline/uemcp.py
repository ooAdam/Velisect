"""Minimal client for the UE 5.8 ModelContextProtocol plugin (streamable HTTP at 127.0.0.1:8000/mcp).
Usage:
  python uemcp.py list                       -> tools/list
  python uemcp.py call <tool> '<json args>'  -> tools/call
"""
import json, sys, urllib.request

URL = "http://127.0.0.1:8010/mcp"  # Velisect editor (8000 belongs to another project)
HEAD = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def post(payload, session=None):
    h = dict(HEAD)
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        sid = r.headers.get("Mcp-Session-Id") or session
        body = r.read().decode("utf-8", "replace")
    msgs = []
    for line in body.splitlines():
        if line.startswith("data:"):
            msgs.append(json.loads(line[5:].strip()))
    if not msgs and body.strip():
        msgs.append(json.loads(body))
    return sid, msgs


def session():
    sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "velisect-claude", "version": "1"}}})
    try:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    except Exception:
        pass
    return sid


def last_result(msgs):
    for m in reversed(msgs):
        if "result" in m or "error" in m:
            return m
    return msgs[-1] if msgs else {}


if __name__ == "__main__":
    sid = session()
    if sys.argv[1] == "list":
        _, msgs = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
    else:
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        _, msgs = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": sys.argv[2], "arguments": args}}, sid)
    result = last_result(msgs)
    # Optional 4th arg: save any returned image content to that path instead of printing base64.
    if len(sys.argv) > 4:
        import base64
        for item in result.get("result", {}).get("content", []):
            if item.get("type") == "image":
                open(sys.argv[4], "wb").write(base64.b64decode(item["data"]))
                item["data"] = f"<saved to {sys.argv[4]}>"
            elif item.get("type") == "text" and '"mimeType"' in item.get("text", ""):
                payload = json.loads(item["text"]).get("returnValue") or {}
                image = payload.get("image", payload)
                if image.get("data"):
                    open(sys.argv[4], "wb").write(base64.b64decode(image["data"]))
                    item["text"] = f"<image saved to {sys.argv[4]}>"
    print(json.dumps(result, indent=1))
