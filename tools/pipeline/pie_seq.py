"""In the open editor (MCP 8010): start PIE, level the view, run console commands, then save N HighResShots spaced in real
time to <out_prefix>_NN.png (e.g. "slomo 0.2;VsReload" to step through a reload). Stops PIE when done.
Usage: python -I pie_seq.py <out_prefix> "<cmd1;cmd2>" <count> <interval_s> [first_delay_s]"""
import glob, json, os, shutil, subprocess, sys, time
PIPE = r"C:\Users\adanr\velisect\tools\pipeline"
sys.path.insert(0, PIPE)
import uemcp

prefix, cmds, count, interval = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
first = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
for _ in range(120):
    try:
        sid = uemcp.session(); break
    except Exception:
        time.sleep(2)

def call(tool, args=None):
    _, msgs = uemcp.post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "call_tool", "arguments": {
        "toolset_name": "EditorToolset.EditorAppToolset", "tool_name": tool, "arguments": args or {}}}}, sid)
    return uemcp.last_result(msgs)

def editor_py(code):
    f = os.path.join(r"C:\Users\adanr\velisect\Saved\ToolLogs", "pie_seq_cmd.py")
    open(f, "w").write(code)
    return subprocess.run([sys.executable, "-I", os.path.join(PIPE, "uepy.py"), f], capture_output=True, text=True).stdout

running = '"returnValue":true' in json.dumps(call("IsPIERunning")).replace(" ", "").replace("\\", "")
if not running:
    call("StartPIE", {"options": {"bSimulate": False, "playMode": "PlayMode_InViewPort", "warmupSeconds": 6}})
shots_dir = r"C:\Users\adanr\velisect\Saved\Screenshots"
editor_py("""import unreal
world = unreal.UnrealEditorSubsystem().get_game_world()
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=pc.get_control_rotation().yaw))
for cmd in %r:
    unreal.SystemLibrary.execute_console_command(world, cmd)
""" % [c for c in cmds.split(";") if c.strip()])
time.sleep(first)
shot_cmd = """import unreal
world = unreal.UnrealEditorSubsystem().get_game_world()
unreal.SystemLibrary.execute_console_command(world, "HighResShot 1280x720")
"""
taken = []
for i in range(count):
    t0 = time.time()
    before = set(glob.glob(os.path.join(shots_dir, "**", "*.png"), recursive=True))
    editor_py(shot_cmd)
    for _ in range(40):
        time.sleep(0.1)
        new = set(glob.glob(os.path.join(shots_dir, "**", "*.png"), recursive=True)) - before
        if new:
            time.sleep(0.3)
            out = f"{prefix}_{i:02d}.png"; shutil.copyfile(max(new, key=os.path.getmtime), out); taken.append(out); break
    time.sleep(max(interval - (time.time() - t0), 0))
editor_py("""import unreal
world = unreal.UnrealEditorSubsystem().get_game_world()
unreal.SystemLibrary.execute_console_command(world, "slomo 1")
""")
call("StopPIE")
print("\n".join(taken))
