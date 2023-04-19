from .bindings import DynamicPrim

import logging
import numpy as np
import omni.ext

from pxr import Usd, UsdGeom, UsdShade, Sdf, UsdLux, Tf
from typing import List
from unidecode import unidecode


class USDtools():
    ATTR_NDI_NAME = 'ndi:source'
    ATTR_BANDWIDTH_NAME = "ndi:lowbandwidth"
    PREFIX = "dynamic://"
    SCOPE_NAME = "NDI_Looks"

    def get_stage() -> Usd.Stage:
        usd_context = omni.usd.get_context()
        return usd_context.get_stage()

    def make_name_valid(name: str) -> str:
        return Tf.MakeValidIdentifier(unidecode(name))

    def create_dynamic_material(name: str):
        stage = USDtools.get_stage()
        if not stage:
            logger = logging.getLogger(__name__)
            logger.error("Could not get stage")
            return

        scope_path: str = f"{stage.GetDefaultPrim().GetPath()}/{USDtools.SCOPE_NAME}"
        UsdGeom.Scope.Define(stage, scope_path)

        safename = USDtools.make_name_valid(name)
        if name != safename:
            logger = logging.getLogger(__name__)
            logger.warn(f"Name \"{name}\" was not a valid USD identifier, changed it to \"{safename}\"")

        USDtools._create_material_and_shader(stage, scope_path, safename)
        USDtools._fill_dynamic_with_magenta(safename)

    def _create_material_and_shader(stage: Usd.Stage, scope_path: str, safename: str):
        material_path = f"{scope_path}/{safename}"
        material: UsdShade.Material = UsdShade.Material.Define(stage, material_path)
        shader: UsdShade.Shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.SetSourceAsset("OmniPBR.mdl", "mdl")
        shader.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        shader.CreateIdAttr("OmniPBR")
        shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset).Set(f"{USDtools.PREFIX}{safename}")
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    def _fill_dynamic_with_magenta(safename: str):
        magenta = np.array([255, 0, 255, 255], np.uint8)
        frame = np.full((1, 1, 4), magenta, dtype=np.uint8)
        height, width, channels = frame.shape
        dynamic_texture = omni.ui.DynamicTextureProvider(safename)
        dynamic_texture.set_data_array(frame, [width, height, channels])

    def find_all_dynamic_sources() -> List[DynamicPrim]:
        stage = USDtools.get_stage()
        if not stage:
            logger = logging.getLogger(__name__)
            logger.warning("Could not get stage")
            return []

        dynamic_sources: List[str] = []
        dynamic_shaders, dynamic_sources = USDtools._find_all_dynamic_shaders(stage, dynamic_sources)
        dynamic_lights, _ = USDtools._find_all_dynamic_lights(stage, dynamic_sources)
        return dynamic_shaders + dynamic_lights

    def _find_all_dynamic_shaders(stage: Usd.Stage, sources: List[str]):
        shaders: List[UsdShade.Shader] = [UsdShade.Shader(x) for x in stage.Traverse() if x.IsA(UsdShade.Shader)]
        result: List[DynamicPrim] = []

        prefix_length: int = len(USDtools.PREFIX)
        for shader in shaders:
            texture_input = shader.GetInput("diffuse_texture")
            texture_value = texture_input.Get()
            if texture_value:
                path: str = texture_value.path
                if len(path) > prefix_length:
                    candidate = path[:prefix_length]
                    if candidate == USDtools.PREFIX:
                        name = path[prefix_length:]
                        if name not in sources:
                            sources.append(name)
                            attr_ndi = shader.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
                            attr_ndi = attr_ndi.Get() if attr_ndi.IsValid() else None
                            attr_low = shader.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
                            attr_low = attr_low.Get() if attr_low.IsValid() else False
                            p = DynamicPrim(shader.GetPath().pathString, name, attr_ndi, attr_low)
                            result.append(p)

        return result, sources

    def _find_all_dynamic_lights(stage: Usd.Stage, sources: List[str]):
        rect_lights: List[UsdLux.Rectlight] = [UsdLux.RectLight(x) for x in stage.Traverse() if x.IsA(UsdLux.RectLight)]
        result: List[DynamicPrim] = []

        prefix_length: int = len(USDtools.PREFIX)
        for rect_light in rect_lights:
            # TODO: Filter those that have "isProjector" (the attribute doesn't exist)
            attribute = rect_light.GetPrim().GetAttribute("texture:file").Get()
            if attribute:
                path: str = attribute.path
                if len(path) > prefix_length:
                    candidate = path[:prefix_length]
                    if candidate == USDtools.PREFIX:
                        name = path[prefix_length:]
                        if name not in sources:
                            attr_ndi = rect_light.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
                            attr_ndi = attr_ndi.Get() if attr_ndi.IsValid() else None
                            attr_low = rect_light.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
                            attr_low = attr_low.Get() if attr_low.IsValid() else False
                            p = DynamicPrim(rect_light.GetPath().pathString, name, attr_ndi, attr_low)
                            result.append(p)

        return result, sources

    def set_prim_ndi_attribute(path: str, value: str):
        stage = USDtools.get_stage()
        if not stage:
            logger = logging.getLogger(__name__)
            logger.error("Could not get stage")
            return

        prim: Usd.Prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            logger = logging.getLogger(__name__)
            logger.error(f"Could not set the ndi attribute of prim at {path}")
            return

        prim.CreateAttribute(USDtools.ATTR_NDI_NAME, Sdf.ValueTypeNames.String).Set(value)

    def set_prim_lowbandwidth_attribute(path: str, value: bool):
        stage = USDtools.get_stage()
        if not stage:
            logger = logging.getLogger(__name__)
            logger.error("Could not get stage")
            return

        prim: Usd.Prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            logger = logging.getLogger(__name__)
            logger.error(f"Could not set the bandwidth attribute of prim at {path}")

        prim.CreateAttribute(USDtools.ATTR_BANDWIDTH_NAME, Sdf.ValueTypeNames.Bool).Set(value)

# region stage events
    def subscribe_to_stage_events(callback):
        return (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop(callback, name="mf.ov.ndi.STAGE_EVENT")
        )

    def is_StageEventType_OPENED(type) -> bool:
        return type == int(omni.usd.StageEventType.OPENED)
# endregion
