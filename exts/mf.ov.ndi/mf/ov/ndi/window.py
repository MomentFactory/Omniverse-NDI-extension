from .model import NDIModel, NDIBinding
from .comboboxModel import ComboboxModel
import omni.ui as ui
import pyperclip
import logging


class NDIWindow(ui.Window):
    WINDOW_NAME = "NDI®"
    DEFAULT_TEXTURE_NAME = "myDynamicMaterial"
    NEW_TEXTURE_BTN_TXT = "Create Dynamic Texture"
    DISCOVER_TEX_BTN_TXT = "Discover Dynamic Textures"
    STOP_STREAMS_BTN_TXT = "Stop all streams"
    EMPTY_TEXTURE_LIST_TXT = "No dynamic texture found"

    def __init__(self, delegate=None, **kwargs):
        super().__init__(NDIWindow.WINDOW_NAME, **kwargs)
        self._model: NDIModel = NDIModel(self)
        self._refresh_materials()
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

    def on_kill_all_streams(self):
        for panel in self._bindingPanels:
            panel.on_stream_stopped()

# region UI
    def _ui_section_header(self):
        button_style = {"Button": {"stack_direction": ui.Direction.LEFT_TO_RIGHT}}

        with ui.HStack(height=0):
            self._dynamic_name = ui.StringField()
            self._dynamic_name.model.set_value(NDIWindow.DEFAULT_TEXTURE_NAME)
            ui.Button(NDIWindow.NEW_TEXTURE_BTN_TXT, image_url="resources/glyphs/menu_plus.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_create_dynamic_material)
        with ui.HStack(height=0):
            ui.Button(NDIWindow.DISCOVER_TEX_BTN_TXT, image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_materials)
            ui.Button(NDIWindow.STOP_STREAMS_BTN_TXT, clicked_fn=self._kill_all_streams)

    def _ui_section_bindings(self):
        ComboboxModel.ResetWatchers()
        self._bindingPanels = []
        with ui.ScrollingFrame():
            with ui.VStack():
                bindings: NDIBinding = self._model.get_bindings()
                if len(bindings) == 0:
                    ui.Label(NDIWindow.EMPTY_TEXTURE_LIST_TXT)
                else:
                    for binding in bindings:
                        self._bindingPanels.append(NDIBindingPanel(binding, self._model, self, height=0))
# endregion

# region controls
    def _on_click_create_dynamic_material(self):
        name: str = self._dynamic_name.model.get_value_as_string()
        if name == "":
            logger = logging.getLogger(__name__)
            logger.warning("Cannot create dynamic texture with empty name")
            return
        self._model.create_dynamic_material(name)
        self.refresh_materials_and_rebuild()

    def _on_click_refresh_materials(self):
        self.refresh_materials_and_rebuild()

    def refresh_materials_and_rebuild(self):
        self._refresh_materials()
        # TODO: Better rebuild (sub component instead of whole window)
        self.frame.rebuild()

    def _refresh_materials(self):
        self._model.search_for_dynamic_material()

    def _kill_all_streams(self):
        self._model.kill_all_streams()
        for panel in self._bindingPanels:
            panel.on_stream_stopped()
# endregion


class NDIBindingPanel(ui.CollapsableFrame):
    NDI_INACTIVE = "resources/glyphs/error.svg"
    NDI_ACTIVE = "resources/glyphs/check_solid.svg"
    PLAY_ICON = "resources/glyphs/timeline_play.svg"
    PAUSE_ICON = "resources/glyphs/toolbar_pause.svg"
    COPY_ICON = "resources/glyphs/copy.svg"
    LOW_BANDWIDTH_ICON = "resources/glyphs/AOV_dark.svg"

    PLAYPAUSE_BTN_NAME = "play_pause_btn"
    BANDWIDTH_BTN_NAME = "low_bandwidth_btn"
    COPYPATH_BTN_NAME = "copy_path_btn"

    def __init__(self, binding: NDIBinding, model: NDIModel, window: NDIWindow, **kwargs):
        self._name = binding.get_id()
        super().__init__(self._name, **kwargs)
        self._binding: NDIBinding = binding
        self._binding.set_panel(self)
        self._window = window
        self._model = model
        self._isPlaying = False

        with self:
            with ui.HStack():
                with ui.VStack():
                    with ui.HStack():
                        self._status_icon = ui.Image(NDIBindingPanel.NDI_INACTIVE, width=30)
                        self._combobox_alt = ui.Label("")
                        self._combobox_alt.visible = False
                        self._combobox = ComboboxModel(self._name, self._model, self._binding.get_source(),
                                                       self.on_ndi_status_change, self._combobox_alt)
                        self._combobox_ui = ui.ComboBox(self._combobox)

                        self.playPauseToolButton = ui.Button(text="", image_url=NDIBindingPanel.PLAY_ICON, height=30,
                                                             width=30, clicked_fn=self._on_click_play_pause_ndi,
                                                             name=NDIBindingPanel.PLAYPAUSE_BTN_NAME)
                        self._lowBandWidthButton = ui.ToolButton(image_url=NDIBindingPanel.LOW_BANDWIDTH_ICON, width=30,
                                                                 height=30, tooltip="Low bandwidth mode",
                                                                 clicked_fn=self._set_low_bandwidth_value,
                                                                 name=NDIBindingPanel.BANDWIDTH_BTN_NAME)
                        ui.Button("", image_url=NDIBindingPanel.COPY_ICON, width=30, height=30,
                                  clicked_fn=self._on_click_copy, tooltip="Copy dynamic texture path(dynamic://*)",
                                  name=NDIBindingPanel.COPYPATH_BTN_NAME)
                        self._set_ndi_status_icon(self._combobox.is_active())

    def _set_low_bandwidth_value(self):
        self._binding.set_lowbandwidth(not self._binding.get_lowbandwidth())

    def _on_click_copy(self):
        pyperclip.copy(self._binding.get_id_full())

    def _start_ndi(self):
        lowbandwidth = self._lowBandWidthButton.model.get_value_as_bool()
        if self._model.add_stream(self._binding.get_id(), self._binding.get_source(), lowbandwidth):
            self._lowBandWidthButton.enabled = False
            self._lowBandWidthButton.model.set_value(lowbandwidth)
            self._combobox_ui.visible = False
            self._combobox_alt.visible = True
            self._isPlaying = True
            self._toggle_play_pause_btn()

    def _kill_stream(self):
        self._model.remove_stream(self._binding.get_id(), self._binding.get_source())
        self.on_stream_stopped()

    def on_stream_stopped(self):
        self._lowBandWidthButton.enabled = True
        self._combobox_alt.visible = False
        self._combobox_ui.visible = True
        self._isPlaying = False
        self._toggle_play_pause_btn()

    def _on_click_play_pause_ndi(self):
        if self._isPlaying:
            self._kill_stream()
        else:
            self._start_ndi()

    def _toggle_play_pause_btn(self):
        self.playPauseToolButton.image_url = NDIBindingPanel.PAUSE_ICON if self._isPlaying else NDIBindingPanel.PLAY_ICON

    def on_ndi_status_change(self):
        status = self._binding.get_ndi_status()
        self._set_ndi_status_icon(status)
        if not status:
            self._kill_stream()

    def _set_ndi_status_icon(self, active: bool):
        if active:
            self._status_icon.source_url = NDIBindingPanel.NDI_ACTIVE
        else:
            self._status_icon.source_url = NDIBindingPanel.NDI_INACTIVE
