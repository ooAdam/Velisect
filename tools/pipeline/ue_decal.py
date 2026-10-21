import unreal
E = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
path = "/Game/Velisect/Materials/M_BulletHole"
if E.does_asset_exist(path):
    E.delete_asset(path)
m = tools.create_asset("M_BulletHole", "/Game/Velisect/Materials", unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
def e(cls, x, y, **kw):
    n = MEL.create_material_expression(m, cls, x, y)
    for k, v in kw.items(): n.set_editor_property(k, v)
    return n
uv = e(unreal.MaterialExpressionTextureCoordinate, -900, 0)
center = e(unreal.MaterialExpressionConstant2Vector, -900, 120, r=0.5, g=0.5)
dist = e(unreal.MaterialExpressionDistance, -700, 40)
MEL.connect_material_expressions(uv, "", dist, "A"); MEL.connect_material_expressions(center, "", dist, "B")
edge = e(unreal.MaterialExpressionSubtract, -550, 40)
MEL.connect_material_expressions(e(unreal.MaterialExpressionConstant, -700, 160, r=0.5), "", edge, "A"); MEL.connect_material_expressions(dist, "", edge, "B")
sharp = e(unreal.MaterialExpressionMultiply, -400, 40)
MEL.connect_material_expressions(edge, "", sharp, "A"); MEL.connect_material_expressions(e(unreal.MaterialExpressionConstant, -550, 160, r=6.0), "", sharp, "B")
sat = e(unreal.MaterialExpressionSaturate, -250, 40); MEL.connect_material_expressions(sharp, "", sat, "")
MEL.connect_material_property(sat, "", unreal.MaterialProperty.MP_OPACITY)
MEL.connect_material_property(e(unreal.MaterialExpressionConstant3Vector, -250, -120, constant=unreal.LinearColor(0.025, 0.02, 0.015, 1)), "", unreal.MaterialProperty.MP_BASE_COLOR)
MEL.connect_material_property(e(unreal.MaterialExpressionConstant, -250, 180, r=0.75), "", unreal.MaterialProperty.MP_ROUGHNESS)
MEL.recompile_material(m); E.save_loaded_asset(m)
print("decal ok")
