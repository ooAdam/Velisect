"""Through the Velisect editor's MCP (port 8010): start PIE, let it settle, save the editor's image, stop PIE.
Usage: python pie_shot.py <out.png> [seconds]"""
import base64
import json
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # run with python -I, which drops the script's folder
import uemcp  # noqa: E402

out = sys.argv[1]
settle = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
sid = uemcp.session()


def call(tool, args=None):
    _, msgs = uemcp.post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "call_tool", "arguments": {
        "toolset_name": "EditorToolset.EditorAppToolset", "tool_name": tool, "arguments": args or {}}}}, sid)
    return uemcp.last_result(msgs)


already = '"returnValue":true' in json.dumps(call("IsPIERunning")).replace(" ", "").replace("\\", "")
if not already:
    call("StartPIE", {"options": {"bSimulate": False, "playMode": "PlayMode_InViewPort", "warmupSeconds": settle}})
else:
    time.sleep(settle)
for item in call("CaptureEditorImage").get("result", {}).get("content", []):
    if item.get("type") == "text" and '"mimeType"' in item.get("text", ""):
        image = json.loads(item["text"]).get("returnValue") or {}
        open(out, "wb").write(base64.b64decode(image.get("image", image)["data"]))
        print("shot:", out)
if not already:
    call("StopPIE")
