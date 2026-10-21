# Gotchas found while building

One trap per bullet, under its topic. `Grep "^## " gotchas.md` for the map.

## Builds
- The Mournhollow editor's Live Coding blocks UBT on the shared engine ("Unable to build while Live Coding is active"): pass `-NoHotReloadFromIDE` (the tool does). Close only the Velisect editor before `compile`.
- Adding UPROPERTYs needs a full compile with the editor closed; Live Coding can't. Save first: closing the editor can raise a Save Content dialog (the navmesh dirties the map).
- `UNavigationSystemV1::GetCurrent<T>` doesn't compile here; use `FNavigationSystem::GetCurrent<UNavigationSystemV1>(World)`.
- A test's table of `TPair<const TCHAR*, TArray<...>>` won't brace-initialise (C2440): use a small struct.
- Never keep the project in OneDrive (or any synced folder): it locked staging files mid-build ("Access to the path ... is denied") and synced GBs of Saved/Intermediate. Moved to `C:\Users\adanr\velisect` in M3; after a move, delete `Intermediate/` so UBT rebuilds its makefiles.
- The cook succeeds while a material fails to compile, and the game silently uses the default material; `package` now greps for it. M_PBR's Masks samplers defaulted to the sRGB `WhiteSquareTexture` (fixed in M2 by `fix_pbr_defaults.py`).

## MCP, Python, Blender
- Two editors run on this engine: Mournhollow's MCP owns port 8000. Velisect's is 8010 (`-ModelContextProtocolPort=8010`, or `ModelContextProtocol.StartServer 8010` from the console).
- `CaptureViewport` renders the **editor** world even during PIE; for an outside view in PIE move the level's `DebugCam` and `SetViewTargetWithBlend` to it, then `CaptureEditorImage`. Python can't spawn actors in the PIE world.
- MCP tool args: every schema field must be present (`CaptureViewport` needs `annotations` even when unused). Images come back inside a text payload (`returnValue.image.data` or `returnValue.data`).
- Unreal Python: `EditorLevelLibrary` is deprecated (use the subsystems); post-process fields are `auto_exposure_min_brightness`, `film_grain_intensity`; spawned rect lights default to Stationary: set Movable (static lighting is off) or they draw red errors.
- Blender's MCP add-on is Blender Lab's official `MCP` extension (since 2026-10-21); ahujasid's `blender_mcp` add-on is disabled because both use port 9876, so never re-enable it or put `uvx blender-mcp` back. The first MCP call after Blender starts can return "Empty response" while the server auto-starts; retry once. Pipeline scripts run headless, never through the MCP.
- Re-running a pipeline script rewrites FBX creation timestamps (about 85 bytes); if the geometry is unchanged, `git checkout -- SourceArt` instead of committing LFS churn. `kit.py` once held a stale copy of the texture code that overwrote the tuned textures; textures live only in `textures.py`.
- A Blender splash screen blocks nothing, but an open modal does; check a screenshot when the socket stops answering.

## Assets and animation
- Mixamo FBX through Interchange: bones import lowercase without the `mixamorig:` prefix; `create_physics_asset` on import is ignored (make them with `SkeletalMeshEditorSubsystem.create_physics_asset`).
- Mixamo takes carry forward travel on the hips (Sprint 3.6 m per cycle); export them in place from Blender.
- The upper-body layer must blend its root in component space, and the spine's aim pitch is inverted on this rig (see `animation.md`).
- Vicevoxel crates import at wildly different scales (a 3 m crate): `ue_level.py`'s props are scaled to target heights after placing.
- With every panel lit and shadowed, VSM one-pass projection overflows: rect lights on a checkerboard, shadows on half of those (36).
