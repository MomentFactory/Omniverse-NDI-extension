import omni.kit.test
from ..window import NDIWindow
from .test_utils import (make_stage, close_stage, get_window, DYNAMIC_ID1, DYNAMIC_ID2, create_dynamic_material,
                         create_dynamic_rectlight, refresh_dynamic_list, get_dynamic_material_prim)


class UITestsHeader(omni.kit.test.AsyncTestCase):
    def setUp(self):
        self._stage = make_stage()
        self._window = get_window()

    def tearDown(self):
        close_stage()

    async def test_create_material_button(self):
        field = self._window.find("**/StringField[*]")
        field.widget.model.set_value(DYNAMIC_ID1)
        self.assertEqual(field.widget.model.get_value_as_string(), DYNAMIC_ID1)

        button = self._window.find(f"**/Button[*].text=='{NDIWindow.NEW_TEXTURE_BTN_TXT}'")
        await button.click()

        prim = get_dynamic_material_prim(DYNAMIC_ID1)
        self.assertTrue(prim.IsValid)

    async def test_texture_discovery(self):
        create_dynamic_material()
        create_dynamic_rectlight()

        await refresh_dynamic_list(self._window)

        panels = self._window.find_all("**/NDIBindingPanel[*]")
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
    def setUp(self):
        self._stage = make_stage()
        self._window = get_window()

    def tearDown(self):
        close_stage()

    async def test_no_panel_on_start(self):
        await refresh_dynamic_list(self._window)

        panel = self._window.find("**/NDIBindingPanel[*]")
        self.assertIsNone(panel)

        label = self._window.find("**/Label[*]")
        self.assertEqual(label.widget.text, NDIWindow.EMPTY_TEXTURE_LIST_TXT)


"""
    async def test_combobox(self):
        button = self._window.find("**/Button[*].text=='Create Dynamic Texture'")
        await button.click()

        combobox = window.find("**/ComboBox[*]")
"""
