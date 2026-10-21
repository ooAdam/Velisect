exec(open(r"C:\Users\adanr\OneDrive\Documents\Unreal Projects\Velisect\tools\pipeline\common_bl.py").read())
import mathutils, re
OUT = r"C:\Users\adanr\OneDrive\Documents\Unreal Projects\Velisect\SourceArt"
S = mathutils.Matrix.Diagonal((-1, 1, 1, 1))  # mirror across armature-space X (the character's left/right axis)

def partner(name):
    if "Left" in name: return name.replace("Left", "Right")
    if "Right" in name: return name.replace("Right", "Left")
    return name

def camel(n):
    n = re.sub(r"\(\d+\)", lambda m: m.group(0)[1:-1], n)
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[^A-Za-z0-9]+", n) if w)

def get_arm():
    return [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

def resample(arm, transform):
    """Sample every frame's armature-space bone matrices, let transform() edit them, then rebake the action."""
    act = arm.animation_data.action
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    sc = bpy.context.scene
    frames = list(range(f0, f1 + 1))
    data = []
    for f in frames:
        sc.frame_set(f)
        data.append({pb.name: pb.matrix.copy() for pb in arm.pose.bones})
    new = bpy.data.actions.new(act.name + "_rs")
    arm.animation_data.action = new
    n = len(frames)
    for i, f in enumerate(frames):
        mats = transform(i / max(n - 1, 1), data[i], data)
        for pb in arm.pose.bones:
            M, R = mats[pb.name], pb.bone.matrix_local
            if pb.parent:
                basis = R.inverted() @ pb.parent.bone.matrix_local @ mats[pb.parent.name].inverted() @ M
            else:
                basis = R.inverted() @ M
            pb.matrix_basis = basis
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=f)
            pb.keyframe_insert("scale", frame=f)
    bpy.data.actions.remove(act)
    sc.frame_start, sc.frame_end = f0, f1

def strip_drift(arm):
    root = arm.pose.bones[0].name
    def fn(t, mats, all_frames):
        start = all_frames[0][root].translation
        end = all_frames[-1][root].translation
        out = dict(mats)
        M = mats[root].copy()
        # armature space: X = lateral, Z = forward/back (Y is up); remove the linear ground-plane travel
        M.translation.x -= (end.x - start.x) * t
        M.translation.z -= (end.z - start.z) * t
        out[root] = M
        return out
    resample(arm, fn)

def mirror(arm):
    rest = {pb.name: pb.bone.matrix_local for pb in arm.pose.bones}
    def fn(t, mats, all_frames):
        out = {}
        for name in mats:
            src = partner(name) if partner(name) in mats else name
            delta = mats[src] @ rest[src].inverted()       # motion relative to rest, armature space
            out[name] = (S @ delta @ S) @ rest[name]       # mirrored motion applied to this bone's rest
        return out
    resample(arm, fn)

def export(path, with_mesh, bake):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o.type == 'ARMATURE' or (with_mesh and o.type == 'MESH'))
    with bpy.context.temp_override(**ctx()):
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
            object_types={'ARMATURE', 'MESH'} if with_mesh else {'ARMATURE'},
            add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
            bake_anim=bake, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
            bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
            mesh_smooth_type='FACE', path_mode='COPY', embed_textures=with_mesh)

def export_mesh(src, dst, texdir):
    clear(); fbx_import(src)
    os.makedirs(texdir, exist_ok=True)
    for img in bpy.data.images:
        if img.packed_file:
            name = os.path.basename(img.filepath.replace("\\", "/"))
            img.filepath_raw = os.path.join(texdir, name)
            img.save()
    arm = get_arm()
    if arm.animation_data: arm.animation_data.action = None
    for pb in arm.pose.bones: pb.matrix_basis = mathutils.Matrix.Identity(4)
    export(dst, True, False)

KEEP_DRIFT = ("dying", "death", "hit reaction")
MIRRORS = {"Strafing": "StrafeRight", "Sprint Forward Right": "SprintForwardLeft",
           "Run Backward Right": "RunBackwardLeft", "Walk Crouching Right": "WalkCrouchingLeft"}
RENAME = {"Strafing": "StrafeLeft"}

def export_anims(folder, prefix, outdir, skip):
    done = []
    for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.fbx"))):
        stem = os.path.splitext(os.path.basename(p))[0]
        if stem.startswith(skip) or stem.startswith("T-Pose"): continue
        variants = [(RENAME.get(stem, camel(stem)), False)]
        if stem in MIRRORS: variants.append((MIRRORS[stem], True))
        for name, do_mirror in variants:
            clear(); fbx_import(p)
            arm = get_arm()
            if not arm.animation_data or not arm.animation_data.action: continue
            if not any(k in stem.lower() for k in KEEP_DRIFT): strip_drift(arm)
            if do_mirror: mirror(arm)
            for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
            export(os.path.join(outdir, f"{prefix}{name}.fbx"), False, True)
            done.append(name)
    return done

import glob
res = {}
export_mesh(os.path.join(ROOT, "UserCharacter", "Ch35_nonPBR.fbx"), os.path.join(OUT, "Player", "SK_Player.fbx"), os.path.join(OUT, "Player", "Textures"))
export_mesh(os.path.join(ROOT, "Enemy#1", "Mremireh O Desbiens.fbx"), os.path.join(OUT, "Zombie", "SK_Zombie.fbx"), os.path.join(OUT, "Zombie", "Textures"))
res["player"] = export_anims("UserCharacter", "A_Player_", os.path.join(OUT, "Player", "Animations"), ("Ch35",))
res["zombie"] = export_anims("Enemy#1", "A_Zombie_", os.path.join(OUT, "Zombie", "Animations"), ("Ch10", "Mremireh"))
print(json.dumps(res))
