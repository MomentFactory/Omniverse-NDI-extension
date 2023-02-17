import omni.ext
import carb
from pxr import Usd, UsdGeom, UsdShade, Sdf


class USDtools():
    def on_click_create(name: str, parent_name: str, width: float, height: float):
        texture_name = name
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        if parent_name == "":
            parent_prim = stage.GetDefaultPrim()
        else:
            parent_prims = [x for x in stage.Traverse() if x.GetName() == parent_name]
            if len(parent_prims) == 0:
                carb.log_error(f"Error finding parent prim with name:\"{parent_name}\"")
            parent_prim = parent_prims[0]
        parent_path = parent_prim.GetPath()
        prim_path = f"{parent_path}/{name}"

        hw = width / 2
        hh = height / 2

        billboard: UsdGeom.Mesh = UsdGeom.Mesh.Define(stage, f"{prim_path}/Mesh")
        billboard.CreatePointsAttr([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)])
        billboard.CreateFaceVertexCountsAttr([4])
        billboard.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
        billboard.CreateExtentAttr([(-430, -145, 0), (430, 145, 0)])
        texCoords = UsdGeom.PrimvarsAPI(billboard).CreatePrimvar("st",
                                                                 Sdf.ValueTypeNames.TexCoord2fArray,
                                                                 UsdGeom.Tokens.varying)
        texCoords.Set([(0, 0), (1, 0), (1, 1), (0, 1)])

        material_path = f"{prim_path}/Material"
        material: UsdShade.Material = UsdShade.Material.Define(stage, material_path)
        shader: UsdShade.Shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.SetSourceAsset("OmniPBR.mdl", "mdl")
        shader.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        shader.CreateIdAttr("OmniPBR")
        shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset).Set(f"dynamic://{texture_name}")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        billboard.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
        UsdShade.MaterialBindingAPI(billboard).Bind(material)
