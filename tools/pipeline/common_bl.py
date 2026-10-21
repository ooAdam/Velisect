import bpy, os, json
ROOT = r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\FabLibrary\FPS_Guns_4K_-_Rifle_1-a7e70f32\fbx\fps_guns_4k_rifle_1_extracted\Velisect"
def ctx():
    if bpy.app.background: return {}  # headless (blx.py): the io operators need no viewport
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    return dict(window=win, screen=win.screen, area=area, region=next(r for r in area.regions if r.type=='WINDOW'))
def clear():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            if d.users == 0: coll.remove(d)
def fbx_import(path, **kw):
    with bpy.context.temp_override(**ctx()):
        bpy.ops.import_scene.fbx(filepath=path, **kw)
