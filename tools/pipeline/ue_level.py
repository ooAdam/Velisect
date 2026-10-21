"""Builds /Game/Velisect/Maps/L_Backrooms_Level1 from the Backrooms modular kit."""
import random
import unreal

E = unreal.EditorAssetLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAP = "/Game/Velisect/Maps/L_Backrooms_Level1"
KIT = "/Game/Velisect/Environment/Backrooms/Meshes/"

CELL, NX, NY, HEIGHT = 400.0, 12, 12, 300.0
SEED = 1987
rng = random.Random(SEED)

# ---------------------------------------------------------------- layout
# Edge keys: ("v", i, j) is the wall between cell (i, j) and (i+1, j); ("h", i, j) between (i, j) and (i, j+1).
SAFE = {(0, 0), (1, 0), (0, 1), (1, 1)}  # open spawn area
walls, halves = set(), set()
for i in range(NX - 1):
    for j in range(NY):
        if not ({(i, j), (i + 1, j)} <= SAFE):
            r = rng.random()
            if r < 0.30:
                walls.add(("v", i, j))
            elif r < 0.40:
                halves.add(("v", i, j))
for i in range(NX):
    for j in range(NY - 1):
        if not ({(i, j), (i, j + 1)} <= SAFE):
            r = rng.random()
            if r < 0.30:
                walls.add(("h", i, j))
            elif r < 0.40:
                halves.add(("h", i, j))


def neighbours(c):
    i, j = c
    if i + 1 < NX and ("v", i, j) not in walls: yield (i + 1, j), ("v", i, j)
    if i > 0 and ("v", i - 1, j) not in walls: yield (i - 1, j), ("v", i - 1, j)
    if j + 1 < NY and ("h", i, j) not in walls: yield (i, j + 1), ("h", i, j)
    if j > 0 and ("h", i, j - 1) not in walls: yield (i, j - 1), ("h", i, j - 1)


def reachable():
    seen, stack = {(0, 0)}, [(0, 0)]
    while stack:
        for n, _ in neighbours(stack.pop()):
            if n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


# Knock out walls between the reached region and the rest until every cell connects.
while True:
    seen = reachable()
    if len(seen) == NX * NY:
        break
    frontier = [w for w in walls if
                (w[0] == "v" and (((w[1], w[2]) in seen) != ((w[1] + 1, w[2]) in seen))) or
                (w[0] == "h" and (((w[1], w[2]) in seen) != ((w[1], w[2] + 1) in seen)))]
    walls.discard(rng.choice(frontier))

# Pillars on interior grid corners that no wall touches.
pillars = []
for i in range(1, NX):
    for j in range(1, NY):
        touching = {("v", i - 1, j - 1), ("v", i - 1, j), ("h", i - 1, j - 1), ("h", i, j - 1)} & (walls | halves)
        if not touching and rng.random() < 0.22:
            pillars.append((i * CELL, j * CELL))


def edge_transform(edge):
    kind, i, j = edge
    if kind == "v":
        return unreal.Vector((i + 1) * CELL, (j + 0.5) * CELL, 0), unreal.Rotator(0, 0, 90)
    return unreal.Vector((i + 0.5) * CELL, (j + 1) * CELL, 0), unreal.Rotator(0, 0, 0)


# ---------------------------------------------------------------- level
if E.does_asset_exist(MAP):
    # Rebuild in place: clear everything the generator owns.
    LEVELS.load_level(MAP)
    for actor in ACTORS.get_all_level_actors():
        if not isinstance(actor, unreal.WorldSettings) and str(actor.get_folder_path()).split("/")[0] in ("Backrooms", "Lighting", "Gameplay", "Props"):
            ACTORS.destroy_actor(actor)
else:
    LEVELS.new_level(MAP)


def place(mesh, loc, rot=unreal.Rotator(0, 0, 0), folder="Backrooms", label=None, scale=None):
    actor = ACTORS.spawn_actor_from_object(unreal.load_asset(mesh), loc, rot)
    actor.set_folder_path(folder)
    if label:
        actor.set_actor_label(label)
    if scale:
        actor.set_actor_scale3d(scale)
    return actor


