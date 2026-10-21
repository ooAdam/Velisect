"""Run a Python file inside the Velisect Unreal Editor via the PythonScriptPlugin remote execution protocol.
Usage: python uepy.py script.py"""
import sys, time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution as rx

script = sys.argv[1]
cfg = rx.RemoteExecutionConfig()
r = rx.RemoteExecution(cfg)
r.start()
try:
    node = None
    for _ in range(60):
        nodes = [n for n in r.remote_nodes if n.get("project_name", "").lower() == "velisect"]
        if nodes:
            node = nodes[0]
            break
        time.sleep(0.5)
    if not node:
        print("No Velisect editor node found; nodes:", r.remote_nodes)
        sys.exit(2)
    r.open_command_connection(node["node_id"])
    res = r.run_command(script, unattended=True, exec_mode=rx.MODE_EXEC_FILE)
    for o in res.get("output", []):
        print(o.get("output", "").rstrip())
    if not res.get("success"):
        print("FAILED:", res.get("result"))
        sys.exit(1)
finally:
    r.stop()
