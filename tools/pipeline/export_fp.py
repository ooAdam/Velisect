"""First-person rifle animation (M5). Rigs the rifle (magazine, spare magazine, bolt and trigger bones), holds it in the
first-person arms with two-bone IK and fingers closed until they touch, keys the clips in CLIPS and bakes them for Unreal.
Writes SourceArt/Player/FP/ (SK_RifleFP.fbx, A_FP_<clip>.fbx, A_RifleFP_<clip>.fbx) and contact sheets to Saved/ToolLogs/fp/.
Run: node tools/unreal.mjs blender tools/pipeline/export_fp.py   (VS_FP=hold or VS_FP=<clip> renders sheets, exports nothing)
Space: Blender world (m) = Unreal component space (cm) with Y flipped. Rifle space: +Y muzzle, +Z up, +X right."""
exec(open(r"C:\Users\adanr\velisect\tools\pipeline\common_bl.py").read())
import math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

PIPE = r"C:\Users\adanr\velisect\tools\pipeline"
OUT = r"C:\Users\adanr\velisect\SourceArt\Player\FP"
SHOTS = r"C:\Users\adanr\velisect\Saved\ToolLogs\fp"
VM = json.load(open(os.path.join(PIPE, "player_cfg.json")))["viewmodel"]
MODE = os.environ.get("VS_FP", "export")
FLIP = Matrix.Diagonal((1, -1, 1))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

def ue(t):
    """Unreal component-space transform (cm, quaternion xyzw) -> Blender world matrix (m)."""
    q = t["quat"]
    M = (FLIP @ Quaternion((q[3], q[0], q[1], q[2])).to_matrix() @ FLIP).to_4x4()
    M.translation = Vector((t["loc"][0], -t["loc"][1], t["loc"][2])) / 100
    return M

def rot_about(R, p):
    """4x4 that turns by the 3x3 R about point p."""
    return Matrix.Translation(p) @ R.to_4x4() @ Matrix.Translation(-p)

def frame(u, v):
    """Orthonormal 3x3 with columns u, v (made perpendicular to u), u x v."""
    u = u.normalized(); v = (v - u * v.dot(u)).normalized()
    return Matrix((u, v, u.cross(v))).transposed()

def bvh(objs, space=Matrix.Identity(4)):
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        M = space @ o.matrix_world
        verts += [M @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)

# --- the arms: SK_PlayerArms on the aim pose (the first frame of Firing Rifle): torso, neck and shoulders stay there ---
clear()
fbx_import(r"C:\Users\adanr\velisect\SourceArt\Player\SK_PlayerArms.fbx")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arms_mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
before = set(bpy.data.objects)
fbx_import(os.path.join(ROOT, "UserCharacter", "Firing Rifle.fbx"))
take = [o for o in bpy.data.objects if o not in before]
act = next(o for o in take if o.type == 'ARMATURE').animation_data.action
arm.animation_data_create(); arm.animation_data.action = act
if getattr(act, "slots", None): arm.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(act.frame_range[0]))
BONE = {pb.name.split(":")[-1]: pb.name for pb in arm.pose.bones}
PARENT = {k: (arm.data.bones[v].parent.name.split(":")[-1] if arm.data.bones[v].parent else None) for k, v in BONE.items()}
Aw = arm.matrix_world.copy(); Aw_inv = Aw.inverted()
BASE = {k: Aw @ arm.pose.bones[v].matrix for k, v in BONE.items()}
REST = {k: Aw @ arm.data.bones[v].matrix_local for k, v in BONE.items()}
arm.animation_data.action = None
for o in take: bpy.data.objects.remove(o, do_unlink=True)
bpy.data.actions.remove(act)

def apply_pose(W):
    for k, v in BONE.items():
        b = arm.data.bones[v]
        M = Aw_inv @ W[k]
        if b.parent:
            basis = b.matrix_local.inverted() @ b.parent.matrix_local @ (Aw_inv @ W[PARENT[k]]).inverted() @ M
        else:
            basis = b.matrix_local.inverted() @ M
        arm.pose.bones[v].matrix_basis = basis

# --- hands: a palm frame from the rest pose (fingers straight, palms down) ---
FINGERS = ("Thumb", "Index", "Middle", "Ring", "Pinky")
RADIUS = {"Thumb": 0.0095, "Index": 0.0085, "Middle": 0.009, "Ring": 0.0085, "Pinky": 0.0075}
PALM = 0.012      # bone line to palm skin
HAND = {}
for side in ("Left", "Right"):
    H = REST[side + "Hand"]; w = H.translation
    m1, i1, p1 = (REST[f"{side}Hand{f}1"].translation for f in ("Middle", "Index", "Pinky"))
    a0, l0 = (m1 - w).normalized(), (i1 - p1).normalized()
    n0 = a0.cross(l0).normalized()
    if n0.z > 0: n0 = -n0                      # palms face down in the rest pose
    B0 = frame(n0, l0)
    sign = 1 if (B0.col[1].cross(B0.col[0])).dot(a0) > 0 else -1
    centre = w + (m1 - w) * 0.55 + n0 * PALM
    fingers = {}
    for f in FINGERS:
        chain = [f"{side}Hand{f}{j}" for j in (1, 2, 3, 4)]
        d = (REST[chain[1]].translation - REST[chain[0]].translation).normalized()
        toward = n0 if f != "Thumb" else (n0 - l0 * 0.7).normalized()
        axis_w = d.cross(toward).normalized()
        joints = []
        for j, name in enumerate(chain):
            parent = REST[side + "Hand"] if j == 0 else REST[chain[j - 1]]
            joints.append({"L": parent.inverted() @ REST[name],
                           "axis": (REST[name].to_3x3().inverted() @ axis_w).normalized()})
        fingers[f] = joints
    HAND[side] = {"B0": B0, "sign": sign, "centre": centre, "rest": H, "fingers": fingers}

