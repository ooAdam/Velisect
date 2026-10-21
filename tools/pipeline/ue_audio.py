import unreal, os
E = unreal.EditorAssetLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
SA = r"C:\Users\adanr\velisect\SourceArt\Audio"
tasks = []
for n in ["S_RifleShot", "S_FluorescentHum"]:
    t = unreal.AssetImportTask(); t.filename = os.path.join(SA, n + ".wav"); t.destination_path = "/Game/Velisect/Audio"
    t.destination_name = n; t.automated = True; t.replace_existing = True; t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
hum = unreal.load_asset("/Game/Velisect/Audio/S_FluorescentHum")
hum.set_editor_property("looping", True)
E.save_loaded_asset(hum)
# Spatialised hum emitters on a coarse grid so the buzz swells under the lights.
att = unreal.SoundAttenuationSettings()
att.set_editor_property("attenuation_shape_extents", unreal.Vector(150, 0, 0))
att.set_editor_property("falloff_distance", 900.0)
for a in ACTORS.get_all_level_actors():
    if str(a.get_folder_path()) == "Audio":
        ACTORS.destroy_actor(a)
n = 0
for i in range(1, 12, 3):
    for j in range(1, 12, 3):
        snd = ACTORS.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(i * 400 + 200, j * 400 + 200, 280))
        snd.set_folder_path("Audio")
        c = snd.get_component_by_class(unreal.AudioComponent)
        c.set_editor_property("sound", hum)
        c.set_editor_property("volume_multiplier", 0.35)
        c.set_editor_property("pitch_multiplier", 1.0 + ((i * 7 + j * 3) % 5 - 2) * 0.01)
        c.set_editor_property("override_attenuation", True)
        c.set_editor_property("attenuation_overrides", att)
        n += 1
LEVELS.save_current_level()
print("audio placed", n)
