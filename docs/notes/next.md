# Next session: start here

Overwritten at every milestone commit. Keep it to about ten lines.

- **Open the chat in the project folder** (`C:\Users\adanr\OneDrive\Documents\Unreal Projects\Velisect`) so CLAUDE.md and `.mcp.json` load. Mournhollow's editor owns MCP port 8000; Velisect's is 8010.
- **M1 (first playable) and M2 (the workflow) committed.** The game: true-FP soldier with the rifle, 4 zombies, Backrooms Level 1 (`history.md`). The loop: `node tools/unreal.mjs compile test package`, `py`/`blender`/`shot` for editor work (`architecture.md`, `mcp.md`). 2 content tests pass (`tests.md`); the packaged exe loads Level 1 with no errors (M2 checked by hand: launch, read its log).
- **Next feature (the user's pick): the loot and extraction loop** — lootable crates (the Vicevoxel props are placed but inert), an inventory/carry limit, an extraction point that ends the run with what you took, and a way back in. Ask the user how loot should work (types, value, weight) before building.
- **Open, small:** the project lives in OneDrive, which syncs Saved/Intermediate (GBs) and once locked a build (ask the user about moving it, e.g. to `C:\Users\adanr\velisect`); no automated smoke run of the packaged game yet (Mournhollow's `smoke` is the model); the zombie has no hit reaction or sounds; no footsteps; legs never show when looking down (accepted); hearing radius 1800 pulls most of the floor (tune in play); the remote isn't set up (ask before creating a GitHub repo; GitHub CLI isn't installed).
- **Ask the user how M1 plays:** aim framing (`player_cfg.json` → `ue_tune_player.py`), zombie speed/damage (`BP_Zombie`), light and fog levels.
- **Notes for the loot feature:** `design.md`, `architecture.md` (C++ classes, props, level script); `gotchas.md` before any build trouble.