W, D = NX * CELL, NY * CELL
for x in range(int(W // 800)):
    for y in range(int(D // 800)):
        place(KIT + "SM_BR_Floor_800", unreal.Vector(x * 800 + 400, y * 800 + 400, 0), folder="Backrooms/Floor")
        place(KIT + "SM_BR_Ceiling_800", unreal.Vector(x * 800 + 400, y * 800 + 400, HEIGHT), folder="Backrooms/Ceiling")

# Perimeter.
for i in range(NX):
    place(KIT + "SM_BR_Wall_400", unreal.Vector((i + 0.5) * CELL, 0, 0), folder="Backrooms/Walls")
    place(KIT + "SM_BR_Wall_400", unreal.Vector((i + 0.5) * CELL, D, 0), folder="Backrooms/Walls")
for j in range(NY):
    place(KIT + "SM_BR_Wall_400", unreal.Vector(0, (j + 0.5) * CELL, 0), unreal.Rotator(0, 0, 90), folder="Backrooms/Walls")
    place(KIT + "SM_BR_Wall_400", unreal.Vector(W, (j + 0.5) * CELL, 0), unreal.Rotator(0, 0, 90), folder="Backrooms/Walls")

for edge in sorted(walls):
    loc, rot = edge_transform(edge)
    place(KIT + "SM_BR_Wall_400", loc, rot, folder="Backrooms/Walls")
for edge in sorted(halves):
    loc, rot = edge_transform(edge)
    # Half-length wall pushed toward one end leaves a doorway-sized gap.
    shift = rng.choice([-100.0, 100.0])
    offset = unreal.Vector(0, shift, 0) if edge[0] == "v" else unreal.Vector(shift, 0, 0)
    place(KIT + "SM_BR_Wall_200", loc + offset, rot, folder="Backrooms/Walls")
for (x, y) in pillars:
    place(KIT + "SM_BR_Pillar", unreal.Vector(x, y, 0), folder="Backrooms/Pillars")

# Fluorescent panels in every cell; real rect lights on a checkerboard, a few panels dead.
light_count = 0
for i in range(NX):
    for j in range(NY):
        c = unreal.Vector((i + 0.5) * CELL, (j + 0.5) * CELL, HEIGHT)
        dead = (i, j) not in SAFE and rng.random() < 0.08
        panel = place(KIT + "SM_BR_LightPanel", c, folder="Backrooms/Lights")
        if dead:
            panel.static_mesh_component.set_material(1, unreal.load_asset("/Game/Velisect/Environment/Backrooms/Materials/MI_BR_PanelFrame"))
            continue
        if (i + j) % 2 == 0:
            light = ACTORS.spawn_actor_from_class(unreal.RectLight, c - unreal.Vector(0, 0, 6), unreal.Rotator(0, -90, 0))
            light.set_folder_path("Backrooms/Lights")
            comp = light.rect_light_component
            comp.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            comp.set_editor_property("intensity", 2600.0)
            comp.set_editor_property("source_width", 55.0)
            comp.set_editor_property("source_height", 115.0)
            comp.set_editor_property("attenuation_radius", 1000.0)
            comp.set_editor_property("barn_door_angle", 88.0)
            comp.set_editor_property("light_color", unreal.Color(255, 238, 196, 255))
            comp.set_editor_property("cast_shadows", True)
            light_count += 1

# Atmosphere.
fog = ACTORS.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(W / 2, D / 2, 0))
fog.set_folder_path("Lighting")
fc = fog.component
fc.set_editor_property("fog_density", 0.035)
fc.set_editor_property("fog_height_falloff", 0.001)
fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.42, 0.36, 0.16, 1))
fc.set_editor_property("start_distance", 250.0)

ppv = ACTORS.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(W / 2, D / 2, 150))
ppv.set_folder_path("Lighting")
ppv.set_editor_property("unbound", True)
s = ppv.settings
for k, v in {
    "override_auto_exposure_min_brightness": True, "auto_exposure_min_brightness": 4.0,
    "override_auto_exposure_max_brightness": True, "auto_exposure_max_brightness": 9.0,
    "override_bloom_intensity": True, "bloom_intensity": 0.9,
    "override_vignette_intensity": True, "vignette_intensity": 0.55,
    "override_film_grain_intensity": True, "film_grain_intensity": 0.22,
    "override_scene_fringe_intensity": True, "scene_fringe_intensity": 0.6,
    "override_white_temp": True, "white_temp": 5600.0,
    "override_color_saturation": True, "color_saturation": unreal.Vector4(0.92, 0.92, 0.88, 1.0),
    "override_color_contrast": True, "color_contrast": unreal.Vector4(1.08, 1.08, 1.08, 1.0),
}.items():
    s.set_editor_property(k, v)
