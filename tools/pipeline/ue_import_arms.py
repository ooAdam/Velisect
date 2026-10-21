"""Imports SourceArt/Player/SK_PlayerArms.fbx (export_arms.py) onto the player skeleton with SK_Player's materials
(run in the open editor: node tools/unreal.mjs py tools/pipeline/ue_import_arms.py)."""
import unreal

E = unreal.EditorAssetLibrary
DEST = "/Game/Velisect/Characters/Player"
ui = unreal.FbxImportUI()
ui.import_mesh = True; ui.import_as_skeletal = True; ui.import_animations = False
ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
ui.skeleton = unreal.load_asset(DEST + "/SK_Player_Skeleton")
task = unreal.AssetImportTask()
task.filename = r"C:\Users\adanr\velisect\SourceArt\Player\SK_PlayerArms.fbx"
task.destination_path = DEST; task.destination_name = "SK_PlayerArms"
task.automated = True; task.replace_existing = True; task.save = True; task.options = ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
print("imported", list(task.imported_object_paths))

arms = unreal.load_asset(DEST + "/SK_PlayerArms")
body = unreal.load_asset(DEST + "/SK_Player")
by_slot = {str(m.material_slot_name): m.material_interface for m in body.materials}
mats = arms.get_editor_property("materials")
for i, m in enumerate(mats):  # elements come back as copies: set each, then put it back
    slot = str(m.material_slot_name)
    print("slot", slot, "->", by_slot.get(slot) and by_slot[slot].get_name())
    if slot in by_slot:
        m.set_editor_property("material_interface", by_slot[slot])
        mats[i] = m
arms.set_editor_property("materials", mats)
E.save_loaded_asset(arms)
print("arms skeleton", arms.skeleton.get_path_name())
