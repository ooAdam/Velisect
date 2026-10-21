"""Run a Python file inside Blender through the ahujasid 'MCP for Blender' add-on socket (port 9876).
Usage: python blx.py script.py [timeout_seconds]   -- prints whatever the script print()s."""
import json, socket, sys

code = open(sys.argv[1], encoding="utf-8").read()
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 900
req = json.dumps({"type": "execute_code", "params": {"code": code}})
with socket.create_connection(("127.0.0.1", 9876), timeout=timeout) as s:
    s.sendall(req.encode())
    buf = b""
    while True:
        c = s.recv(1 << 20)
        if not c:
            break
        buf += c
        try:
            resp = json.loads(buf.decode("utf-8"))
            break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
if resp.get("status") == "success":
    print(resp["result"].get("result", resp["result"]))
else:
    print("ERROR:", resp.get("message"))
    sys.exit(1)
