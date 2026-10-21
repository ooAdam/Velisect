"""Writes player_cfg.json's tuning onto BP_Player's defaults (run in the open editor: node tools/unreal.mjs py tools/pipeline/ue_tune_player.py).
The viewmodel is framed from the reference: "frame" pins rifle mesh points to screen spots (fractions of the half-width
from the centre, right and down) at the viewmodel FOV; the rifle pose that lands them there gives the arms' offset."""
import json, math
import unreal

E = unreal.EditorAssetLibrary
M = unreal.MathLibrary
cfg = json.load(open(r"C:\Users\adanr\velisect\tools\pipeline\player_cfg.json"))
vm = cfg["viewmodel"]
grip = cfg["grip"]
grip_t = unreal.Transform(unreal.Vector(*grip["loc"]), unreal.Rotator(roll=grip["rot"][2], pitch=grip["rot"][0], yaw=grip["rot"][1]), unreal.Vector(1, 1, 1))

FORWARD = unreal.Transform(unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=90), unreal.Vector(1, 1, 1))

def rifle_in_camera(x, y, z, yaw, pitch):
    # the rifle's muzzle (mesh -Y) turned to the camera's forward (+X), then aimed (camera space, pitch up) and placed
    aim = unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=pitch, yaw=yaw), unreal.Vector(1, 1, 1))
    return M.compose_transforms(FORWARD, aim)

def solve(A, b):
    n = len(b)
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[p], b[i], b[p] = A[p], A[i], b[p], b[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            A[r] = [a - f * c for a, c in zip(A[r], A[i])]
            b[r] -= f * b[i]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(A[i][j] * x[j] for j in range(i + 1, n))) / A[i][i]
    return x

# For a given rifle angle, where each frame point lands is linear in the rifle's position: least squares gives the
# position and its screen error. The angle is searched over a grid (the reference barrel tips up and in towards the
# crosshair), keeping the rifle a believable distance in front of the eye.
tan_half = math.tan(math.radians(vm["fov"]) / 2)

def fit(yaw, pitch):
    turn = rifle_in_camera(0, 0, 0, yaw, pitch)
    rows, rhs = [], []
    for point, (u, v) in vm["frame"]:
        q = M.transform_location(turn, unreal.Vector(*point))
        u, v = u * tan_half, v * tan_half
        rows += [[-u, 1, 0], [-v, 0, -1]]
        rhs += [u * q.x - q.y, v * q.x + q.z]
    A = [[sum(r[i] * r[j] for r in rows) for j in range(3)] for i in range(3)]
    b = [sum(r[i] * h for r, h in zip(rows, rhs)) for i in range(3)]
    params = solve(A, b) + [yaw, pitch]
    error = 0.0
    for point, (u, v) in vm["frame"]:
        c = M.transform_location(rifle_in_camera(*params), unreal.Vector(*point))
        error += (c.y / c.x / tan_half - u) ** 2 + (-c.z / c.x / tan_half - v) ** 2
    return math.sqrt(error), params

(yaw_lo, yaw_hi), (pitch_lo, pitch_hi) = vm["aim_range"]
fits = [fit(yaw * 0.5, pitch * 0.5) for yaw in range(int(yaw_lo * 2), int(yaw_hi * 2) + 1) for pitch in range(int(pitch_lo * 2), int(pitch_hi * 2) + 1)]
error, params = min(f for f in fits if f[1][0] > vm["min_distance"])
for point, (u, v) in vm["frame"]:
    c = M.transform_location(rifle_in_camera(*params), unreal.Vector(*point))
    print("frame point", point, "lands", round(c.y / c.x / tan_half, 3), round(-c.z / c.x / tan_half, 3), "wanted", u, v)
print("rifle in camera (x, y, z, yaw, pitch):", [round(p, 2) for p in params], "error", round(error, 4))

# The arms' aim pose (the rifle clip's first frame) puts the rifle at grip * right hand; place the arms so it lands there.
arms = unreal.load_asset("/Game/Velisect/Characters/Player/SK_PlayerArms")
aim = unreal.load_asset("/Game/Velisect/Characters/Player/Animations/A_Player_FiringRifle")
options = unreal.AnimPoseEvaluationOptions()
options.set_editor_property("optional_skeletal_mesh", arms)
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(aim, 0.0, options)
right_hand = next(n for n in unreal.AnimPoseExtensions.get_bone_names(pose) if str(n).lower() == "righthand")
hand = unreal.AnimPoseExtensions.get_bone_pose(pose, right_hand, unreal.AnimPoseSpaces.WORLD)
rifle_in_arms = M.compose_transforms(grip_t, hand)
target = rifle_in_camera(*params)
offset = M.compose_transforms(M.invert_transform(rifle_in_arms), target)
check = M.compose_transforms(rifle_in_arms, offset)
print("viewmodel offset", offset.translation, offset.rotation.rotator(), "check", check.translation, target.translation)

bp = unreal.load_asset("/Game/Velisect/Blueprints/BP_Player")
cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
cdo.set_editor_property("body_offset", unreal.Vector(*cfg["body"]))
cdo.set_editor_property("camera_offset", unreal.Vector2D(*cfg["camera"]))
cdo.set_editor_property("eye_height", cfg["eye"])
cdo.set_editor_property("aim_yaw_offset", cfg["yaw"])
cdo.set_editor_property("aim_pitch_scale", cfg["pitch_scale"])
cdo.set_editor_property("aim_pitch_offset", cfg["pitch_offset"])
cdo.set_editor_property("weapon_grip_offset", grip_t)
cdo.set_editor_property("muzzle_offset", unreal.Vector(*cfg["muzzle"]))
cdo.set_editor_property("viewmodel_offset", offset)
cdo.set_editor_property("viewmodel_field_of_view", vm["fov"])
cdo.set_editor_property("viewmodel_scale", vm["scale"])
cdo.set_editor_property("left_hand_grip", unreal.Vector(*vm["left_grip"]))
cdo.set_editor_property("pistol_grip", unreal.Vector(*vm["pistol_grip"]))
cdo.set_editor_property("left_elbow_hint", unreal.Vector(*vm["left_elbow"]))
twist = vm["left_twist"]
cdo.set_editor_property("left_hand_twist", unreal.Rotator(roll=twist[2], pitch=twist[0], yaw=twist[1]))
cdo.set_editor_property("viewmodel_sprint_slide", unreal.Vector(*vm["sprint_slide"]))
turn = vm["sprint_turn"]
cdo.set_editor_property("viewmodel_sprint_turn", unreal.Rotator(roll=turn[2], pitch=turn[0], yaw=turn[1]))
cdo.set_editor_property("viewmodel_kick_back", vm["kick_back"])
cdo.set_editor_property("viewmodel_sway", vm["sway"])
cdo.set_editor_property("viewmodel_max_sway", vm["max_sway"])
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
E.save_loaded_asset(bp)
print("BP_Player tuned")
