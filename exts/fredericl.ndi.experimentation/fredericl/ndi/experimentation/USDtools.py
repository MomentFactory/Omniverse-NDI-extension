import omni.ext
from typing import List
from pxr import Usd, UsdShade, Sdf, UsdLux
from dataclasses import dataclass
import carb
import numpy as np


@dataclass
class DynamicPrim:
    path: str
    name: str
    ndi: str


class USDtools():
    ATTR_NAME = 'ndi:source'
    PREFIX = "dynamic://"

    def create_dynamic_material(name: str) -> UsdShade.Material:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        material_path = f"/Looks/{name}/Material"
        material: UsdShade.Material = UsdShade.Material.Define(stage, material_path)
        shader: UsdShade.Shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.SetSourceAsset("OmniPBR.mdl", "mdl")
        shader.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        shader.CreateIdAttr("OmniPBR")
        shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset).Set(f"{USDtools.PREFIX}{name}")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

        magenta = np.array([255, 0, 255, 255], np.uint8)
        frame = np.full((1, 1, 4), magenta, dtype=np.uint8)
        dynamic_texture = omni.ui.DynamicTextureProvider(name)
        dynamic_texture.set_bytes_data(frame.flatten().tolist(), [1, 1], omni.ui.TextureFormat.RGBA8_UNORM)

        return material

    def find_all_dynamic_sources() -> List[DynamicPrim]:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()
        if stage is None:  # Sometimes stage isn't loaded when the frame draws
            return []

        shaders: List[UsdShade.Shader] = [UsdShade.Shader(x) for x in stage.Traverse() if x.IsA(UsdShade.Shader)]
        dynamic_shaders: List[str] = []
        result: List[DynamicPrim] = []
        for shader in shaders:
            texture_input = shader.GetInput("diffuse_texture")
            texture_value = texture_input.Get()
            if texture_value:
                path: str = texture_value.path
                length: int = len(USDtools.PREFIX)
                if len(path) > length:
                    candidate = path[:length]
                    if candidate == USDtools.PREFIX:
                        name = path[length:]
                        if name not in dynamic_shaders:
                            dynamic_shaders.append(name)
                            attr = shader.GetPrim().GetAttribute(USDtools.ATTR_NAME)
                            attr = attr.Get() if attr.IsValid() else None
                            p = DynamicPrim(shader.GetPath().pathString, name, attr)
                            result.append(p)

        rect_lights: List[UsdLux.Rectlight] = [UsdLux.RectLight(x) for x in stage.Traverse() if x.IsA(UsdLux.RectLight)]
        for rect_light in rect_lights:
            # TODO: Filter those that have "isProjector" (the attribute doesn't exist)
            attribute = rect_light.GetPrim().GetAttribute("texture:file").Get()
            if attribute:
                path: str = attribute.path
                if len(path) > length:
                    candidate = path[:length]
                    if candidate == USDtools.PREFIX:
                        name = path[length:]
                        if name not in dynamic_shaders:
                            dynamic_shaders.append(name)
                            attr = rect_light.GetPrim().GetAttribute(USDtools.ATTR_NAME)
                            attr = attr.Get() if attr.IsValid() else None
                            p = DynamicPrim(rect_light.GetPath().pathString, name, attr)
                            result.append(p)

        return result

    def set_prim_ndi_attribute(path: str, value: str):
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        prim: Usd.Prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            carb.log_error(f"Could not set the ndi attribute of prim at {path}")
            return

        prim.CreateAttribute(USDtools.ATTR_NAME, Sdf.ValueTypeNames.String).Set(value)
