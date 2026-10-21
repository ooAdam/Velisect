# Next session: start here

Overwritten at every milestone commit. Keep it to about ten lines.

- **Open the chat in `C:\Users\adanr\velisect`** so CLAUDE.md and `.mcp.json` load. Mournhollow's editor owns MCP port 8000; Velisect's is 8010.
- **M3 (out of OneDrive) committed:** the project moved from OneDrive to `C:\Users\adanr\velisect`; build output is back in `Packaged/` like Mournhollow; compile, 2 tests and package pass from the new path, and the exe loads Level 1 with no errors (checked by hand: launch, read its log).
- **Pushed to https://github.com/ooAdam/Velisect** (main, LFS 506 MB); from now on every milestone commit is pushed. A fresh clone needs `git lfs install` first.
- **M1 (first playable) and M2 (the workflow):** true-FP soldier with the rifle, 4 zombies, Backrooms Level 1 (`history.md`); the loop is `node tools/unreal.mjs compile test package`, with `py`/`blender`/`shot` for editor work (`architecture.md`, `mcp.md`).
- **Next feature (the user's pick): the loot and extraction loop** — lootable crates (the Vicevoxel props are placed but inert), an inventory/carry limit, an extraction point that ends the run with what you took, and a way back in. Ask the user how loot should work (types, value, weight) before building.
- **Open, small:** no automated smoke run of the packaged game yet (Mournhollow's `smoke` is the model); the zombie has no hit reaction or sounds; no footsteps; legs never show when looking down (accepted); hearing radius 1800 pulls most of the floor (tune in play).
- **Ask the user how M1 plays:** aim framing (`player_cfg.json` → `ue_tune_player.py`), zombie speed/damage (`BP_Zombie`), light and fog levels.
- **Notes for the loot feature:** `design.md`, `architecture.md` (C++ classes, props, level script); `gotchas.md` before any build trouble.
