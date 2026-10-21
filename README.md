# Velisect

A first-person shooter in the Backrooms: endless yellow halls, damp carpet, the hum of the lights, and something wandering the floor. Go in, find what's worth taking, get back out.

## Play
Double-click **Play Velisect.bat** (or `npm run play`); the game is built into `Packaged\Windows`. If it says the game isn't built: `npm run package`.

| Key | Action |
|---|---|
| W A S D | move |
| Mouse | look |
| Shift | sprint (rifle lowered) |
| Space | jump |
| Ctrl / C | crouch |
| Left mouse | fire (full auto) |
| R | reload |
| F | flashlight |

You have 100 health and a 30-round rifle with 120 spare. Gunfire carries: anything within about 18 m will come. Headshots do triple damage. If you die, the floor resets after a few seconds.

## Level 1
A 48 × 48 m stretch of the Backrooms: four of them wander it. Supply crates and old radios lie against the walls. Looting and extraction are next.

## Building it
Unreal Engine 5.8 and Visual Studio Build Tools; Node for the build tool. `node tools/unreal.mjs compile test package` (the editor must be closed). Git LFS holds the content: run `git lfs install` before cloning.