def hand_world(side, n, l, c, anchor=None):
    """Hand bone world matrix that puts the palm centre (or the anchor bone's head) at c, the palm facing n,
    the knuckles (pinky to index) along l."""
    h = HAND[side]
    R = frame(n, l) @ h["B0"].transposed()
    p = REST[side + anchor].translation if anchor else h["centre"]
    return Matrix.Translation(c - p) @ rot_about(R, p) @ h["rest"]

def finger_chain(Hw, side, f, ang, swing=None):
    """World matrices of a finger's joints 1-4: joint 1 optionally swung (a local rotation, for the thumb), then curled."""
    out, M = [], Hw
    for j, d in enumerate(HAND[side]["fingers"][f]):
        M = M @ d["L"]
        if j == 0 and swing is not None: M = M @ swing.to_matrix().to_4x4()
        if j < 3: M = M @ Matrix.Rotation(math.radians(ang[j]), 4, d["axis"])
        out.append(M)
    return out

def finger_hits(Hw, side, f, ang, swing, tree, to_local):
    r = RADIUS[f]
    ch = finger_chain(Hw, side, f, ang, swing); out = []
    for s in range(1 if f == "Thumb" else 0, 3):          # the thumb's first bone is palm (thenar) flesh
        a, b = to_local @ ch[s].translation, to_local @ ch[s + 1].translation
        for k in range(5):
            p = a.lerp(b, (k + 0.5) / 5)
            loc, nrm, _, dist = tree.find_nearest(p)
            if loc is not None and dist < r * 0.75:          # distance only: some of the asset's faces point inwards
                out.append(s); break
    return out

def aim_finger(Hw, side, f, want, tree, to_local):
    """The finger's base swing whose straight finger is clear of tree and closest to want (a world direction)."""
    j1 = HAND[side]["fingers"][f]
    M1 = Hw @ j1[0]["L"]
    rest_dir = (j1[1]["L"].translation).normalized()
    to_l = M1.to_3x3().inverted()
    want = want.normalized()
    best = None
    n = 400
    for i in range(n):                                   # Fibonacci sphere of directions
        zc = 1 - 2 * (i + 0.5) / n; rr = math.sqrt(1 - zc * zc); th = i * 2.399963
        d = Vector((rr * math.cos(th), rr * math.sin(th), zc))
        score = d.dot(want)
        if score < 0.3 or (best and score <= best[0]): continue
        swing = rest_dir.rotation_difference((to_l @ d).normalized())
        if not finger_hits(Hw, side, f, (0, 0, 0), swing, tree, to_local):
            best = (score, swing)
    return best[1] if best else Quaternion()

def wrap_finger(Hw, side, f, tree, to_local, limit=(95, 110, 80), couple=0.75, swing=None):
    """The curl (MCP and PIP searched, DIP = couple x PIP) that lies closest along the surface without going in:
    each bone's nearest point to the surface counts, so the finger hugs the grip instead of stopping at the first touch."""
    r = RADIUS[f] * 0.8
    first = finger_hits(Hw, side, f, (0, 0, 0), swing, tree, to_local)
    def cost(a1, a2):
        ch = finger_chain(Hw, side, f, (a1, a2, min(a2 * couple, limit[2])), swing)
        total = 0.0
        for s in range(1 if f == "Thumb" else 0, 3):
            a, b = to_local @ ch[s].translation, to_local @ ch[s + 1].translation
            near = 1.0
            for k in range(4):
                d = tree.find_nearest(a.lerp(b, (k + 0.5) / 4))[3]
                if d is None: continue
                if d < r: return None
                near = min(near, d)
            total += min(near - r, 0.03)
        return total
    best = (1e9, 0, 0)
    for a1 in range(0, int(limit[0]) + 1, 5):
        for a2 in range(0, int(limit[1]) + 1, 5):
            c = cost(a1, a2)
            if c is not None and (c < best[0] - 1e-4 or (abs(c - best[0]) < 1e-4 and a1 + a2 > best[1] + best[2])):
                best = (c, a1, a2)
    b1, b2 = best[1], best[2]
    for a1 in range(max(b1 - 4, 0), min(b1 + 5, int(limit[0]) + 1)):
        for a2 in range(max(b2 - 4, 0), min(b2 + 5, int(limit[1]) + 1)):
            c = cost(a1, a2)
            if c is not None and c < best[0] - 1e-5: best = (c, a1, a2)
    _, a1, a2 = best
    return [float(a1), float(a2), round(min(a2 * couple, limit[2]), 1)], first

def solve_arm(W, side, Hw, pole, twist=0.5):
    """Two-bone IK: upper arm and forearm reach the hand's wrist; the elbow bends in its own hinge plane towards pole."""
    up, fore, hand = side + "Arm", side + "ForeArm", side + "Hand"
    S, E, Wr = BASE[up].translation, BASE[fore].translation, BASE[hand].translation
    L1, L2 = (E - S).length, (Wr - E).length
    T = Hw.translation
    D = min((T - S).length, (L1 + L2) * 0.999)
    dW = (T - S).normalized()
    dp = (pole - S) - dW * (pole - S).dot(dW); dp.normalize()
    x = (L1 * L1 - L2 * L2 + D * D) / (2 * D); y = math.sqrt(max(L1 * L1 - x * x, 0))
    E2 = S + dW * x + dp * y
    h0 = (E - S).cross(Wr - E).normalized(); h1 = (E2 - S).cross(T - E2).normalized()
    R1 = frame(E2 - S, h1) @ frame(E - S, h0).transposed()
    W[up] = rot_about(R1, S) @ BASE[up]
    f1 = rot_about(R1, S) @ BASE[fore]
    d1 = (R1 @ (Wr - E)).normalized(); d2 = (T - E2).normalized()
    W[fore] = rot_about(d1.rotation_difference(d2).to_matrix(), E2) @ f1
    # share the wrist's twist with the forearm, so the sleeve turns with the hand instead of only the wrist
    neutral = W[fore].to_quaternion() @ (BASE[fore].to_quaternion().inverted() @ BASE[hand].to_quaternion())
    delta = Hw.to_quaternion() @ neutral.inverted()
    v = Vector((delta.x, delta.y, delta.z)); p = d2 * v.dot(d2)
    q = Quaternion((delta.w, p.x, p.y, p.z))
    if q.magnitude > 1e-6:
        q.normalize()
        if q.w < 0: q.negate()
        if q.angle > 1e-4: W[fore] = rot_about(Quaternion(q.axis, q.angle * twist).to_matrix(), E2) @ W[fore]
    W[hand] = Hw
    return (T - S).length - (L1 + L2)

