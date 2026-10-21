"""First-person arms: Ch35 cut down to the faces the arm and hand bones own, on the full rig (same skeleton as SK_Player).
Writes SourceArt/Player/SK_PlayerArms.fbx and a preview render next to it (run: node tools/unreal.mjs blender tools/pipeline/export_arms.py)."""
exec(open(r"C:\Users\adanr\velisect\tools\pipeline\common_bl.py").read())
import bmesh, mathutils
OUT = r"C:\Users\adanr\velisect\SourceArt\Player"
ARM_BONES = ("Arm", "ForeArm", "Hand")  # LeftArm, RightForeArm, LeftHandIndex2, ... (shoulders and torso go)

def is_arm(group):
    side = group.split(":")[-1]
    return any(side.startswith(s + b) for s in ("Left", "Right") for b in ARM_BONES)

clear(); fbx_import(os.path.join(ROOT, "UserCharacter", "Ch35_nonPBR.fbx"))
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis = mathutils.Matrix.Identity(4)

body = [o for o in bpy.data.objects if o.type == 'MESH'][0]
names = {g.index: g.name for g in body.vertex_groups}
keep = {v.index for v in body.data.vertices if v.groups and is_arm(names[max(v.groups, key=lambda g: g.weight).group])}
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(body.data); bm.free()
body.name = "SK_PlayerArms"
print("arms verts", len(body.data.vertices), "of", len(names) and len(keep))

for o in bpy.data.objects:
    o.select_set(o in (arm, body))
with bpy.context.temp_override(**ctx()):
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SK_PlayerArms.fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False, bake_anim=False,
        mesh_smooth_type='FACE', path_mode='STRIP', embed_textures=False)

# preview: front orthographic render of what was kept
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = 1400, 600
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
pts = [body.matrix_world @ v.co for v in body.data.vertices]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
cam.data.ortho_scale = max(hi - lo) * 1.05
cam.location = (lo + hi) / 2 + mathutils.Vector((0, -5, 0))
cam.rotation_euler = (1.5708, 0, 0)
sc.render.filepath = os.path.join(OUT, "SK_PlayerArms_preview.png")
bpy.ops.render.render(write_still=True)
print("exported", os.path.join(OUT, "SK_PlayerArms.fbx"))
