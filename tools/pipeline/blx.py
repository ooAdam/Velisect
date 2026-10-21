"""Run a Blender pipeline script in a fresh headless Blender (factory settings, no add-ons or open window needed).
Usage: python blx.py script.py [timeout_seconds]   -- prints the script's output; exits non-zero if the script raised.
Blender: $BLENDER, else the newest C:\\Program Files\\Blender Foundation\\Blender <ver>\\blender.exe."""
import glob, os, re, subprocess, sys

def blender_exe():
    if os.environ.get("BLENDER"):
        return os.environ["BLENDER"]
    found = glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe")
    if not found:
        sys.exit("No Blender found: set BLENDER to blender.exe")
    return max(found, key=lambda p: [int(n) for n in re.findall(r"\d+", os.path.basename(os.path.dirname(p)))])

script = os.path.abspath(sys.argv[1])
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 900
r = subprocess.run([blender_exe(), "--background", "--factory-startup", "--python-exit-code", "1", "--python", script],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
# Drop Blender's own startup/shutdown chatter; keep the script's prints and any traceback.
noise = re.compile(r"^(Blender \d|Read prefs|Read blend|Blender quit|$)")
print("\n".join(l for l in r.stdout.splitlines() if not noise.match(l)))
if r.returncode:
    print(r.stderr[-4000:], file=sys.stderr)
    sys.exit(r.returncode)
