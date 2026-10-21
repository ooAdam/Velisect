import unreal
E = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
MAT = "/Game/Velisect/Materials"
WHITE = unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
FLAT = unreal.load_asset("/Engine/EngineMaterials/DefaultNormal")
# a linear (non-sRGB) default for Masks samplers: the cooker rejects WhiteSquareTexture there (M2)
MASK_DEFAULT = "/Game/Velisect/Weapons/Rifle/Textures/T_Rifle_Body_Mixed_AO"
BR_TEX = "/Game/Velisect/Environment/Backrooms/Textures/"


def fresh(name, path, cls, factory):
    full = f"{path}/{name}"
    if E.does_asset_exist(full):
        E.delete_asset(full)
    return tools.create_asset(name, path, cls, factory)


def tex_settings():
    for p in E.list_assets("/Game/Velisect/Environment/Backrooms/Textures") + E.list_assets("/Game/Velisect/Weapons/Rifle/Textures"):
        t = unreal.load_asset(p)
        n = t.get_name()
        if n.endswith("_N") or "Normal" in n:
            t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            t.set_editor_property("srgb", False)
            if "OpenGL" in n:
                t.set_editor_property("flip_green_channel", True)
        elif any(k in n for k in ("_R", "Roughness", "Metallic", "AO", "Mask", "Specular", "Opacity")) and not n.endswith("_D"):
            t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            t.set_editor_property("srgb", False)
        E.save_loaded_asset(t)


class G:
    """Tiny helper for building material graphs."""

    def __init__(self, m):
        self.m = m

    def e(self, cls, x, y, **props):
        n = MEL.create_material_expression(self.m, cls, x, y)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def c(self, a, ao, b, bi):
        MEL.connect_material_expressions(a, ao, b, bi)

    def out(self, a, ao, prop):
        MEL.connect_material_property(a, ao, prop)

    def scalar(self, name, val, x, y):
        return self.e(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=val)

    def vec(self, name, val, x, y):
        return self.e(unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name, default_value=val)

    def tex(self, name, tex, x, y, normal=False):
        return self.e(unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name, texture=tex,
                      sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)

    def op(self, cls, a, ao, b, bo, x, y):
        n = self.e(cls, x, y)
        self.c(a, ao, n, "A")
        self.c(b, bo, n, "B")
        return n


