"""Imports export_fp.py's first-person takes: SK_RifleFP (the rifle with magazine, spare magazine, bolt and trigger bones,
on SM_Rifle's materials) with its A_RifleFP_* takes, and the arms' A_FP_* takes on the player skeleton.
Run: node tools/unreal.mjs py tools/pipeline/ue_import_fp.py (headless when the editor is closed)."""
import glob, os
import unreal

E = unreal.EditorAssetLibrary
SRC = r"C:\Users\adanr\velisect\SourceArt\Player\FP"
RIFLE = "/Game/Velisect/Weapons/Rifle"
PLAYER = "/Game/Velisect/Characters/Player"
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(src, dest, name, ui):
    t = unreal.AssetImportTask()
    t.filename = src; t.destination_path = dest; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = True; t.options = ui
    return t

def anim_ui(skeleton):
    ui = unreal.FbxImportUI()
    ui.import_mesh = False; ui.import_as_skeletal = True; ui.import_animations = True
    ui.import_materials = False; ui.import_textures = False; ui.skeleton = skeleton
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    ui.anim_sequence_import_data.set_editor_property("import_bone_tracks", True)
    ui.anim_sequence_import_data.set_editor_property("remove_redundant_keys", False)
    return ui

ui = unreal.FbxImportUI()
ui.import_mesh = True; ui.import_as_skeletal = True; ui.import_animations = False
ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
existing = unreal.load_asset(RIFLE + "/SK_RifleFP_Skeleton") if E.does_asset_exist(RIFLE + "/SK_RifleFP_Skeleton") else None
if existing: ui.skeleton = existing
t = task(os.path.join(SRC, "SK_RifleFP.fbx"), RIFLE, "SK_RifleFP", ui)
tools.import_asset_tasks([t])
print("rifle", list(t.imported_object_paths))

rifle = unreal.load_asset(RIFLE + "/SK_RifleFP")
static = unreal.load_asset(RIFLE + "/SM_Rifle")
by_slot = {str(m.material_slot_name): m.material_interface for m in static.static_materials}
mats = rifle.get_editor_property("materials")
for i, m in enumerate(mats):  # elements come back as copies: set each, then put it back
    slot = str(m.material_slot_name)
    print("slot", slot, "->", by_slot[slot].get_name() if slot in by_slot else "MISSING")
    if slot in by_slot:
        m.set_editor_property("material_interface", by_slot[slot])
        mats[i] = m
rifle.set_editor_property("materials", mats)
E.save_loaded_asset(rifle)
skel = rifle.skeleton
ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
print("rifle bones", [str(n) for n in unreal.AnimPoseExtensions.get_bone_names(ref)], "bounds", rifle.get_bounds().box_extent)

tasks = [task(f, RIFLE + "/Animations", os.path.splitext(os.path.basename(f))[0], anim_ui(skel))
         for f in sorted(glob.glob(os.path.join(SRC, "A_RifleFP_*.fbx")))]
player_skel = unreal.load_asset(PLAYER + "/SK_Player_Skeleton")
tasks += [task(f, PLAYER + "/Animations", os.path.splitext(os.path.basename(f))[0], anim_ui(player_skel))
          for f in sorted(glob.glob(os.path.join(SRC, "A_FP_*.fbx")))]
tools.import_asset_tasks(tasks)
for t in tasks:
    a = unreal.load_asset(t.destination_path + "/" + t.destination_name)
    print("take", t.destination_name, "ok" if a else "MISSING", round(a.get_play_length(), 3) if a else "")
