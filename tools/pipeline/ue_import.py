import unreal, os, glob
SA = r"C:\Users\adanr\velisect\SourceArt"
SRC = r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\FabLibrary\FPS_Guns_4K_-_Rifle_1-a7e70f32\fbx\fps_guns_4k_rifle_1_extracted\Velisect"
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

def run(tasks):
    tools.import_asset_tasks(tasks)
    for t in tasks:
        log.append((os.path.basename(t.filename), len(t.imported_object_paths)))

def task(src, dest, name, opts=None):
    t = unreal.AssetImportTask()
    t.filename = src; t.destination_path = dest; t.destination_name = name or ""
    t.automated = True; t.replace_existing = True; t.save = True
    if opts: t.options = opts
    return t

def skel_ui(physics=True):
    ui = unreal.FbxImportUI()
    ui.import_mesh = True; ui.import_as_skeletal = True; ui.import_animations = False
    ui.import_materials = True; ui.import_textures = True; ui.create_physics_asset = physics
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    return ui

def anim_ui(skeleton):
    ui = unreal.FbxImportUI()
    ui.import_mesh = False; ui.import_as_skeletal = True; ui.import_animations = True
    ui.import_materials = False; ui.import_textures = False; ui.skeleton = skeleton
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    ui.anim_sequence_import_data.set_editor_property("import_bone_tracks", True)
    ui.anim_sequence_import_data.set_editor_property("remove_redundant_keys", False)
    return ui

def static_ui(combine=True, materials=True):
    ui = unreal.FbxImportUI()
    ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_animations = False
    ui.import_materials = materials; ui.import_textures = materials
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.static_mesh_import_data.set_editor_property("combine_meshes", combine)
    ui.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    return ui

# --- Characters ---
run([task(SA + r"\Zombie\SK_Zombie.fbx", "/Game/Velisect/Characters/Zombie", "SK_Zombie", skel_ui())])
for who, folder in (("Player", "Player"), ("Zombie", "Zombie")):
    skel = unreal.load_asset(f"/Game/Velisect/Characters/{folder}/SK_{who}_Skeleton")
    tasks = []
    for f in sorted(glob.glob(os.path.join(SA, folder, "Animations", "*.fbx"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        if who == "Zombie":
            stem = stem.replace("A_Zombie_Zombie", "A_Zombie_")
        tasks.append(task(f, f"/Game/Velisect/Characters/{folder}/Animations", stem, anim_ui(skel)))
    run(tasks)

# --- Rifle (materials built by hand from the PBR set) ---
run([task(SRC + r"\FPS Guns 4K - Rifle 1\Models\Rifle 1.fbx", "/Game/Velisect/Weapons/Rifle", "SM_Rifle", static_ui(True, False))])
tex_tasks = []
for f in glob.glob(SRC + r"\FPS Guns 4K - Rifle 1\Textures\4K\*\*.png"):
    stem = "T_Rifle_" + os.path.splitext(os.path.basename(f))[0]
    tex_tasks.append(task(f, "/Game/Velisect/Weapons/Rifle/Textures", stem))
run(tex_tasks)

# --- Backrooms kit ---
run([task(f, "/Game/Velisect/Environment/Backrooms/Meshes", os.path.splitext(os.path.basename(f))[0], static_ui(True, False))
     for f in glob.glob(SA + r"\Backrooms\*.fbx")])
run([task(f, "/Game/Velisect/Environment/Backrooms/Textures", os.path.splitext(os.path.basename(f))[0])
     for f in glob.glob(SA + r"\Backrooms\Textures\*.png")])

# --- Props ---
run([task(f, "/Game/Velisect/Props/Radio", os.path.splitext(os.path.basename(f))[0], static_ui(True, True))
     for f in glob.glob(SRC + r"\RadioPack\*.fbx")])
CRATES = ["VV_ammobox_001", "VV_ammo_crate", "VV_MilitaryCrate", "VV_Medical_Crate", "VV_SupplyCrate_2", "VV_WeaponBox1",
          "VV_FootLocker", "VV_aidbox_001", "VV_petrolcanister_a", "VV_weapon_case_a_3", "VV_ammo_can_small", "VV_Health_Generic"]
for c in CRATES:
    run([task(SRC + rf"\supply crates-Vicevoxel-FBX\{c}.fbx", f"/Game/Velisect/Props/Crates/{c}", "SM_" + c[3:], static_ui(True, True))])

for l in log: print(l)
