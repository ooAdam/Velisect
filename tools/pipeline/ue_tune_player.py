"""Writes player_cfg.json's tuning onto BP_Player's defaults (run in the open editor: node tools/unreal.mjs py tools/pipeline/ue_tune_player.py)."""
import json
import unreal

E = unreal.EditorAssetLibrary
cfg = json.load(open(r"C:\Users\adanr\OneDrive\Documents\Unreal Projects\Velisect\tools\pipeline\player_cfg.json"))
bp = unreal.load_asset("/Game/Velisect/Blueprints/BP_Player")
cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
cdo.set_editor_property("body_offset", unreal.Vector(*cfg["body"]))
cdo.set_editor_property("camera_offset", unreal.Vector2D(*cfg["camera"]))
cdo.set_editor_property("eye_height", cfg["eye"])
cdo.set_editor_property("aim_yaw_offset", cfg["yaw"])
cdo.set_editor_property("aim_pitch_scale", cfg["pitch_scale"])
cdo.set_editor_property("aim_pitch_offset", cfg["pitch_offset"])
grip = cfg["grip"]
cdo.set_editor_property("weapon_grip_offset", unreal.Transform(unreal.Vector(*grip["loc"]), unreal.Rotator(roll=grip["rot"][2], pitch=grip["rot"][0], yaw=grip["rot"][1]), unreal.Vector(1, 1, 1)))
cdo.set_editor_property("muzzle_offset", unreal.Vector(*cfg["muzzle"]))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
E.save_loaded_asset(bp)
print("BP_Player tuned", cfg)
