import omni.kit.test
from ..window import Window, BindingPanel
from ..comboboxModel import ComboboxModel
from .test_utils import (make_stage, close_stage, get_window, DYNAMIC_ID1, DYNAMIC_ID2, create_dynamic_material,
                         create_dynamic_rectlight, refresh_dynamic_list, get_dynamic_material_prim, add_proxy_source)


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

        button = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")
        await button.click()

        prim = get_dynamic_material_prim(DYNAMIC_ID1)
        self.assertTrue(prim.IsValid)

    async def test_texture_discovery(self):
        create_dynamic_material()
        create_dynamic_rectlight()

        await refresh_dynamic_list(self._window)

        panels = self._window.find_all("**/BindingPanel[*]")
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

        panel = self._window.find("**/BindingPanel[*]")
        self.assertIsNone(panel)

        label = self._window.find("**/Label[*]")
        self.assertEqual(label.widget.text, Window.EMPTY_TEXTURE_LIST_TXT)

    async def test_combobox_defaults(self):
        await refresh_dynamic_list(self._window)
        add_proxy_source(self._window.widget)

        button = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")
        await button.click()
        combobox = self._window.find("**/ComboBox[*]")

        model = combobox.widget.model
        self.assertEqual(model._current_value(), ComboboxModel.NONE_VALUE)

        model._current_index.set_value(1)
        self.assertNotEquals(model._current_value(), ComboboxModel.NONE_VALUE)

        model._current_index.set_value(0)
        self.assertEqual(model._current_value(), ComboboxModel.NONE_VALUE)

    async def test_low_bandwidth_btn(self):
        await refresh_dynamic_list(self._window)

        button = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")
        await button.click()

        panel = self._window.find("**/BindingPanel[*]")
        binding, _, _ = panel.widget._get_data()
        self.assertFalse(binding.lowbandwidth)
        button = panel.find(f"**/ToolButton[*].name=='{BindingPanel.BANDWIDTH_BTN_NAME}'")
        await button.click()
        binding, _, _ = panel.widget._get_data()
        self.assertTrue(binding.lowbandwidth)
        await button.click()
        binding, _, _ = panel.widget._get_data()
        self.assertFalse(binding.lowbandwidth)

    async def test_low_bandwidth_stream(self):
        await refresh_dynamic_list(self._window)
        add_proxy_source(self._window.widget)

        button = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")
        await button.click()

        combobox = self._window.find("**/ComboBox[*]")
        combobox.widget.model._set_current_from_value(ComboboxModel.PROXY_VALUE)

        panel = self._window.find("**/BindingPanel[*]")
        button_bandwidth = panel.find(f"**/ToolButton[*].name=='{BindingPanel.BANDWIDTH_BTN_NAME}'")
        button_playpause = button = panel.find(f"**/Button[*].name=='{BindingPanel.PLAYPAUSE_BTN_NAME}'")

        self.assertTrue(panel.widget._lowbandwidth_toolbutton.enabled)
        await button_playpause.click()
        self.assertFalse(self._window.widget._model._ndi._streams[0]._lowbandwidth)
        self.assertFalse(panel.widget._lowbandwidth_toolbutton.enabled)
        await button_playpause.click()
        self.assertTrue(panel.widget._lowbandwidth_toolbutton.enabled)

        await button_bandwidth.click()

        await button_playpause.click()
        self.assertTrue(self._window.widget._model._ndi._streams[0]._lowbandwidth)
        await button_playpause.click()

    async def test_proxy_play_pause(self):
        await refresh_dynamic_list(self._window)
        add_proxy_source(self._window.widget)

        button_create = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")
        await button_create.click()

        combobox = self._window.find("**/ComboBox[*]")
        combobox.widget.model._set_current_from_value(ComboboxModel.PROXY_VALUE)

        panel = self._window.find("**/BindingPanel[*]")
        button_playpause = panel.find(f"**/Button[*].name=='{BindingPanel.PLAYPAUSE_BTN_NAME}'")
        self.assertTrue(panel.widget._combobox_ui.visible)
        self.assertFalse(panel.widget._combobox_alt.visible)
        await button_playpause.click()

        self.assertGreater(len(self._window.widget._model._ndi._streams), 0)
        self.assertFalse(panel.widget._combobox_ui.visible)
        self.assertTrue(panel.widget._combobox_alt.visible)

        await button_playpause.click()
        self.assertEquals(len(self._window.widget._model._ndi._streams), 0)

    async def test_proxy_multiple(self):
        await refresh_dynamic_list(self._window)

        field = self._window.find("**/StringField[*]")
        button_create = self._window.find(f"**/Button[*].text=='{Window.NEW_TEXTURE_BTN_TXT}'")

        field.widget.model.set_value(DYNAMIC_ID1)
        await button_create.click()
        field.widget.model.set_value(DYNAMIC_ID2)
        await button_create.click()

        comboboxes = self._window.find_all("**/ComboBox[*]")
        for combobox in comboboxes:
            combobox.widget.model._set_current_from_value(ComboboxModel.PROXY_VALUE)

        buttons_playpause = self._window.find_all(f"**/Button[*].name=='{BindingPanel.PLAYPAUSE_BTN_NAME}'")
        for button_playpause in buttons_playpause:
            await button_playpause.click()

        self.assertEquals(len(self._window.widget._model._ndi._streams), 2)

        button_stopall = self._window.find(f"**/Button[*].text=='{Window.STOP_STREAMS_BTN_TXT}'")
        await button_stopall.click()
        self.assertEquals(len(self._window.widget._model._ndi._streams), 0)

        panels = self._window.find_all("**/BindingPanel[*]")
        for panel in panels:
            self.assertTrue(panel.widget._combobox_ui.visible)
            self.assertFalse(panel.widget._combobox_alt.visible)
