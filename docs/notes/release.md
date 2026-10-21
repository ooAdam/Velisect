# Pre-release checklist (Steam)

A running list so nothing is forgotten. Tick items as they land; add new ones as they come up.

## Done
- [x] Editor-only plugins (`ModelContextProtocol`, `ToolsetRegistry`, `EditorToolset`, `PythonScriptPlugin`, `EditorScriptingUtilities`, `ModelingToolsEditorMode`) have `"TargetAllowList": ["Editor"]` in `Velisect.uproject`, so the MCP server never ships. Any new editor or MCP plugin gets the same line.

## Build
- [ ] A `ship` step in `tools/unreal.mjs`: Shipping config (no console, no debug tools), Steam libraries included.
- [ ] Audit the packaged folder: no editor plugins, no `.pdb`, nothing from `SourceArt/` or `docs/`. (The engine's own `boost_*`/`tbb` DLLs are expected.)
- [ ] Automated smoke run of the packaged game (Mournhollow's `smoke` is the model).
- [ ] Crash reporting.

## Licences and content
- [ ] Mixamo characters and animations: commercial use is allowed; keep a note of which were used.
- [ ] Fab assets (rifle, Vicevoxel crates, radios): read each item's licence and record it here.
- [ ] The inspiration images never go in the game.
- [ ] Backrooms is open folklore; copy nothing from named, owned works (e.g. Kane Pixels' series).
- [ ] Replace the synthesized placeholder audio (gunshot, hum) with licensed or custom sound.
- [x] Blender assets rebuild headless from committed scripts (`unreal.mjs blender`; kit, textures and characters verified 2026-10-21, textures byte-identical).
- [ ] Every Unreal-side asset step (`ue_*.py`) is likewise re-runnable from a clean import.

## Player must-haves
- [ ] Settings menu: graphics, mouse sensitivity, key rebinding, audio.
- [ ] Frame-rate target, profiled on a mid-range PC.
- [ ] Save data.

## Steam
- [ ] Steamworks app fee ($100).
- [ ] "Coming Soon" store page well before launch, to collect wishlists.
- [ ] Store art, screenshots, trailer.
- [ ] Content and AI-disclosure questionnaire, answered honestly about how assets and code were made.
- [ ] Steam integration through Unreal's Steam online subsystem: achievements, cloud saves.
