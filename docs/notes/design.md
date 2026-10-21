# Design: what the user wants

- **The game:** a first-person shooter in the Backrooms. The player goes in, extracts good loot, and comes back out (an extraction loop). Built in Unreal 5.8 and Blender with the user's own assets.
- **The look:** the user's inspiration images, kept outside the repo at `<raw library>/Backrooms images inspiration/` and `<raw library>/POV inspiration/` (path in `architecture.md`): yellow wallpaper with chevron columns, damp patterned carpet, a drop ceiling with fluorescent panels, a warm haze, endless corridors and pillars; the POV shows gloved hands and a rifle in the lower right.
- **The player:** the user's Mixamo character Ch35 (a gas-mask soldier) with their rifle-pack animations, in true first person (the body is there, the head hidden).
- **The enemy:** one zombie, the Mixamo **Mremireh O Desbiens** with the user's zombie takes. (`Ch10` in the Enemy#1 folder is unused: the takes are on Mremireh's rig.)
- **Props the user supplied for loot and dressing:** the rifle (FPS Guns 4K Rifle 1), a radio pack, and Vicevoxel supply crates (12 imported of 36).
- **Level 1:** small, nothing big; a Backrooms floor to go into and fight the enemy in.
- **Scope so far (M1):** character, first-person movement and animations, the zombie, Level 1. Loot, inventory and extraction are the next feature track; nothing of them exists yet besides props.
- **Audio:** the user supplied none; the gunshot and fluorescent hum are synthesized placeholders (`tools/pipeline/make_audio.py`).
