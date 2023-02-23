import omni.ext
from typing import List
from pxr import Usd, UsdShade, Sdf


class USDtools():
    def create_dynamic_material(name: str) -> UsdShade.Material:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        material_path = f"/Looks/{name}/Material"
        material: UsdShade.Material = UsdShade.Material.Define(stage, material_path)
        shader: UsdShade.Shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.SetSourceAsset("OmniPBR.mdl", "mdl")
        shader.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        shader.CreateIdAttr("OmniPBR")
        shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset).Set(f"dynamic://{name}")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        return material

    def find_all_dynamic_materials() -> List[str]:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()
        if stage is None:  # Sometimes stage isn't loaded when the frame draws
            return

        shaders: List[UsdShade.Shader] = [UsdShade.Shader(x) for x in stage.Traverse() if x.IsA(UsdShade.Shader)]
        dynamic_shaders: List[str] = []
        for shader in shaders:
            path: str = shader.GetInput("diffuse_texture").Get().path
            compare: str = "dynamic://"
            length: int = len(compare)
            if len(path) > length:
                candidate = path[:length]
                if candidate == compare:
                    name = path[length:]
                    if name not in dynamic_shaders:
                        dynamic_shaders.append(name)

        return dynamic_shaders
