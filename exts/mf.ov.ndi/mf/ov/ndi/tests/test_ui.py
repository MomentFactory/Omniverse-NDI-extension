import omni.kit.test
import omni.kit.ui_test as ui_test
from ..window import NDIWindow
from ..USDtools import USDtools
from pxr import Usd, UsdLux


DYNAMIC_ID1 = "myDynamicMaterial1"
DYNAMIC_ID2 = "myDynamicMaterial2"


class UITestsHeader(omni.kit.test.AsyncTestCase):
    def _make_stage(self) -> Usd.Stage:
        usd_context = omni.usd.get_context()
        usd_context.new_stage()
        stage = usd_context.get_stage()
        stage.DefinePrim("/World")
        return stage

    async def test_create_material_button(self):
        stage = self._make_stage()
        window = ui_test.find(NDIWindow.WINDOW_NAME)

        field = window.find("**/StringField[*]")
        field.widget.model.set_value(DYNAMIC_ID1)
        self.assertEqual(field.widget.model.get_value_as_string(), DYNAMIC_ID1)

        button = window.find("**/Button[*].text=='Create Dynamic Texture'")
        await button.click()

        prim = stage.GetPrimAtPath(f"{stage.GetDefaultPrim().GetPath()}/NDI_Looks/{DYNAMIC_ID1}")
        self.assertTrue(prim.IsValid)

    async def test_texture_discovery(self):
        stage = self._make_stage()
        window = ui_test.find(NDIWindow.WINDOW_NAME)

        USDtools.create_dynamic_material(DYNAMIC_ID1)

        path: str = f"{stage.GetDefaultPrim().GetPath()}/myRectLight"
        light = UsdLux.RectLight.Define(stage, path)
        light.GetPrim().GetAttribute("texture:file").Set(f"{USDtools.PREFIX}{DYNAMIC_ID2}")

        button = window.find("**/Button[*].text=='Discover Dynamic Textures'")
        await button.click()

        panels = window.find_all("**/NDIBindingPanel[*]")
        self.assertEqual(len(panels), 2)

        panel1_found = False
        panel2_found = False
        for panel in panels:
            labels = panel.find_all("**/Label[*]")
            for label in labels:
                if label.widget.text == DYNAMIC_ID1:
                    panel1_found = True
                elif label.widget.text == DYNAMIC_ID2:
                    panel2_found = True

        self.assertTrue(panel1_found)
        self.assertTrue(panel2_found)


class UITestsPanel(omni.kit.test.AsyncTestCase):
    async def test_no_panel_on_start(self):
        window = ui_test.find(NDIWindow.WINDOW_NAME)
        panel = window.find("**/NDIBindingPanel[*]")
        self.assertIsNone(panel)

        label = window.find("**/Label[*]")
        self.assertEqual(label.widget.text, "No dynamic texture found")


"""
    async def test_combobox(self):
        self._make
        window = ui_test.find(NDIWindow.WINDOW_NAME)
        button = window.find("**/Button[*].text=='Create Dynamic Texture'")
        await button.click()

        combobox = window.find("**/ComboBox[*]")
"""
