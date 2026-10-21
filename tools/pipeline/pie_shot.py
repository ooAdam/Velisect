"""Through the Velisect editor's MCP (port 8010): start PIE, let it settle, level the view and save a 1920x1080 frame of
the game (HighResShot; the editor's image if that fails), stop PIE.
Usage: python pie_shot.py <out.png> [seconds]   (VS_SHOT_CMDS="cmd1;cmd2" runs console commands in PIE first)"""
import base64
import glob
import json
import shutil
import subprocess
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
# The game frame: through the editor's Python, level the player's view and ask for a high-res shot of it.
here = os.path.dirname(os.path.abspath(__file__))
shots = os.path.join(here, "..", "..", "Saved", "Screenshots")
before = set(glob.glob(os.path.join(shots, "**", "*.png"), recursive=True))
command = os.path.join(here, "..", "..", "Saved", "ToolLogs", "pie_shot_view.py")
open(command, "w").write("""import unreal
world = unreal.UnrealEditorSubsystem().get_game_world()
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=pc.get_control_rotation().yaw))
for cmd in %r:
    unreal.SystemLibrary.execute_console_command(world, cmd)
unreal.SystemLibrary.execute_console_command(world, "HighResShot 1920x1080")
""" % [c for c in os.environ.get("VS_SHOT_CMDS", "").split(";") if c.strip()])
subprocess.run([sys.executable, "-I", os.path.join(here, "uepy.py"), command], capture_output=True)
for _ in range(20):
    time.sleep(0.5)
    new = set(glob.glob(os.path.join(shots, "**", "*.png"), recursive=True)) - before
    if new:
        time.sleep(0.5)
        shutil.copyfile(max(new, key=os.path.getmtime), out)
        print("shot:", out)
        break
for item in ([] if new else call("CaptureEditorImage").get("result", {}).get("content", [])):
    if item.get("type") == "text" and '"mimeType"' in item.get("text", ""):
        image = json.loads(item["text"]).get("returnValue") or {}
        open(out, "wb").write(base64.b64decode(image.get("image", image)["data"]))
        print("shot:", out)
if not already:
    call("StopPIE")
