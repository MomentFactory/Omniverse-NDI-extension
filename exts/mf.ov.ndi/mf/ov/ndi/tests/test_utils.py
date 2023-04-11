import omni
import omni.kit.ui_test as ui_test
from pxr import Usd, UsdLux, UsdShade
from ..USDtools import USDtools
from ..window import NDIWindow

SOURCE1 = "MY-PC (Test Pattern)"
SOURCE2 = "MY-PC (Test Pattern 2)"
DYNAMIC_ID1 = "myDynamicMaterial1"
DYNAMIC_ID2 = "myDynamicMaterial2"
DUMMY_PATH = "/path/to/dummy"


def make_stage() -> Usd.Stage:
    usd_context = omni.usd.get_context()
    usd_context.new_stage()
    # self._stage = Usd.Stage.CreateInMemory()

    stage = usd_context.get_stage()
    prim = stage.DefinePrim("/World")
    stage.SetDefaultPrim(prim)

    return stage


def get_stage() -> Usd.Stage:
    usd_context = omni.usd.get_context()
    stage = usd_context.get_stage()
    return stage


def close_stage():
    usd_context = omni.usd.get_context()
    assert usd_context.can_close_stage()
    usd_context.close_stage()


def get_window():
    return ui_test.find(NDIWindow.WINDOW_NAME)


def create_dynamic_material() -> UsdShade.Material:
    return USDtools.create_dynamic_material(DYNAMIC_ID1)


def create_dynamic_rectlight():
    stage = get_stage()
    path: str = f"{stage.GetDefaultPrim().GetPath()}/myRectLight"
    light = UsdLux.RectLight.Define(stage, path)
    light.GetPrim().GetAttribute("texture:file").Set(f"{USDtools.PREFIX}{DYNAMIC_ID2}")


async def refresh_dynamic_list(window):
    button = window.find("**/Button[*].text=='Discover Dynamic Textures'")
    await button.click()
