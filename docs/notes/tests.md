# Tests

`node tools/unreal.mjs test` runs `Velisect.*` headless (`VS_TEST=<group>` for one), about 15 s. Sources: `Source/Velisect/Private/Tests/`.

- **Velisect.Content.SoftPaths:** every soft object path on `BP_Player`, `BP_Zombie` and `BP_GameMode` defaults (structs and arrays included: 30 + 9 + 0) loads. Mutation (M2): renaming `A_Player_Jump` in C++ failed it, naming the property and path.
- **Velisect.Content.Bones:** SK_Player and SK_Zombie load, have physics assets, and `FindBone` finds spine, spine1, spine2, head, righthand and the left-arm IK chain (zombie: spine, head); SK_PlayerArms loads on the player skeleton with the IK bones. Mutation (M4): a wrong arms path failed it ("SK_PlayerArmsX loads").
- **Not covered yet:** gameplay numbers (anim rates, aim alignment, AI states) are checked by PIE shots and the measurements in `animation.md`; a smoke run of the packaged game is still to build.
