# Velisect: notes for Claude

Lives at `C:\Users\adanr\velisect` (moved out of OneDrive in M3; never put it back in a synced folder). A first-person shooter set in the Backrooms: go in, extract good loot, come back out. Unreal 5.8 C++ (this folder is the Unreal project) with Blender as the asset factory. The user's other game, **Mournhollow** (`C:\Users\adanr\mournhollow`), is unrelated: never touch its files or its editor. README.md is the player-facing description and controls.

## Spend tokens like they're the user's (the user's ask)
- **Start a session with `docs/notes/next.md`** (about ten lines: where things stand, what's next, which notes to open), then only the notes it names.
- **Read the notes on demand, not up front.** Open only the file the task touches, and only the part you need (Grep first):

  | File | When |
  |---|---|
  | `design.md` | the user's vision and hard requirements, the inspiration images, what's in and out of scope |
  | `architecture.md` | source assets and where they live, the pipeline (Blender → SourceArt → Content), every C++ class, content layout, commands |
  | `animation.md` | `UVelisectAnimInstance` (code-driven layers, no AnimBP), the clip map, the aim and camera tuning in `BP_Player` |
  | `gotchas.md` | traps already hit, by topic (`Grep "^## "` for the map): read the topic before debugging a build, MCP, Blender or animation problem |
  | `mcp.md` | the Unreal MCP (port 8010), the Blender socket, Python remote execution, and how to call each |
  | `tests.md` | what each automation test checks and its mutation result |
  | `history.md` | the milestone table |
- **Never print a long output.** `node tools/unreal.mjs` is quiet: each step's whole output goes to `Saved/ToolLogs/<step>.log`; grep it for more. Long output of your own goes to a scratchpad file.
- **Look, don't guess, but look cheaply:** `node tools/unreal.mjs shot <name>` (editor open) saves one PIE image to `Saved/ToolLogs/shots/`. One image per check, of what changed.
- **Run the smallest check that proves the change:** `VS_TEST=Velisect.Content node tools/unreal.mjs test` for one group; the full `test` and `package` once, before the commit.
- **Notes stay short:** after a milestone add one row to `history.md` and the facts a future session needs to the topic file, a sentence or two each. Details go in the commit message. Don't restate what the code says.
- **Don't re-read files you just wrote, and don't re-derive what's settled.** Prefer Grep with a narrow pattern; read big files by line range (`VelisectCharacter.cpp`).
- **A fresh session per feature** is cheaper than one long session that compacts. At each milestone commit, overwrite `docs/notes/next.md`: what's done, what's next, open problems, uncommitted work that isn't ours, and which notes the next task needs.
- **Model per task (the user picks):** routine tuning, data and small fixes run fine on Sonnet or lower effort; new systems and animation or AI problems want Opus at high effort.

## The user's loop
- **The game is the packaged exe** `Packaged/Windows/Velisect.exe` (Development), started with `Play Velisect.bat` or `npm run play`. Play-In-Editor is for Claude's checks.
- The user asks → Claude builds it: C++ in `Source/Velisect`, editor automation in `tools/pipeline/ue_*.py` (run in the open editor with `node tools/unreal.mjs py <file>`), Blender work through `tools/pipeline/*.py` (`node tools/unreal.mjs blender <file>`) → test, package, look → the user plays the exe.
- **Inspect → Plan → Checkpoint → Implement → Verify → Commit.** Present findings before large changes; start from a clean tree; verify with `test`, a `shot` of what changed, and `package`. **Commit at each verified milestone** (message `M<n>: <what>`, ending with the Co-Authored-By line). Push only once the user has set up the remote and said to.
- **Commands** (`node tools/unreal.mjs <steps>`): `compile`, `test`, `package`, `play`, `open` (editor with MCP on 8010), `py <file>`, `blender <file>`, `shot [name]`. `compile` and `package` need the Velisect editor and the game closed: **ask the user to close them, never kill them** (the tool refuses while they're open). A C++ change reaches the game only through `package`; reaches the editor only after `compile` with the editor closed.

## Rules
- Gameplay is C++; Blueprints are thin data subclasses (`BP_Player`, `BP_Zombie`, `BP_GameMode`) holding tuned values. **No Blueprint graphs** without asking. Python only for editor automation; Blender is the asset factory.
- Tuned values live in data, not code: `tools/pipeline/player_cfg.json` → `ue_tune_player.py` writes them onto `BP_Player`. Change the json, run the script, commit both.
- `Content/Velisect` is committed (Git LFS) and is the source of truth for imported and tuned assets; `SourceArt/` holds Blender's exports and is regenerated (only `Backrooms/` and `Audio/` are committed). The raw asset library (Mixamo FBX, rifle, crates, radios) stays outside the repo at the path in `architecture.md`; never delete or move it.
- Never edit Unreal assets from two places at once (no `py` scripts while the user has unsaved changes in the editor).
- Report failed tests as they are. Never claim something works without verifying it (test result, a shot, the log).
- Ask before closing the user's apps; never touch the Mournhollow editor (port 8000) or its project.

## Traps that cost the most (the rest in `gotchas.md`)
- MCP port **8000 is Mournhollow's editor**. Velisect's is **8010**. Check before any MCP call.
- Builds: Mournhollow's Live Coding blocks UBT on this engine unless `-NoHotReloadFromIDE` (the tool passes it).
- `package` fails on any "Failed to compile Material" (the cook itself doesn't): a Masks sampler needs a linear default texture, never `WhiteSquareTexture`.
- Bash heredocs choke on apostrophes and backslashes in scripts: write scripts with the Write tool and run the file.
- Mixamo in UE: bones import lowercase (`spine`, `righthand`); find them with `Velisect::FindBone`. The spine's aim pitch is inverted (`AimPitchScale = -1`).
