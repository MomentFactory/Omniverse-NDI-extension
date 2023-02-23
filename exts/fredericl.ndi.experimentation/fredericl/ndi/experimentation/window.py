from .model import NDIModel, NDIBinding
from .comboboxModel import ComboboxModel
import omni.ui as ui
import pyperclip


class NDIWindow(ui.Window):
    WINDOW_NAME = "NDI Dynamic Texture"

    def __init__(self, model: NDIModel, delegate=None, **kwargs):
        super().__init__(NDIWindow.WINDOW_NAME, **kwargs)
        self._count = 0  # Eventually obsolete?
        self._model: NDIModel = model
        # self._refresh_materials() Removed because scene not always present when called
        # self._refresh_ndi() Removed because of long search time
        self.frame.set_build_fn(self._build_fn)

    def destroy(self):
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
            ui.Button("Create Dynamic Material", image_url="resources/glyphs/menu_plus.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_create_dynamic_material)
            ui.Button("Refresh NDI feeds", image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_ndi)
            ui.Button("Refresh Dynamic Materials", image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_materials)

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
        suffix: str = "" if self._count == 0 else str(self._count)
        self._model.create_dynamic_material(f"myDynamicMaterial{suffix}")
        self._count += 1
        self.refresh_materials_and_rebuild()

    def _on_click_refresh_ndi(self):
        self._refresh_ndi()

    def _on_click_refresh_materials(self):
        self.refresh_materials_and_rebuild()

    def refresh_materials_and_rebuild(self):
        self._refresh_materials()
        self.frame.rebuild()

    def _refresh_materials(self):
        self._model.search_for_dynamic_material()

    def _refresh_ndi(self):
        self._model.search_for_ndi_feeds()
# endregion


class NDIBindingPanel(ui.CollapsableFrame):
    def __init__(self, binding: NDIBinding, model: NDIModel, window: NDIWindow, **kwargs):
        name = binding.get_id()
        super().__init__(name, **kwargs)
        self._binding: NDIBinding = binding
        self._window = window
        with self:
            with ui.HStack():
                with ui.VStack():
                    with ui.HStack():
                        ui.Button("C", width=30, clicked_fn=self._on_click_copy)
                        ui.Label(name)
                    with ui.HStack():
                        ui.Button("Y", width=30)  # TODO: Not a button (maybe eventually when stats)
                        self._combobox = ComboboxModel(name, model)
                        ui.ComboBox(self._combobox)
                ui.Button("X", width=25, clicked_fn=self._on_click_reset)

    def _on_click_copy(self):
        pyperclip.copy(self._binding.get_id())

    def _on_click_reset(self):
        self._combobox.select_none()
        self.collapsed = True
