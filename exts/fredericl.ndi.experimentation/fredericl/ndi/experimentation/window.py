from .model import NDIModel, NDIBinding
from .comboboxModel import ComboboxModel
import omni.ui as ui
import pyperclip
import carb


class NDIWindow(ui.Window):
    WINDOW_NAME = "NDI Dynamic Texture"

    def __init__(self, delegate=None, **kwargs):
        super().__init__(NDIWindow.WINDOW_NAME, **kwargs)
        self._model: NDIModel = NDIModel()
        self._refresh_materials()
        # self._refresh_ndi() Removed because of long search time
        self.frame.set_build_fn(self._build_fn)

    def destroy(self):
        self._model.on_shutdown()
        self._model = None
        super().destroy()

    def _build_fn(self):
        with self.frame:
            with ui.VStack(style={"margin": 3}):
                self._ui_section_header()
                self._ui_section_bindings()

# region UI
    def _ui_section_header(self):
        button_style = {"Button": {"stack_direction": ui.Direction.LEFT_TO_RIGHT}}

        with ui.HStack(height=0):
            self._dynamic_name = ui.StringField()
            self._dynamic_name.model.set_value("myDynamicMaterial")
            ui.Button("Create Dynamic Material", image_url="resources/glyphs/menu_plus.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_create_dynamic_material)
        with ui.HStack(height=0):
            ui.Button("Refresh NDI feeds", image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_ndi)
            ui.Button("Refresh Dynamic Materials", image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_materials)
            ui.Button("Stop all streams", clicked_fn=self._model.kill_all_streams)

    def _ui_section_bindings(self):
        ComboboxModel.ResetWatchers()
        with ui.ScrollingFrame():
            with ui.VStack():
                bindings: NDIBinding = self._model.get_bindings()
                if len(bindings) == 0:
                    ui.Label("No dynamic materials found")
                else:
                    for binding in bindings:
                        NDIBindingPanel(binding, self._model, self, height=0)
# endregion

# region controls
    def _on_click_create_dynamic_material(self):
        name: str = self._dynamic_name.model.get_value_as_string()
        if name == "":
            carb.log_warn("Cannot create dynamic material with empty name")
            return
        self._model.create_dynamic_material(name)
        self.refresh_materials_and_rebuild()

    def _on_click_refresh_ndi(self):
        self._refresh_ndi()

    def _on_click_refresh_materials(self):
        self.refresh_materials_and_rebuild()

    def refresh_materials_and_rebuild(self):
        self._refresh_materials()
        # TODO: Better rebuild (sub component instead of whole window)
        self.frame.rebuild()

    def _refresh_materials(self):
        self._model.search_for_dynamic_material()

    def _refresh_ndi(self):
        self._model.search_for_ndi_feeds()
# endregion


class NDIBindingPanel(ui.CollapsableFrame):
    NDI_INACTIVE = "resources/glyphs/error.svg"
    NDI_ACTIVE = "resources/glyphs/check_solid.svg"

    def __init__(self, binding: NDIBinding, model: NDIModel, window: NDIWindow, **kwargs):
        name = binding.get_id()
        super().__init__(name, **kwargs)
        self._binding: NDIBinding = binding
        self._window = window
        self._model = model
        with self:
            with ui.HStack():
                with ui.VStack():
                    with ui.HStack():
                        ui.Button("C", width=30, clicked_fn=self._on_click_copy)
                        ui.Label(name)
                    with ui.HStack():
                        self._status_label_inactive = ui.Image(NDIBindingPanel.NDI_INACTIVE, width=30)
                        self._status_label_active = ui.Image(NDIBindingPanel.NDI_ACTIVE, width=30)
                        self._on_ndi_status_change()
                        self._combobox = ComboboxModel(name, model, binding.get_source(), self._on_ndi_status_change)
                        binding.register_status_fn(self._on_ndi_status_change)
                        ui.ComboBox(self._combobox)
                        ui.Button(">", width=30, clicked_fn=self._on_click_play_ndi)
                        ui.Button("||", width=30, clicked_fn=self._on_click_pause_ndi)

    def _on_click_copy(self):
        pyperclip.copy(self._binding.get_id_full())

    def _on_click_reset(self):
        self._combobox.select_none()
        self.collapsed = True

    def _on_click_play_ndi(self):
        self._model.add_stream(self._binding.get_id(), self._binding.get_source())

    def _on_click_pause_ndi(self):
        self._model.remove_stream(self._binding.get_id(), self._binding.get_source())

    def _on_ndi_status_change(self):
        status = self._binding.get_ndi_status()
        if status:
            self._status_label_active.visible = True
            self._status_label_inactive.visible = False
        else:
            self._status_label_active.visible = False
            self._status_label_inactive.visible = True
        # TODO: Better rebuild (sub component instead of whole window)
        self._window.frame.rebuild()