ppv.set_editor_property("settings", s)

nav = ACTORS.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(W / 2, D / 2, 150))
nav.set_folder_path("Gameplay")
nav.set_actor_scale3d(unreal.Vector(W / 200 + 0.5, D / 200 + 0.5, 2.5))

start = ACTORS.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(CELL * 0.5, CELL * 0.5, 100), unreal.Rotator(0, 0, 45))
start.set_folder_path("Gameplay")

# Zombies in far cells.
zombie_class = unreal.BlueprintEditorLibrary.generated_class(unreal.load_asset("/Game/Velisect/Blueprints/BP_Zombie"))
far = [(i, j) for i in range(NX) for j in range(NY) if i + j >= 9]
for n, (i, j) in enumerate(rng.sample(far, 4)):
    z = ACTORS.spawn_actor_from_class(zombie_class, unreal.Vector((i + 0.5) * CELL, (j + 0.5) * CELL, 105), unreal.Rotator(0, 0, rng.uniform(0, 360)))
    z.set_folder_path("Gameplay/Zombies")
    z.set_actor_label(f"Zombie_{n + 1}")

# Loot props against walls.
PROPS = ["/Game/Velisect/Props/Crates/VV_ammobox_001/SM_ammobox_001", "/Game/Velisect/Props/Crates/VV_ammo_crate/SM_ammo_crate",
         "/Game/Velisect/Props/Crates/VV_MilitaryCrate/SM_MilitaryCrate", "/Game/Velisect/Props/Crates/VV_Medical_Crate/SM_Medical_Crate",
         "/Game/Velisect/Props/Crates/VV_SupplyCrate_2/SM_SupplyCrate_2", "/Game/Velisect/Props/Crates/VV_WeaponBox1/SM_WeaponBox1",
         "/Game/Velisect/Props/Crates/VV_FootLocker/SM_FootLocker", "/Game/Velisect/Props/Crates/VV_aidbox_001/SM_aidbox_001",
         "/Game/Velisect/Props/Crates/VV_petrolcanister_a/SM_petrolcanister_a", "/Game/Velisect/Props/Crates/VV_weapon_case_a_3/SM_weapon_case_a_3",
         "/Game/Velisect/Props/Crates/VV_ammo_can_small/SM_ammo_can_small", "/Game/Velisect/Props/Crates/VV_Health_Generic/SM_Health_Generic",
         "/Game/Velisect/Props/Radio/SM_Radio", "/Game/Velisect/Props/Radio/SM_WalkieTalkie_LongAntenna", "/Game/Velisect/Props/Radio/SM_Telephone"]
cells = [(i, j) for i in range(NX) for j in range(NY) if (i, j) not in SAFE]
placed = []
for path in PROPS:
    mesh = unreal.load_asset(path)
    if not mesh:
        print("missing prop", path)
        continue
    box = mesh.get_bounding_box()
    i, j = rng.choice(cells)
    side = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    loc = unreal.Vector((i + 0.5 + side[0] * 0.32) * CELL, (j + 0.5 + side[1] * 0.32) * CELL, -box.min.z)
    a = place(path, loc, unreal.Rotator(0, 0, rng.uniform(0, 360)), folder="Props", label=path.split("/")[-1])
    placed.append((a.get_actor_label(), round(box.max.z - box.min.z)))

LEVELS.save_current_level()

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ws = world.get_world_settings()
ws.set_editor_property("default_game_mode", unreal.BlueprintEditorLibrary.generated_class(unreal.load_asset("/Game/Velisect/Blueprints/BP_GameMode")))
LEVELS.save_current_level()
print(f"walls={len(walls)} halves={len(halves)} pillars={len(pillars)} lights={light_count} props={placed}")
