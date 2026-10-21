"""M2 fix: M_PBR's Masks samplers default to a linear mask texture so the material cooks (WhiteSquareTexture is sRGB)."""
import unreal

MEL = unreal.MaterialEditingLibrary
m = unreal.load_asset("/Game/Velisect/Materials/M_PBR")
mask = unreal.load_asset("/Game/Velisect/Weapons/Rifle/Textures/T_Rifle_Body_Mixed_AO")


def texture_nodes(node):
    """The texture parameter nodes feeding node (itself, or one level up through a multiply)."""
    if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D):
        return [node]
    return [n for n in MEL.get_inputs_for_material_expression(m, node) if isinstance(n, unreal.MaterialExpressionTextureSampleParameter2D)]


fixed = []
for prop in (unreal.MaterialProperty.MP_METALLIC, unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION):
    for node in texture_nodes(MEL.get_material_property_input_node(m, prop)):
        node.set_editor_property("texture", mask)
        fixed.append(str(node.get_editor_property("parameter_name")))
MEL.recompile_material(m)
unreal.EditorAssetLibrary.save_loaded_asset(m)
print("M_PBR mask defaults fixed:", fixed)
