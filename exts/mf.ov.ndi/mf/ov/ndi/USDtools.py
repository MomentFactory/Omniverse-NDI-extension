import omni.ext
from typing import List
from pxr import Usd, UsdGeom, UsdShade, Sdf, UsdLux, Tf
from dataclasses import dataclass
import logging
import numpy as np
from unidecode import unidecode


@dataclass
class DynamicPrim:
    path: str
    name: str
    ndi: str
    low: bool


class USDtools():
    ATTR_NDI_NAME = 'ndi:source'
    ATTR_BANDWIDTH_NAME = "ndi:lowbandwidth"
    PREFIX = "dynamic://"

    def create_dynamic_material(name: str) -> UsdShade.Material:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        scope_path: str = f"{stage.GetDefaultPrim().GetPath()}/Looks"
        UsdGeom.Scope.Define(stage, scope_path)

        safename = Tf.MakeValidIdentifier(unidecode(name))
        if name != safename:
            logger = logging.getLogger(__name__)
            logger.warn(f"Name \"{name}\" was not a valid USD identifier, changed it to \"{safename}\"")

        material_path = f"{scope_path}/{safename}"
        material: UsdShade.Material = UsdShade.Material.Define(stage, material_path)
        shader: UsdShade.Shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.SetSourceAsset("OmniPBR.mdl", "mdl")
        shader.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        shader.CreateIdAttr("OmniPBR")
        shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset).Set(f"{USDtools.PREFIX}{safename}")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

        magenta = np.array([255, 0, 255, 255], np.uint8)
        frame = np.full((1, 1, 4), magenta, dtype=np.uint8)
        height, width, channels = frame.shape
        dynamic_texture = omni.ui.DynamicTextureProvider(safename)
        dynamic_texture.set_data_array(frame, [width, height, channels])
        # dynamic_texture.set_bytes_data(frame.flatten().tolist(), [1, 1], omni.ui.TextureFormat.RGBA8_UNORM)

        return material

    def find_all_dynamic_sources() -> List[DynamicPrim]:
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()
        if stage is None:  # Sometimes stage isn't loaded when the frame draws
            return []

        shaders: List[UsdShade.Shader] = [UsdShade.Shader(x) for x in stage.Traverse() if x.IsA(UsdShade.Shader)]
        dynamic_shaders: List[str] = []
        result: List[DynamicPrim] = []

        length: int = len(USDtools.PREFIX)
        for shader in shaders:
            texture_input = shader.GetInput("diffuse_texture")
            texture_value = texture_input.Get()
            if texture_value:
                path: str = texture_value.path
                if len(path) > length:
                    candidate = path[:length]
                    if candidate == USDtools.PREFIX:
                        name = path[length:]
                        if name not in dynamic_shaders:
                            dynamic_shaders.append(name)
                            attr_ndi = shader.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
                            attr_ndi = attr_ndi.Get() if attr_ndi.IsValid() else None
                            attr_low = shader.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
                            attr_low = attr_low.Get() if attr_low.IsValid() else False
                            p = DynamicPrim(shader.GetPath().pathString, name, attr_ndi, attr_low)
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
                            attr_ndi = shader.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
                            attr_ndi = attr_ndi.Get() if attr_ndi.IsValid() else None
                            attr_low = shader.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
                            attr_low = attr_low.Get() if attr_low.IsValid() else False
                            p = DynamicPrim(rect_light.GetPath().pathString, name, attr_ndi, attr_low)
                            result.append(p)

        return result

    def set_prim_ndi_attribute(path: str, value: str):
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        prim: Usd.Prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            logger = logging.getLogger(__name__)
            logger.error(f"Could not set the ndi attribute of prim at {path}")
            return

        prim.CreateAttribute(USDtools.ATTR_NDI_NAME, Sdf.ValueTypeNames.String).Set(value)

    def set_prim_bandwidth_attribute(path: str, value: bool):
        usd_context = omni.usd.get_context()
        stage: Usd.Stage = usd_context.get_stage()

        prim: Usd.Prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            logger = logging.getLogger(__name__)
            logger.error(f"Could not set the bandwidth attribute of prim at {path}")

        prim.CreateAttribute(USDtools.ATTR_BANDWIDTH_NAME, Sdf.ValueTypeNames.Bool).Set(value)