def pose_arms(hands):
    """hands: side -> (hand world, pole point, finger angles); returns world matrices for every bone."""
    W = dict(BASE)
    for side, (Hw, pole, fingers) in hands.items():
        solve_arm(W, side, Hw, pole)
        for f in FINGERS:
            for j, M in enumerate(finger_chain(Hw, side, f, fingers[f]["ang"], fingers[f]["swing"])):
                W[f"{side}Hand{f}{j + 1}"] = M
    return W

# --- the rifle: parts baked into rifle space; the magazine (with its rounds) twice, the bolt carrier and the trigger move ---
before = set(bpy.data.objects)
fbx_import(os.path.join(ROOT, "FPS Guns 4K - Rifle 1", "Models", "Rifle 1.fbx"))
new = [o for o in bpy.data.objects if o not in before]
PART = {}
for o in new:
    if o.type == 'MESH':
        o.data = o.data.copy(); o.data.transform(o.matrix_world)
        PART[o.name] = o
for o in new:
    if o.type == 'MESH': o.parent = None; o.matrix_world = Matrix.Identity(4)
for o in new:
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
MAG_PARTS = ["Magazine1"] + [n for n in PART if n.startswith("Bullet")]
GROUP = {n: "magazine" for n in MAG_PARTS}
GROUP.update({"Shell_Remover": "bolt", "Trigger_44": "trigger"})

def verts_of(names):
    return np.array([v.co[:] for n in names for v in PART[n].data.vertices])

def grip_axis(names, up=Z):
    v = verts_of(names); c = v.mean(axis=0)
    w, e = np.linalg.eigh(np.cov((v - c).T))
    g = Vector(e[:, -1]).normalized()
    return Vector(c), (g if g.dot(up) > 0 else -g)

mag_v = verts_of(["Magazine1"])
MAG_PIVOT = Vector((0, mag_v[mag_v[:, 2] > mag_v[:, 2].max() - 0.02][:, 1].max(), 0.172))   # the front lug it rocks about
bolt_v = verts_of(["Shell_Remover"])
HANDLE = Vector(bolt_v[bolt_v[:, 0] > 0.03].mean(axis=0))            # charging handle knob, right side
TRIGGER = Vector((0, verts_of(["Trigger_44"])[:, 1].mean(), verts_of(["Trigger_44"])[:, 2].max()))
trig_v = verts_of(["Trigger_44"]); band = trig_v[np.abs(trig_v[:, 2] - 0.152) < 0.006]
TRIGGER_FACE = Vector((0, band[:, 1].max(), 0.152))                  # where the finger pad pulls
PADDLE = Vector(verts_of(["Mag_Holder_Back"]).mean(axis=0))          # magazine release, behind the magazine
BOLT_TRAVEL = 0.095
PIVOT = Vector((0, -0.16, 0.13))                                     # the gun turns about the right hand's grip

TREES = {
    "pistol": bvh([PART[n] for n in ("Main_Grip", "Mag_Holder", "Mag_Holder_Back", "Trigger_44", "Main_Receiver2", "Mode_Switch")]),
    "fore": bvh([PART[n] for n in ("Foregrip_Main", "Foregrip_Switch", "Foregrip_Switch1", "Forend", "Cage")]),
    "mag": bvh([PART[n] for n in MAG_PARTS]),
    "trigger": bvh([PART[n] for n in ("Trigger_44", "Mag_Holder", "Mag_Holder_Back")]),
    "paddle": bvh([PART[n] for n in ["Mag_Holder_Back", "Mag_Holder"] + MAG_PARTS]),
    "handle": bvh([PART[n] for n in ("Shell_Remover", "Receiver_Cover", "Main_Receiver2")]),
}

def grip_hand(side, tree, centre, g, along, wrap, gap=0.002):
    """Hand on a grip (rifle space): palm on the grip's outer side (wrap turns it towards the back), knuckles up the grip."""
    out = -X if side == "Right" else X          # from the palm into the grip
    fwd = (Y - g * Y.dot(g)).normalized()
    n = (out * math.cos(math.radians(wrap)) + fwd * math.sin(math.radians(wrap))).normalized()
    c = centre + g * along
    hit = tree.ray_cast(c - n * 0.2, n)[0]
    return n, g, hit - n * gap

