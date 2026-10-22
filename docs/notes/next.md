# Next session: start here

Overwritten at every milestone commit. Keep it to about ten lines.

- **Open the chat in `C:\Users\adanr\velisect`** so CLAUDE.md and `.mcp.json` load. Mournhollow's editor owns MCP port 8000; Velisect's is 8010.
- **M5 (authored first-person hold and reloads) committed and pushed:** both hands hold the rifle with fitted fingers (trigger finger on the trigger); AK tactical reload 2.0 s and empty reload 2.73 s (adds the rack) play on the arms and the rigged rifle (SK_RifleFP) in sync; bolt cycles per shot. Tests 2/2, package ok, packaged exe loads Level 1 clean. How: `animation.md`. Change a take: keys in `export_fp.py` (`reload_keys`, `CLIPS`) → `blender export_fp.py` → `py ue_import_fp.py` → `py ue_tune_player.py`.
- **Ask the user how M5 plays:** reload speed (`reload_rate` in `player_cfg.json`), how high and canted the reload hold is (`L` in `reload_keys`), the rack roll.
- **Open, small:** reloads have no foley yet (mag out/in, rack); the tossed magazine doesn't land in the world; arms have no hit reaction now (body only); zombie has no hit reaction or sounds; no footsteps.
- **Next feature (the user's pick): the loot and extraction loop** - lootable crates (the Vicevoxel props are placed but inert), an inventory/carry limit, an extraction point that ends the run with what you took, and a way back in. Ask the user how loot should work (types, value, weight) before building.
- **Checking on screen:** `node tools/unreal.mjs shot` saves a clean game frame; `python -I tools/pipeline/pie_seq.py <prefix> "slomo 0.2;VsReload" 9 1.25` steps through a reload; `py` scripts run headless when the editor is closed.
- **Notes for the loot feature:** `design.md`, `architecture.md` (C++ classes, props, level script); `gotchas.md` before any build trouble.
