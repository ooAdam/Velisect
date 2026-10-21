# Architecture

## Sources and pipeline
- **Raw library (outside the repo, 4.8 GB, never move it):** `C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\FabLibrary\FPS_Guns_4K_-_Rifle_1-a7e70f32\fbx\fps_guns_4k_rifle_1_extracted\Velisect\` with `UserCharacter/` (Ch35 + 30 takes, 60 fps), `Enemy#1/` (Mremireh + 13 zombie takes, 30 fps), `FPS Guns 4K - Rifle 1/`, `RadioPack/`, `supply crates-Vicevoxel-FBX/`, and the inspiration images.
- **Blender (`tools/pipeline/export_chars.py`):** strips each take's linear hip drift (in place; death and hit takes keep theirs), mirrors right-side takes into left ones (`StrafeLeft`→`StrafeRight`, `SprintForwardRight`→`Left`, `RunBackwardRight`→`Left`, `WalkCrouchingRight`→`Left`), re-exports meshes and takes to `SourceArt/Player|Zombie` (regenerated, not committed). `export_arms.py` cuts Ch35 to its arms (`SourceArt/Player/SK_PlayerArms.fbx`, imported by `ue_import_arms.py` onto the player skeleton with SK_Player's material). `kit.py` builds the Backrooms kit (walls 400/200, pillar, floor and ceiling slabs 800, light panel) and `textures.py` its tileable textures (`SourceArt/Backrooms`, committed).
- **Unreal (run in the open editor with `node tools/unreal.mjs py <file>`):** `ue_import.py` (everything into `/Game/Velisect`), `ue_materials.py` (`M_BR_Surface` master with world-space stains and floor grime, `M_PBR` for the rifle, instances, physics assets), `ue_level.py` (seeded layout: 12×12 cells of 4 m, 3 m ceiling, walls/half-walls/pillars, flood-fill connectivity, panels, rect lights, fog, post, navmesh, start, 4 zombies, props), `ue_audio.py`, `ue_decal.py`, `ue_tune_player.py` (+ `player_cfg.json`). These were run once to build M1 and may need care to re-run (they overwrite).

## Content (`/Game/Velisect`, committed via LFS)
`Characters/Player|Zombie` (SK_, physics assets, `Animations/A_Player_*`, `A_Zombie_*`), `Weapons/Rifle`, `Environment/Backrooms` (meshes, textures, materials), `Props/Crates|Radio`, `Materials` (masters, `M_BulletHole`), `Audio`, `Blueprints` (`BP_Player`, `BP_Zombie`, `BP_GameMode`), `Maps/L_Backrooms_Level1` (default and only map; has a `DebugCam` actor in folder Debug for outside views in PIE).

## C++ (`Source/Velisect`)
- `AVelisectCharacter`: first-person arms and rifle on the camera over the full body (`animation.md`). Enhanced Input built in code (no input assets). Walk 280, sprint 600, crouch 160, jump; hitscan rifle (25 dmg, 600 rpm, 30/120, spread, recoil, procedural spine kick, muzzle light, decals, `S_RifleShot`); flashlight; health 100, death cam on the head bone, level restart after 6 s. Gunfire calls `HearNoise` on zombies within `NoiseRadius` 1800.
- `UVelisectAnimInstance` + proxy: see `animation.md`.
- `AVelisectZombie`: states Idle/Wander/Scream/Chase/Attack/Dead; `AAIController` + navmesh; sight 26 m (front cone or within 4.5 m); 150 HP, headshot ×3 via the physics asset's bone; attack 15 (BP) at 45% of the clip, 0.45 s recovery; death clip then 45 s lifespan.
- `AVelisectHUD`: Canvas crosshair (spreads with speed, hidden in sprint), hit marker, health bar, ammo, reload prompt, damage flash, "YOU DIED".
- `AVelisectGameMode`; `VelisectTypes` (`FVelisectLocoClip`, `Velisect::FindBone`).
- Assets load by soft path (C++ defaults, overridable in the BPs); the cooker gets them via `DirectoriesToAlwaysCook=/Game/Velisect` in `DefaultGame.ini`.

## Commands
`node tools/unreal.mjs compile | test | package | play | open | py <file> | blender <file> | shot [name]` (header of `tools/unreal.mjs`). Logs: `Saved/ToolLogs/`; shots `Saved/ToolLogs/shots/`; the packaged game `Packaged/Windows` (its log: `Packaged/Windows/Velisect/Saved/Logs/Velisect.log`).
