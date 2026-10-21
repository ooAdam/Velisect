# History

| # | Milestone | What |
|---|---|---|
| M1 | First playable slice (2026-10-21) | C++ project from a blank one; MCP (8010), Python remote exec; Mixamo takes in place and mirrored in Blender; code-driven anim instance; true-FP player with rifle, sprint, crouch, jump, reload, recoil, decals, flashlight, HUD, death and restart; the zombie (wander, scream, chase, attack, die, headshots); Backrooms Level 1 from a Blender kit with generated textures, lights, haze, navmesh, props; synthesized shot and hum |
| M2 | The workflow (2026-10-21) | Mournhollow's structure: CLAUDE.md, `docs/notes`, `tools/unreal.mjs` (compile, test, package, play, open, py, blender, shot), content tests, cook settings, `Play Velisect.bat`, git with LFS |
| M3 | Out of OneDrive (2026-10-21) | Project moved to `C:\Users\adanr\velisect`; build output back in `Packaged/`; script paths updated; pushed to github.com/ooAdam/Velisect |
| M4 | Valorant viewmodel (2026-10-21) | First-person arms (cut from Ch35) and rifle on the camera as UE first-person primitives, framed from the user's reference by a solve in `ue_tune_player.py`; left hand mirrors the right hand's grip onto the foregrip (IK); procedural kick, sway, bob and sprint hold; body kept for shadow and death cam; the vest straps that showed as black lines are gone |
