exec(open(r"C:\Users\adanr\velisect\tools\pipeline\common_bl.py").read())
import bmesh, numpy as np
OUT = r"C:\Users\adanr\velisect\SourceArt\Backrooms"
os.makedirs(os.path.join(OUT, "Textures"), exist_ok=True)
rng = np.random.default_rng(7)

# ---------------- textures (tileable; FFT-filtered noise wraps by construction) ----------------
def noise(n, sigma):
    f = np.fft.fft2(rng.standard_normal((n, n)))
    k = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    a = np.real(np.fft.ifft2(f * np.exp(-k * (sigma ** 2) * 2 * np.pi ** 2)))
    return (a - a.min()) / (a.max() - a.min())

def fbm(n, sigmas, weights):
    return sum(w * noise(n, s) for s, w in zip(sigmas, weights)) / sum(weights)

def save(name, rgb, alpha=None):
    n = rgb.shape[0]
    rgba = np.concatenate([np.clip(rgb, 0, 1), (alpha if alpha is not None else np.ones((n, n)))[..., None]], axis=2)
    img = bpy.data.images.new(name, n, n, alpha=False)
    img.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())
    img.filepath_raw = os.path.join(OUT, "Textures", name + ".png"); img.file_format = 'PNG'; img.save()

def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nrm = np.stack([-dx, dy, np.ones_like(h)], axis=2)
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    return nrm * 0.5 + 0.5

N = 1024
yy, xx = np.mgrid[0:N, 0:N] / N  # row 0 = top of image

# Wallpaper: 1 m tile. Columns of chevrons (4 per metre), alternate columns offset half a cell.
cols, rows = 4, 6
cu = xx * cols; col = np.floor(cu); u = cu - col
v = (yy * rows + 0.5 * (col % 2)) % 1.0
x = u - 0.5
d = (v + 0.55 * np.abs(x)) % 1.0
chev = ((d > 0.30) & (d < 0.46) & (np.abs(x) < 0.36)).astype(float)
chev = np.clip(chev - 0.15 * noise(N, 2), 0, 1)
stripe = 0.5 + 0.5 * np.cos(2 * np.pi * xx * cols * 2)
grime = fbm(N, [3, 12, 40], [1, 1, 1.5])
base = np.array([0.80, 0.72, 0.38])
col_rgb = base[None, None, :] * (0.93 + 0.05 * stripe[..., None]) * (0.88 + 0.16 * grime[..., None])
col_rgb = col_rgb * (1 - 0.13 * chev[..., None]) + chev[..., None] * np.array([0.0, 0.01, -0.02])
save("T_BR_Wallpaper_D", col_rgb)
save("T_BR_Wallpaper_N", normal_from_height(chev * 0.6 + grime * 0.2, 3.0))

# Carpet: 2 m tile, short-pile weave + damp patches.
weave = 0.5 + 0.5 * np.sin(2 * np.pi * xx * 256) * np.sin(2 * np.pi * yy * 256)
pile = noise(N, 1.2)
blot = fbm(N, [20, 60], [1, 1])
damp = np.clip((blot - 0.55) * 4, 0, 1)
carpet = np.array([0.50, 0.42, 0.24])[None, None, :] * (0.78 + 0.22 * pile[..., None] + 0.06 * weave[..., None])
carpet *= (1 - 0.35 * damp[..., None])
save("T_BR_Carpet_D", carpet)
save("T_BR_Carpet_N", normal_from_height(pile * 0.7 + weave * 0.3, 6.0))
save("T_BR_Carpet_R", np.repeat((0.95 - 0.45 * damp)[..., None], 3, axis=2))

# Ceiling: 1.2 m tile = 2x2 acoustic tiles of 60 cm with T-bar grid.
grid = np.minimum(np.minimum(xx % 0.5, 0.5 - xx % 0.5), np.minimum(yy % 0.5, 0.5 - yy % 0.5))
tbar = (grid < 0.012).astype(float)
speck = (noise(N, 0.6) > 0.62).astype(float) * 0.5 + noise(N, 2) * 0.5
stain = np.clip((fbm(N, [25, 70], [1, 1]) - 0.6) * 3, 0, 1)
ceil = np.array([0.82, 0.78, 0.62])[None, None, :] * (0.85 + 0.15 * speck[..., None]) * (1 - 0.3 * stain[..., None])
ceil = ceil * (1 - tbar[..., None]) + tbar[..., None] * np.array([0.72, 0.70, 0.62])
save("T_BR_Ceiling_D", ceil)
save("T_BR_Ceiling_N", normal_from_height(speck * 0.5 - tbar * 0.8, 4.0))

# Large-scale water-stain mask (tiles every ~6 m in the material) to break repetition.
save("T_BR_StainMask", np.repeat(np.clip((fbm(N, [15, 45, 90], [0.6, 1, 1]) - 0.45) * 2.5, 0, 1)[..., None], 3, axis=2))

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
print("kit ok", sorted(os.listdir(OUT)), sorted(os.listdir(os.path.join(OUT, "Textures"))))