def build_rifle():
    """One skinned mesh (rifle_root, magazine, magazine_spare, bolt, trigger) on an armature in rifle space."""
    objs = []
    for name, o in list(PART.items()):
        group = GROUP.get(name, "rifle_root")
        copies = [(o, group)]
        if group == "magazine":
            d = o.copy(); d.data = o.data.copy(); bpy.context.scene.collection.objects.link(d)
            copies.append((d, "magazine_spare"))
        for ob, g in copies:
            vg = ob.vertex_groups.new(name=g); vg.add(range(len(ob.data.vertices)), 1.0, 'REPLACE')
            col = ob.data.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
            tint = {"magazine": (0.8, 0.6, 0.2, 1), "magazine_spare": (0.85, 0.35, 0.15, 1), "bolt": (0.6, 0.15, 0.15, 1)}.get(g, (0.2, 0.21, 0.23, 1))
            for c in col.data: c.color = tint
            objs.append(ob)
    target = PART["Main_Receiver2"]
    with bpy.context.temp_override(active_object=target, object=target, selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    target.name = target.data.name = "SK_RifleFP"
    target.data.color_attributes.active_color = target.data.color_attributes["Col"]
    rig = bpy.data.objects.new("RifleRig", bpy.data.armatures.new("RifleFP"))
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[rig], selected_editable_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        heads = {"rifle_root": Vector(), "magazine": MAG_PIVOT, "magazine_spare": MAG_PIVOT,
                 "bolt": Vector((0, HANDLE.y, HANDLE.z)), "trigger": TRIGGER}
        for name, h in heads.items():
            eb = rig.data.edit_bones.new(name); eb.head = h; eb.tail = h + Y * 0.05; eb.roll = 0
            if name != "rifle_root": eb.parent = rig.data.edit_bones["rifle_root"]
        bpy.ops.object.mode_set(mode='OBJECT')
    target.parent = rig
    mod = target.modifiers.new("Armature", 'ARMATURE'); mod.object = rig
    return rig, target

def rifle_pose(rig, local):
    """local: bone -> 4x4 in rifle space (moves the bone's rest); missing bones stay at rest."""
    for pb in rig.pose.bones:
        R = pb.bone.matrix_local
        pb.matrix_basis = R.inverted() @ local.get(pb.name, Matrix.Identity(4)) @ R

# --- views ---
def eye_matrix():
    A = ue(VM["hold"]["arms"]); E = A.inverted()          # the eye (Unreal camera) in arms space
    fwd, up = E.to_3x3() @ X, E.to_3x3() @ Z               # Unreal camera: +X forward, +Z up (already flipped by ue())
    z = -fwd.normalized(); x = up.cross(z).normalized()
    M = Matrix((x, z.cross(x), z)).transposed().to_4x4(); M.translation = E.translation
    return M

def camera(name, M, fov=70):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(cam)
    cam.matrix_world = M; cam.data.sensor_fit = 'HORIZONTAL'; cam.data.angle = math.radians(fov); cam.data.clip_start = 0.01
    return cam

def look_at(pos, target, up=Z):
    z = (pos - target).normalized(); x = up.cross(z).normalized()
    M = Matrix((x, z.cross(x), z)).transposed().to_4x4(); M.translation = pos
    return M

def render(cam, path, res=(960, 540)):
    sc = bpy.context.scene; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path

def sheet(paths, cols, out):
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size; rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * h, cols * w, 4), np.float32)
    for i, im in enumerate(imgs):
        px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
        r, c = divmod(i, cols)
        canvas[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = px.reshape(h, w, 4)
    img = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    img.pixels.foreach_set(canvas.ravel()); img.filepath_raw = out; img.file_format = 'PNG'; img.save()
    for im in imgs: bpy.data.images.remove(im)
    print("sheet", out)

def setup_render():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = True; sh.show_shadows = False
    col = arms_mesh.data.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    for c in col.data: c.color = (0.62, 0.5, 0.42, 1)
    arms_mesh.data.color_attributes.active_color = col
    os.makedirs(SHOTS, exist_ok=True)

# --- the hold: hands placed on the grips at the authored rifle placement, fingers fitted ---
G0 = ue(VM["hold"]["rifle"])                 # rifle space -> world at the hold
G0i = G0.inverted()
eye = eye_matrix()
cam_right, cam_up, cam_fwd = eye.to_3x3() @ X, eye.to_3x3() @ Y, -(eye.to_3x3() @ Z)
IDENT = Matrix.Identity(4)

def palm_frame(side, n, l):
    """Palm normal, knuckle line (pinky to index) and finger direction for a hand placed with hand_world(n, l)."""
    B = frame(n, l)
    return B.col[0], B.col[1], HAND[side]["sign"] * B.col[1].cross(B.col[0])

def grip_fingers(side, Hw, palm, tree, thumb, index=None, thumb_at=None):
    """Fingers closed on tree (all in rifle space); the thumb first aimed (thumb = palm-normal, knuckle-line,
    finger-direction weights) or at a point (thumb_at = (point, tree)); index = (point, tree) aims the index finger."""
    n, l, a = palm
    out = {}
    for f in FINGERS:
        if f == "Thumb" and thumb_at:
            base = finger_chain(Hw, side, f, (0, 0, 0))[1].translation
            sw = aim_finger(Hw, side, f, thumb_at[0] - base, thumb_at[1], IDENT)
            ang, first = wrap_finger(Hw, side, f, thumb_at[1], IDENT, limit=(0, 70, 80), couple=1.0, swing=sw)
        elif f == "Thumb":
            sw = aim_finger(Hw, side, f, n * thumb[0] + l * thumb[1] + a * thumb[2], tree, IDENT)
            ang, first = wrap_finger(Hw, side, f, tree, IDENT, limit=(0, 70, 80), couple=1.0, swing=sw)
        elif f == "Index" and index:
            knuckle = finger_chain(Hw, side, f, (0, 0, 0))[0].translation
            sw = aim_finger(Hw, side, f, index[0] - knuckle, index[1], IDENT)
            ang, first = wrap_finger(Hw, side, f, index[1], IDENT, limit=(0, 100, 70), couple=0.7, swing=sw)
        else:
            sw = None
            ang, first = wrap_finger(Hw, side, f, tree, IDENT)
        if first: print("  ", side, f, "starts inside at segments", first)
        out[f] = {"ang": ang, "swing": sw}
    return out

def place(side, n, l, c, anchor=None):
    return hand_world(side, n, l, c, anchor), palm_frame(side, n, l)

# Hands in rifle space (the left hand's anchors move with the part they hold) and their finger presets.
AN, PRESET = {}, {"Right": {}, "Left": {}}
c, g = grip_axis(["Main_Grip"])
n, l, _ = grip_hand("Right", TREES["pistol"], c, g, 0.026, 25)
AN["grip"], palm = place("Right", n, l, Vector((0.028, -0.150, 0.150)), "HandIndex1")
PRESET["Right"]["trigger"] = grip_fingers("Right", AN["grip"], palm, TREES["pistol"], (1.0, 0.2, 0.6), (TRIGGER_FACE + Vector((0.012, 0.012, 0)), TREES["trigger"]))
safe = dict(PRESET["Right"]["trigger"])
safe["Index"] = {"ang": [0, 6, 4], "swing": aim_finger(AN["grip"], "Right", "Index", Vector((0.25, 1, 0.35)), TREES["pistol"], IDENT)}
PRESET["Right"]["safe"] = safe                                     # trigger finger straight along the receiver

c, g = grip_axis(["Foregrip_Main"])
n, l, p = grip_hand("Left", TREES["fore"], c, g, 0.0, 30)
AN["fore"], palm = place("Left", n, l, p)
PRESET["Left"]["fore"] = grip_fingers("Left", AN["fore"], palm, TREES["fore"], (1.0, 0.3, 0.6))

mag_axis = Vector((0, -0.4, 0.92)).normalized()
n, l, p = grip_hand("Left", TREES["mag"], Vector((0, -0.025, 0.11)), mag_axis, 0.0, 10)
AN["mag"], palm = place("Left", n, l, p)
PRESET["Left"]["mag"] = grip_fingers("Left", AN["mag"], palm, TREES["mag"], (0.5, 0.2, -0.8))
PRESET["Left"]["paddle"] = grip_fingers("Left", AN["mag"], palm, TREES["mag"], None, thumb_at=(PADDLE, TREES["paddle"]))

AN["handle"], palm = place("Left", -X, Y, Vector((0.062, HANDLE.y + 0.014, HANDLE.z - 0.04)), "HandIndex1")
PRESET["Left"]["handle"] = grip_fingers("Left", AN["handle"], palm, TREES["handle"], (1.0, 0.0, 0.5))
for side in PRESET:
    PRESET[side]["open"] = {f: {"ang": {"Thumb": [0, 15, 15], "Index": [18, 28, 18], "Middle": [24, 34, 22],
                                         "Ring": [30, 40, 26], "Pinky": [36, 44, 28]}[f], "swing": None} for f in FINGERS}
for side, ps in PRESET.items():
    for name, fp in ps.items(): print(side, name, {f: fp[f]["ang"] for f in FINGERS})

# --- tracks: keys at frames (60 fps), Hermite through the keys (Catmull-Rom tangents; ends and "flat" keys stop) ---
FPS = 60

def hermite(ts, ps, t, flat=()):
    if t <= ts[0]: return ps[0]
    if t >= ts[-1]: return ps[-1]
    i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
    h = ts[i + 1] - ts[i]; s = (t - ts[i]) / h
    def tan(k):
        if k == 0 or k == len(ts) - 1 or k in flat: return ps[k] * 0
        return (ps[k + 1] - ps[k - 1]) / (ts[k + 1] - ts[k - 1])
    m0, m1 = tan(i) * h, tan(i + 1) * h
    s2, s3 = s * s, s * s * s
    return ps[i] * (2 * s3 - 3 * s2 + 1) + m0 * (s3 - 2 * s2 + s) + ps[i + 1] * (3 * s2 - 2 * s3) + m1 * (s3 - s2)

def scalar_track(keys, t):
    ts = [k[0] for k in keys]
    return float(hermite(ts, [np.array([k[1]], float) for k in keys], t, {i for i, k in enumerate(keys) if "flat" in k[2:]})[0])

def rot_vec(q):
    if q.w < 0: q = q.copy(); q.negate()
    ax, ang = q.to_axis_angle()
    return np.array(ax) * ang

def pose_track(keys, t, world):
    """keys: (frame, space, matrix, *flags); world(space, matrix, t) -> world matrix of that key at time t.
    Every key is evaluated at the current time in its own space, so a hand keyed on a moving part follows it."""
    ts = [k[0] for k in keys]
    flat = {i for i, k in enumerate(keys) if "flat" in k[3:]}
    if t <= ts[0]: return world(keys[0][1], keys[0][2], t)
    if t >= ts[-1]: return world(keys[-1][1], keys[-1][2], t)
    i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
    idx = sorted({max(i - 1, 0), i, i + 1, min(i + 2, len(ts) - 1)})
    M = {k: world(keys[k][1], keys[k][2], t) for k in idx}
    sub_t = [ts[k] for k in idx]
    sub_flat = {j for j, k in enumerate(idx) if k in flat or k in (0, len(ts) - 1)}
    loc = hermite(sub_t, [np.array(M[k].to_translation()) for k in idx], t, sub_flat)
    q0 = M[i].to_quaternion()
    rv = []
    for k in idx:
        d = q0.inverted() @ M[k].to_quaternion()
        rv.append(rot_vec(d))
    r = hermite(sub_t, rv, t, sub_flat)
    ang = float(np.linalg.norm(r))
    q = q0 @ (Quaternion(Vector(r / ang), ang) if ang > 1e-9 else Quaternion())
    out = q.to_matrix().to_4x4() @ Matrix.Diagonal(M[i].to_scale().to_4d())
    out.translation = Vector(loc)
    return out

def finger_track(keys, side, t):
    """keys: (frame, preset); presets blend over each gap (smoothstep)."""
    if t <= keys[0][0]: return PRESET[side][keys[0][1]]
    if t >= keys[-1][0]: return PRESET[side][keys[-1][1]]
    i = max(k for k in range(len(keys) - 1) if keys[k][0] <= t)
    s = (t - keys[i][0]) / (keys[i + 1][0] - keys[i][0]); s = s * s * (3 - 2 * s)
    A, B = PRESET[side][keys[i][1]], PRESET[side][keys[i + 1][1]]
    out = {}
    for f in FINGERS:
        qa, qb = A[f]["swing"] or Quaternion(), B[f]["swing"] or Quaternion()
        out[f] = {"ang": [a + (b - a) * s for a, b in zip(A[f]["ang"], B[f]["ang"])], "swing": qa.slerp(qb, s)}
    return out

def gun_offset(v):
    """Rifle placement from an offset: cm right/up/forward and degrees pitch (muzzle up)/yaw (left) in eye space, turned
    about the right hand's grip; roll (top right) about the rifle's own bore line through the grip."""
    p = G0 @ PIVOT
    R = Matrix.Rotation(math.radians(v[3]), 3, cam_right) @ Matrix.Rotation(math.radians(v[4]), 3, cam_up)
    roll = rot_about(Matrix.Rotation(math.radians(v[5]), 3, Y), PIVOT)
    return Matrix.Translation((cam_right * v[0] + cam_up * v[1] + cam_fwd * v[2]) / 100) @ rot_about(R, p) @ G0 @ roll

def rock(deg, down=0.0, back=0.0):
    """Magazine pose in rifle space: rocked about its front lug (positive drops the rear), then moved down/back (m)."""
    return Matrix.Translation(Vector((0, -back, -down))) @ rot_about(Matrix.Rotation(math.radians(deg), 3, X), MAG_PIVOT)

def eye_move(M, right=0.0, up=0.0, fwd=0.0, pitch=0.0, roll=0.0, about=None):
    """A world pose moved in eye space (cm, degrees), turned about `about` (world point; default its origin)."""
    p = about if about is not None else M.translation
    R = Matrix.Rotation(math.radians(pitch), 3, cam_right) @ Matrix.Rotation(math.radians(roll), 3, cam_fwd)
    return Matrix.Translation((cam_right * right + cam_up * up + cam_fwd * fwd) / 100) @ rot_about(R, p) @ M

POUCH = eye_move(G0, -14, -34, -6, -25, -15, G0 @ MAG_PIVOT)        # where the fresh magazine comes from (off screen)

class Clip:
    def __init__(self, name, frames, gun, lh=None, lfing=None, rfing=None, mag=None, spare=None, bolt=None, mag_fall=None,
                 spare_from=None, arms=True):
        self.name, self.n, self.gun = name, frames, gun
        self.lh = lh or [(0, "fore", None)]
        self.lfing, self.rfing = lfing or [(0, "fore")], rfing or [(0, "trigger")]
        self.mag = mag or [(0, "gun", IDENT)]
        self.spare = spare or [(0, "gun", IDENT)]
        self.bolt = bolt or [(0, 0.0)]
        self.mag_fall, self.spare_from, self.arms = mag_fall, spare_from, arms

    def gun_at(self, t):
        ts = [k[0] for k in self.gun]
        v = hermite(ts, [np.array(k[1], float) for k in self.gun], t, {i for i, k in enumerate(self.gun) if "flat" in k[2:]})
        return gun_offset(v)

    def parts(self, t):
        """World placement of the rifle and of each part (rifle-space-rest -> world) at frame t."""
        G = self.gun_at(t)
        world = lambda space, M, tt: (self.gun_at(tt) @ M) if space == "gun" else M
        bolt = scalar_track(self.bolt, t)
        out = {"gun": G, "bolt": G @ Matrix.Translation(-Y * bolt), "bolt_travel": bolt}
        if self.mag_fall is not None and t > self.mag_fall:
            f0 = self.mag_fall
            A, B = pose_track(self.mag, f0 - 1, world), pose_track(self.mag, f0, world)
            v = (B.translation - A.translation) * FPS
            w = rot_vec(B.to_quaternion() @ A.to_quaternion().inverted()) * FPS + np.array(cam_fwd) * 3.0
            dt = (t - f0) / FPS
            p = B.translation + v * dt + Vector((0, 0, -4.9)) * dt * dt
            ang = float(np.linalg.norm(w)) * dt
            spin = Quaternion(Vector(w).normalized(), ang) if ang > 1e-9 else Quaternion()
            M = (spin @ B.to_quaternion()).to_matrix().to_4x4(); M.translation = p
            out["magazine"] = M
            out["magazine_hidden"] = t > f0 + 30
        else:
            out["magazine"] = pose_track(self.mag, t, world)
            out["magazine_hidden"] = False
        out["magazine_keyed"] = pose_track(self.mag, t, world)        # what the hand follows (the tossed one falls)
        out["magazine_spare"] = pose_track(self.spare, t, world)
        out["spare_hidden"] = self.spare_from is None or t < self.spare_from
        return out

    def pose(self, t):
        P = self.parts(t)
        def world(space, M, tt):
            """eye: M is the world pose; gun: M is a hand pose in rifle space; an anchor: the hand holds that part,
            M (optional) shifts it in rifle space first."""
            if space == "eye": return M
            if space == "gun": return P["gun"] @ M
            part, hand = ANCHOR[space]
            return P[part] @ (M if M is not None else IDENT) @ AN[hand]
        lh = pose_track([(k[0], k[1], k[2], *k[3:]) for k in self.lh], t, world)
        rh = P["gun"] @ AN["grip"]
        hands = {"Right": (rh, POLE_R, finger_track(self.rfing, "Right", t)),
                 "Left": (lh, POLE_L, finger_track(self.lfing, "Left", t))}
        return pose_arms(hands), P

    def rifle_local(self, P):
        Gi = P["gun"].inverted()
        tiny = Matrix.Diagonal((0.001, 0.001, 0.001, 1))
        mag = Gi @ P["magazine"]; spare = Gi @ P["magazine_spare"]
        if P["magazine_hidden"]: mag = mag @ Matrix.Translation(MAG_PIVOT) @ tiny @ Matrix.Translation(-MAG_PIVOT)
        if P["spare_hidden"]: spare = spare @ Matrix.Translation(MAG_PIVOT) @ tiny @ Matrix.Translation(-MAG_PIVOT)
        return {"magazine": mag, "magazine_spare": spare, "bolt": Matrix.Translation(-Y * P["bolt_travel"])}

ANCHOR = {"fore": ("gun", "fore"), "grip": ("gun", "grip"), "mag": ("magazine_keyed", "mag"),
          "spare": ("magazine_spare", "mag"), "handle": ("bolt", "handle")}
S_r, S_l = BASE["RightArm"].translation, BASE["LeftArm"].translation
POLE_R = S_r - cam_up * 0.45 + cam_right * 0.2
POLE_L = S_l - cam_up * 0.4 - cam_right * 0.5
REST_GUN = [0, 0, 0, 0, 0, 0]

def reload_keys(empty):
    """The AK reload: thumb on the paddle, rock the magazine out and toss it, a fresh one from the pouch, hook its front
    lug and rock it in (click). Empty adds the under-rack: the rifle rolls onto its left side and the left hand pulls
    the charging handle back and lets it slam."""
    E = 6 if empty else 0                           # the empty reload is a touch less hurried
    seat = 74 + E
    L = np.array([-8, 10, 3, 20, 11, 30], float)     # the reload hold: rifle up, in and canted to show the magazine well
    at = lambda *d: list(L + np.array(d, float))
    gun = [(0, REST_GUN), (14, at(0, -1, 0, -2, -1, -4)), (20, at(0, 0, 0, 0, 0, 0)),
           (28 + E, at(-0.6, -1.2, 0, -3, -0.5, -3)), (36 + E, at(0.2, 0.4, 0, 0.5, 0, 0)),
           (60 + E, at(-0.5, 0.5, 0, 0, 0.5, 1)), (seat - 4, at(-0.5, 0.6, 0, -0.5, 0.5, 1)),
           (seat, at(-0.5, 1.6, 0.4, 2.5, 1, -1)), (seat + 6, at(-0.3, 0.2, 0, -0.5, 0.3, 0.5))]
    mag = [(0, "gun", IDENT), (16, "gun", IDENT, "flat"), (26 + E, "gun", rock(24)), (32 + E, "gun", rock(30, 0.06, 0.01)),
           (34 + E, "gun", rock(33, 0.075, 0.015)), (44 + E, "gun", rock(40, 0.2, 0.04))]
    spare = [(0, "eye", POUCH), (48 + E, "eye", POUCH, "flat"), (seat - 14, "gun", rock(28, 0.03)),
             (seat - 6, "gun", rock(28), "flat"), (seat, "gun", IDENT, "flat"), (200, "gun", IDENT)]
    lh = [(0, "fore", None), (4, "fore", None, "flat"), (16, "mag", None, "flat"), (34 + E, "mag", None),
          (48 + E, "spare", None, "flat"), (seat - 6, "spare", None), (seat, "spare", None, "flat"),
          (seat + 5, "gun", Matrix.Translation(Vector((0, -0.01, -0.035))) @ AN["mag"])]
    lf = [(0, "fore"), (6, "open"), (13, "paddle"), (34 + E, "paddle"), (40 + E, "open"), (46 + E, "mag"), (seat, "mag"), (seat + 5, "open")]
    rf = [(0, "trigger"), (10, "safe")]
    bolt = [(0, 0.0)]
    if not empty:
        n = 120
        gun += [(100, [-1.5, 1.5, 0.5, 4, 2, 5]), (108, [0.4, -0.5, 0, -1.2, -0.5, -1.5]), (n, REST_GUN)]
        lh += [(96, "fore", None, "flat"), (n, "fore", None)]
        lf += [(90, "open"), (98, "fore")]
        rf += [(96, "safe"), (106, "trigger")]
    else:
        n, rk = 164, seat + 26                       # rk: the hand is on the handle
        gun += [(seat + 18, [-3, 7, 2, 15, 10, -45]), (rk, [-1, 7, 1.5, 15, 14, -75]), (rk + 8, [-1.6, 6.4, 0.8, 14, 14, -77]),
                (rk + 12, [-0.4, 7.6, 1.7, 16.5, 13.5, -72]), (rk + 18, [-1, 6.8, 1.5, 14.5, 14, -75]),
                (rk + 40, [0.4, -0.5, 0, -1, -0.5, 2]), (n, REST_GUN)]
        lh += [(rk - 8, "handle", Matrix.Translation(Vector((0.03, 0.02, -0.07)))), (rk, "handle", None, "flat"),
               (rk + 8, "handle", None, "flat"), (rk + 14, "gun", Matrix.Translation(Vector((0.035, -0.01, 0.06))) @ AN["handle"]),
               (rk + 23, "gun", Matrix.Translation(Vector((-0.03, 0.0, 0.07))) @ AN["fore"]),
               (rk + 31, "fore", None, "flat"), (n, "fore", None)]
        lf += [(rk - 10, "open"), (rk - 2, "handle"), (rk + 9, "handle"), (rk + 13, "open"), (rk + 24, "open"), (rk + 31, "fore")]
        rf += [(rk + 30, "safe"), (rk + 40, "trigger")]
        bolt = [(0, 0.0), (rk, 0.0, "flat"), (rk + 8, BOLT_TRAVEL, "flat"), (rk + 9, BOLT_TRAVEL, "flat"), (rk + 12, 0.0, "flat")]
    return Clip("ReloadEmpty" if empty else "ReloadTac", n, gun, lh, lf, rf, mag, spare, bolt, mag_fall=34 + E, spare_from=44 + E)

CLIPS = {
    "Idle": Clip("Idle", 120, [(0, REST_GUN), (60, [0, 0.15, 0, 0.3, 0, 0.2]), (120, REST_GUN)]),
    "Equip": Clip("Equip", 36, [(0, [6, -30, -6, -35, -10, 35]), (14, [0.5, 1.5, 0.5, 4, 1, -3]), (22, [-0.2, -0.4, 0, -1, 0, 1]), (36, REST_GUN)],
                  lh=[(0, "eye", eye_move(G0 @ AN["fore"], -10, -30, -10)), (10, "eye", eye_move(G0 @ AN["fore"], -3, -6, -2)), (18, "fore", None, "flat"), (36, "fore", None)],
                  lfing=[(0, "open"), (12, "open"), (20, "fore")], rfing=[(0, "safe"), (22, "trigger")]),
    "ReloadTac": reload_keys(False),
    "ReloadEmpty": reload_keys(True),
    "Fire": Clip("Fire", 6, [(0, REST_GUN)], bolt=[(0, 0.0), (2, BOLT_TRAVEL, "flat"), (6, 0.0, "flat")], arms=False),
}

# --- run ---
setup_render()
rig, rifle_mesh = build_rifle()

def show(clip, t):
    W, P = clip.pose(t)
    apply_pose(W)
    rig.matrix_world = P["gun"]
    rifle_pose(rig, clip.rifle_local(P))

def contact_sheet(clip, every=6, cols=6):
    cam = camera("FP_" + clip.name, eye)
    paths = []
    for f in list(range(0, clip.n + 1, every)):
        show(clip, f)
        paths.append(render(cam, os.path.join(SHOTS, f"{clip.name}_{f:03d}.png"), (480, 270)))
    sheet(paths, cols, os.path.join(SHOTS, f"{clip.name}_sheet.png"))
    for p in paths: os.remove(p)

if MODE != "export":
    for name in MODE.split(","):
        if name == "hold":
            show(CLIPS["Idle"], 0)
            def close(name, target, offset, dist=0.32):
                p = G0 @ target; d = (G0.to_3x3() @ offset).normalized()
                cam = camera(name, look_at(p + d * dist, p, G0.to_3x3() @ Z), 40); cam.data.clip_start = dist - 0.12
                return cam
            views = [camera("FP", eye),
                     close("RightFromLeft", Vector((0, -0.17, 0.12)), Vector((-1, 0.3, 0.1))),
                     close("RightFromRight", Vector((0, -0.17, 0.12)), Vector((1, 0.2, 0.1))),
                     close("LeftFromRight", Vector((0, 0.15, 0.13)), Vector((1, 0.1, -0.2))),
                     close("LeftFromLeft", Vector((0, 0.15, 0.13)), Vector((-1, -0.1, -0.2))),
                     close("Below", Vector((0, -0.02, 0.12)), Vector((0.2, 0.1, -1)), 0.5)]
            shots = [render(v, os.path.join(SHOTS, f"hold_{v.name}.png"), (640, 360)) for v in views]
            sheet(shots, 3, os.path.join(SHOTS, "hold_sheet.png"))
        elif ":" in name:                                  # Clip:frame,frame,... single frames at full size
            cname, frames = name.split(":")
            cam = camera("FP1", eye)
            paths = []
            for f in frames.split("+"):
                show(CLIPS[cname], int(f)); paths.append(render(cam, os.path.join(SHOTS, f"{cname}_f{int(f):03d}.png")))
            sheet(paths, 2, os.path.join(SHOTS, f"{cname}_frames.png"))
        else:
            contact_sheet(CLIPS[name])
else:
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    sc.render.fps, sc.render.fps_base = FPS, 1.0           # the takes' rate travels in the FBX

    def bake(obj, clip, set_pose, path):
        """Key every frame of clip on obj's pose bones (set_pose(t) poses it), export obj's armature as an FBX take."""
        obj.animation_data_create(); obj.animation_data.action = bpy.data.actions.new(clip.name)
        prev = {}
        for f in range(clip.n + 1):
            set_pose(f)
            for pb in obj.pose.bones:
                if pb.rotation_mode != 'QUATERNION': pb.rotation_mode = 'QUATERNION'
                q = pb.rotation_quaternion.copy()
                if pb.name in prev and q.dot(prev[pb.name]) < 0: q.negate(); pb.rotation_quaternion = q
                prev[pb.name] = q
                for prop in ("location", "rotation_quaternion", "scale"): pb.keyframe_insert(prop, frame=f)
        sc.frame_start, sc.frame_end = 0, clip.n
        for o in bpy.data.objects: o.select_set(o == obj)
        with bpy.context.temp_override(**ctx()):
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE'},
                add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
                bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0)
        act = obj.animation_data.action; obj.animation_data.action = None; bpy.data.actions.remove(act)
        for pb in obj.pose.bones: pb.matrix_basis = Matrix.Identity(4)
        print("exported", os.path.basename(path), clip.n + 1, "frames")

    # the rifle: rest pose skinned mesh, then its takes (named "Armature" so Unreal drops the node, as for the arms)
    arm.name = "ArmsRig"; rig.name = "Armature"; rig.matrix_world = Matrix.Identity(4)
    rifle_mesh.data.color_attributes.remove(rifle_mesh.data.color_attributes["Col"])
    rifle_pose(rig, {})
    for o in bpy.data.objects: o.select_set(o in (rig, rifle_mesh))
    with bpy.context.temp_override(**ctx()):
        bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SK_RifleFP.fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'},
            add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False, bake_anim=False,
            mesh_smooth_type='FACE', path_mode='STRIP')
    for clip in CLIPS.values():
        bake(rig, clip, lambda f, c=clip: rifle_pose(rig, c.rifle_local(c.parts(f))), os.path.join(OUT, f"A_RifleFP_{clip.name}.fbx"))
    # the arms' takes
    rig.name = "RifleRig"; arm.name = "Armature"
    for clip in CLIPS.values():
        if clip.arms:
            bake(arm, clip, lambda f, c=clip: apply_pose(c.pose(f)[0]), os.path.join(OUT, f"A_FP_{clip.name}.fbx"))
    json.dump({name: {"frames": c.n, "fps": FPS} for name, c in CLIPS.items()}, open(os.path.join(OUT, "clips.json"), "w"), indent=1)
