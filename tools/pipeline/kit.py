exec(open(r"C:\Users\adanr\velisect\tools\pipeline\common_bl.py").read())
import bmesh
OUT = r"C:\Users\adanr\velisect\SourceArt\Backrooms"  # textures: textures.py
os.makedirs(OUT, exist_ok=True)

# ---------------- modular meshes ----------------
def new_obj(name, mats):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        mat = bpy.data.materials.get(m) or bpy.data.materials.new(m)
        me.materials.append(mat)
    return ob

def add_box(bm, uv, mn, mx, mat, uv_scale=1.0, faces=("+x", "-x", "+y", "-y", "+z", "-z")):
    """Axis-aligned box with world-scaled box-projected UVs (1 UV unit = uv_scale metres)."""
    (x0, y0, z0), (x1, y1, z1) = mn, mx
    P = {"+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
         "-x": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
         "+y": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
         "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
         "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
         "-z": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)]}
    for key in faces:
        f = bm.faces.new([bm.verts.new(p) for p in P[key]]); f.material_index = mat
        for loop in f.loops:
            c = loop.vert.co
            if key in ("+x", "-x"): u_, v_ = (c.y if key == "+x" else -c.y), c.z
            elif key in ("+y", "-y"): u_, v_ = (-c.x if key == "+y" else c.x), c.z
            else: u_, v_ = c.x, (c.y if key == "+z" else -c.y)
            loop[uv].uv = (u_ / uv_scale, v_ / uv_scale)

def build(name, mats, fn):
    ob = new_obj(name, mats); bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    fn(bm, uv); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(ob.data); bm.free(); return ob

H, T, BB = 3.0, 0.2, 0.12   # ceiling height, wall thickness, baseboard height
def wall(length):
    def fn(bm, uv):
        L = length / 2
        add_box(bm, uv, (-L, -T / 2, BB), (L, T / 2, H), 0, faces=("+x", "-x", "+y", "-y"))
        add_box(bm, uv, (-L, -T / 2 - 0.012, 0), (L, T / 2 + 0.012, BB), 1, uv_scale=0.5, faces=("+x", "-x", "+y", "-y", "+z"))
    return fn
def pillar(bm, uv):
    s = 0.3
    add_box(bm, uv, (-s, -s, BB), (s, s, H), 0, faces=("+x", "-x", "+y", "-y"))
    add_box(bm, uv, (-s - 0.012, -s - 0.012, 0), (s + 0.012, s + 0.012, BB), 1, uv_scale=0.5, faces=("+x", "-x", "+y", "-y", "+z"))
def floor(bm, uv):
    add_box(bm, uv, (-4, -4, -0.1), (4, 4, 0), 0, uv_scale=2.0)
def ceiling(bm, uv):
    add_box(bm, uv, (-4, -4, 0), (4, 4, 0.1), 0, uv_scale=1.2)
def panel(bm, uv):
    add_box(bm, uv, (-0.62, -0.32, -0.035), (0.62, 0.32, 0), 0, faces=("+x", "-x", "+y", "-y"))
    add_box(bm, uv, (-0.58, -0.28, -0.04), (0.58, 0.28, -0.035), 1, faces=("-z",))

clear()
kit = {
    "SM_BR_Wall_400": (["MI_BR_Wallpaper", "MI_BR_Baseboard"], wall(4.0)),
    "SM_BR_Wall_200": (["MI_BR_Wallpaper", "MI_BR_Baseboard"], wall(2.0)),
    "SM_BR_Pillar": (["MI_BR_Wallpaper", "MI_BR_Baseboard"], pillar),
    "SM_BR_Floor_800": (["MI_BR_Carpet"], floor),
    "SM_BR_Ceiling_800": (["MI_BR_Ceiling"], ceiling),
    "SM_BR_LightPanel": (["MI_BR_PanelFrame", "MI_BR_PanelLight"], panel),
}
for name, (mats, fn) in kit.items():
    ob = build(name, mats, fn)
    for o in bpy.data.objects: o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(**ctx()):
        bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True, object_types={'MESH'},
                                 mesh_smooth_type='FACE', apply_scale_options='FBX_SCALE_ALL', bake_anim=False)
print("kit ok", sorted(f for f in os.listdir(OUT) if f.endswith(".fbx")))
