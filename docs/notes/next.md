# Next session: start here

Overwritten at every milestone commit. Keep it to about ten lines.

- **Open the chat in `C:\Users\adanr\velisect`** so CLAUDE.md and `.mcp.json` load. Mournhollow's editor owns MCP port 8000; Velisect's is 8010.
- **M4 (Valorant viewmodel) committed and pushed:** first-person arms and rifle on the camera, framed from the user's reference; left hand grips the foregrip (mirrored right-hand grip + IK); sprint hold, sway, kick; the black vest-strap lines are gone. Tests 2/2, package ok, packaged exe loads Level 1 clean. How it works: `animation.md`; tuning: `player_cfg.json` -> `viewmodel` -> `ue_tune_player.py`.
- **Ask the user how M4 plays:** framing (move `viewmodel.frame` spots or `aim_range`), grip (`left_grip`, `left_twist`, `left_elbow`), sprint tilt, sway strength. Mixamo's reload swings the left arm across the view; a tighter FP reload would need its own clip.
- **Next feature (the user's pick): the loot and extraction loop** - lootable crates (the Vicevoxel props are placed but inert), an inventory/carry limit, an extraction point that ends the run with what you took, and a way back in. Ask the user how loot should work (types, value, weight) before building.
- **Open, small:** under a ceiling panel the FP rifle reads silver (FP scale moves it out of the body's shadow; `gotchas.md`); no automated smoke run of the packaged game yet; the zombie has no hit reaction or sounds; no footsteps; hearing radius 1800 pulls most of the floor.
- **Checking on screen:** `node tools/unreal.mjs shot` saves a clean 1920x1080 game frame; `VS_SHOT_CMDS` runs console commands first (`mcp.md`).
- **Notes for the loot feature:** `design.md`, `architecture.md` (C++ classes, props, level script); `gotchas.md` before any build trouble.