def build_surface():
    """Backrooms master: tiled albedo/normal, world-space water stains, grime near the floor, optional emissive."""
    m = fresh("M_BR_Surface", MAT, unreal.Material, unreal.MaterialFactoryNew())
    g = G(m)
    uv = g.op(unreal.MaterialExpressionMultiply, g.e(unreal.MaterialExpressionTextureCoordinate, -1600, 0), "", g.scalar("UVScale", 1.0, -1600, 120), "", -1400, 40)
    bc = g.tex("BaseColorTex", WHITE, -1150, -200)
    g.c(uv, "", bc, "UVs")
    nm = g.tex("NormalTex", FLAT, -1150, 300, normal=True)
    g.c(uv, "", nm, "UVs")
    tinted = g.op(unreal.MaterialExpressionMultiply, bc, "RGB", g.vec("Tint", unreal.LinearColor(1, 1, 1, 1), -1150, -420), "", -850, -250)

    wp = g.e(unreal.MaterialExpressionWorldPosition, -1600, 600)
    wxy = g.e(unreal.MaterialExpressionComponentMask, -1400, 600, r=True, g=True, b=False, a=False)
    g.c(wp, "", wxy, "")
    suv = g.op(unreal.MaterialExpressionMultiply, wxy, "", g.e(unreal.MaterialExpressionConstant, -1400, 720, r=1.0 / 650.0), "", -1250, 620)
    stain = g.e(unreal.MaterialExpressionTextureSample, -1100, 600, texture=unreal.load_asset(BR_TEX + "T_BR_StainMask"),
                sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    g.c(suv, "", stain, "UVs")
    stain_f = g.op(unreal.MaterialExpressionMultiply, stain, "R", g.scalar("StainStrength", 0.5, -1100, 800), "", -850, 620)

    wz = g.e(unreal.MaterialExpressionComponentMask, -1400, 950, r=False, g=False, b=True, a=False)
    g.c(wp, "", wz, "")
    zh = g.op(unreal.MaterialExpressionDivide, wz, "", g.scalar("GrimeHeight", 45.0, -1400, 1060), "", -1200, 960)
    om = g.e(unreal.MaterialExpressionOneMinus, -1050, 960)
    g.c(zh, "", om, "")
    sat = g.e(unreal.MaterialExpressionSaturate, -920, 960)
    g.c(om, "", sat, "")
    grime = g.op(unreal.MaterialExpressionMultiply, sat, "", g.scalar("GrimeStrength", 0.0, -920, 1080), "", -760, 980)

    dirt = g.op(unreal.MaterialExpressionAdd, stain_f, "", grime, "", -650, 700)
    dirt_s = g.e(unreal.MaterialExpressionSaturate, -520, 700)
    g.c(dirt, "", dirt_s, "")
    dirty = g.op(unreal.MaterialExpressionMultiply, tinted, "", g.vec("DirtTint", unreal.LinearColor(0.42, 0.36, 0.2, 1), -850, -60), "", -600, -100)
    lerp = g.e(unreal.MaterialExpressionLinearInterpolate, -400, -200)
    g.c(tinted, "", lerp, "A")
    g.c(dirty, "", lerp, "B")
    g.c(dirt_s, "", lerp, "Alpha")
    g.out(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    g.out(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)

    rough = g.scalar("Roughness", 0.85, -650, 300)
    wet = g.op(unreal.MaterialExpressionMultiply, rough, "", g.e(unreal.MaterialExpressionConstant, -650, 420, r=0.55), "", -500, 380)
    rl = g.e(unreal.MaterialExpressionLinearInterpolate, -350, 320)
    g.c(rough, "", rl, "A")
    g.c(wet, "", rl, "B")
    g.c(stain_f, "", rl, "Alpha")
    g.out(rl, "", unreal.MaterialProperty.MP_ROUGHNESS)
    g.out(g.scalar("Metallic", 0.0, -350, 480), "", unreal.MaterialProperty.MP_METALLIC)
    em = g.op(unreal.MaterialExpressionMultiply, g.vec("EmissiveColor", unreal.LinearColor(0, 0, 0, 1), -650, 560), "", g.scalar("EmissiveStrength", 0.0, -650, 700), "", -350, 600)
    g.out(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    E.save_loaded_asset(m)
    return m


def build_pbr():
    """Packed PBR master for the rifle texture sets."""
    m = fresh("M_PBR", MAT, unreal.Material, unreal.MaterialFactoryNew())
    g = G(m)
    bc = g.tex("BaseColorTex", WHITE, -900, -300)
    tint = g.op(unreal.MaterialExpressionMultiply, bc, "RGB", g.vec("Tint", unreal.LinearColor(1, 1, 1, 1), -900, -480), "", -500, -300)
    g.out(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    g.out(g.tex("NormalTex", FLAT, -900, 0, normal=True), "RGB", unreal.MaterialProperty.MP_NORMAL)
    met_tex = g.tex("MetallicTex", unreal.load_asset(MASK_DEFAULT), -900, 260)
    met_tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    met = g.op(unreal.MaterialExpressionMultiply, met_tex, "R", g.scalar("MetallicScale", 1.0, -900, 440), "", -500, 260)
    g.out(met, "", unreal.MaterialProperty.MP_METALLIC)
    rough_tex = g.tex("RoughnessTex", unreal.load_asset(MASK_DEFAULT), -900, 560)
    rough_tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    rough = g.op(unreal.MaterialExpressionMultiply, rough_tex, "R", g.scalar("RoughnessScale", 1.0, -900, 740), "", -500, 560)
    g.out(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    ao_tex = g.tex("AOTex", unreal.load_asset(MASK_DEFAULT), -900, 860)
    ao_tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    g.out(ao_tex, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(m)
    E.save_loaded_asset(m)
    return m


def mi(name, parent, path, scalars=None, vectors=None, textures=None):
    inst = fresh(name, path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(inst, k, v)
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(inst, k, unreal.LinearColor(*v))
    for k, v in (textures or {}).items():
        MEL.set_material_instance_texture_parameter_value(inst, k, unreal.load_asset(v))
    E.save_loaded_asset(inst)
    return inst


tex_settings()
surface = build_surface()
pbr = build_pbr()
BRM = "/Game/Velisect/Environment/Backrooms/Materials"
mats = {
    "MI_BR_Wallpaper": mi("MI_BR_Wallpaper", surface, BRM, {"Roughness": 0.8, "StainStrength": 0.45, "GrimeStrength": 0.55, "GrimeHeight": 70.0},
                          textures={"BaseColorTex": BR_TEX + "T_BR_Wallpaper_D", "NormalTex": BR_TEX + "T_BR_Wallpaper_N"}),
    "MI_BR_Baseboard": mi("MI_BR_Baseboard", surface, BRM, {"Roughness": 0.55, "StainStrength": 0.2}, {"Tint": (0.55, 0.48, 0.26, 1)}),
    "MI_BR_Carpet": mi("MI_BR_Carpet", surface, BRM, {"Roughness": 0.95, "StainStrength": 0.65},
                       textures={"BaseColorTex": BR_TEX + "T_BR_Carpet_D", "NormalTex": BR_TEX + "T_BR_Carpet_N"}),
    "MI_BR_Ceiling": mi("MI_BR_Ceiling", surface, BRM, {"Roughness": 0.9, "StainStrength": 0.35},
                        textures={"BaseColorTex": BR_TEX + "T_BR_Ceiling_D", "NormalTex": BR_TEX + "T_BR_Ceiling_N"}),
    "MI_BR_PanelFrame": mi("MI_BR_PanelFrame", surface, BRM, {"Roughness": 0.5, "StainStrength": 0.0}, {"Tint": (0.75, 0.74, 0.68, 1)}),
    "MI_BR_PanelLight": mi("MI_BR_PanelLight", surface, BRM, {"Roughness": 0.4, "StainStrength": 0.0, "EmissiveStrength": 30.0},
                           {"Tint": (1, 1, 1, 1), "EmissiveColor": (1.0, 0.95, 0.78, 1)}),
}
MESH = "/Game/Velisect/Environment/Backrooms/Meshes/"
for mesh_name in ["SM_BR_Wall_400", "SM_BR_Wall_200", "SM_BR_Pillar", "SM_BR_Floor_800", "SM_BR_Ceiling_800", "SM_BR_LightPanel"]:
    sm = unreal.load_asset(MESH + mesh_name)
    for i, s in enumerate(sm.static_materials):
        slot = str(s.material_slot_name)
        if slot in mats:
            sm.set_material(i, mats[slot])
    E.save_loaded_asset(sm)

RT = "/Game/Velisect/Weapons/Rifle/Textures/T_Rifle_"


def rifle_mi(part, prefix, extra=None):
    return mi(f"MI_Rifle_{part}", pbr, "/Game/Velisect/Weapons/Rifle", extra, None, {
        "BaseColorTex": RT + prefix + "_Base_Color", "NormalTex": RT + prefix + "_Normal_OpenGL",
        "MetallicTex": RT + prefix + "_Metallic", "RoughnessTex": RT + prefix + "_Roughness", "AOTex": RT + prefix + "_Mixed_AO"})


rifle_mats = {"blinn2": rifle_mi("Body", "Body"), "blinn3": rifle_mi("Stock", "Stock"),
              "blinn4": rifle_mi("ScopeGlass", "Scope_Glass", {"RoughnessScale": 0.2}), "blinn5": rifle_mi("Bullets", "Bullet")}
rifle = unreal.load_asset("/Game/Velisect/Weapons/Rifle/SM_Rifle")
for i, s in enumerate(rifle.static_materials):
    if str(s.material_slot_name) in rifle_mats:
        rifle.set_material(i, rifle_mats[str(s.material_slot_name)])
E.save_loaded_asset(rifle)

sme = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
for p in ["/Game/Velisect/Characters/Player/SK_Player", "/Game/Velisect/Characters/Zombie/SK_Zombie"]:
    sk = unreal.load_asset(p)
    pa = sme.create_physics_asset(sk, True, 0)
    print(p, "->", pa.get_path_name() if pa else None)
    E.save_loaded_asset(sk)
    if pa:
        E.save_loaded_asset(pa)
print("materials done")
