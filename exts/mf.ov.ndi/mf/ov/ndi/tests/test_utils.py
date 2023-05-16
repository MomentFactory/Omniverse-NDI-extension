import omni
import omni.kit.ui_test as ui_test
from pxr import Usd, UsdLux, UsdShade
from ..USDtools import USDtools
from ..window import Window
from ..eventsystem import EventSystem
from ..comboboxModel import ComboboxModel

SOURCE1 = "MY-PC (Test Pattern)"
SOURCE2 = "MY-PC (Test Pattern 2)"
DYNAMIC_ID1 = "myDynamicMaterial1"
DYNAMIC_ID2 = "myDynamicMaterial2"
DUMMY_PATH = "/path/to/dummy"
RECTLIGHT_NAME = "MyRectLight"
DEFAULT_PRIM_NAME = "World"


def make_stage() -> Usd.Stage:
    usd_context = omni.usd.get_context()
    usd_context.new_stage()
    # self._stage = Usd.Stage.CreateInMemory()

    stage = usd_context.get_stage()
    prim = stage.DefinePrim(f"/{DEFAULT_PRIM_NAME}")
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
    return ui_test.find(Window.WINDOW_NAME)


def create_dynamic_material() -> UsdShade.Material:
    USDtools.create_dynamic_material(DYNAMIC_ID1)
    return get_dynamic_material_prim(DYNAMIC_ID1)


def create_dynamic_rectlight():
    stage = get_stage()
    path: str = f"{stage.GetDefaultPrim().GetPath()}/{RECTLIGHT_NAME}"
    light = UsdLux.RectLight.Define(stage, path)
    light.GetPrim().GetAttribute("texture:file").Set(f"{USDtools.PREFIX}{DYNAMIC_ID2}")


def get_dynamic_material_prim(name: str):
    usd_context = omni.usd.get_context()
    stage = usd_context.get_stage()
    return stage.GetPrimAtPath(f"{stage.GetDefaultPrim().GetPath()}/{USDtools.SCOPE_NAME}/{name}")


async def refresh_dynamic_list(window):
    button = window.find(f"**/Button[*].text=='{Window.DISCOVER_TEX_BTN_TXT}'")
    await button.click()


def add_proxy_source(window):
    EventSystem.send_event(EventSystem.NDIFINDER_NEW_SOURCES, payload={"sources": [ComboboxModel.PROXY_VALUE]})
