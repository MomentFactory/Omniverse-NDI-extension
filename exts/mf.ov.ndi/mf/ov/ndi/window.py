from .bindings import Binding
from .comboboxModel import ComboboxModel
from .eventsystem import EventSystem
from .model import Model
from .USDtools import USDtools

import asyncio
import carb.events
import omni.ui as ui
import omni.kit.app
import pyperclip
from typing import List


class Window(ui.Window):
    WINDOW_NAME = "NDI®"

    DEFAULT_TEXTURE_NAME = "myDynamicMaterial"
    NEW_TEXTURE_BTN_TXT = "Create Dynamic Texture"
    DISCOVER_TEX_BTN_TXT = "Discover Dynamic Textures"
    STOP_STREAMS_BTN_TXT = "Stop all streams"
    EMPTY_TEXTURE_LIST_TXT = "No dynamic texture found"

    def __init__(self, delegate=None, **kwargs):
        self._model: Model = Model()
        self._bindingPanels: List[BindingPanel] = []

        super().__init__(Window.WINDOW_NAME, **kwargs)
        self.frame.set_build_fn(self._build_fn)

        self._subscribe()
        self._model.search_for_dynamic_material()

    def destroy(self):
        for panel in self._bindingPanels:
            panel.destroy()
        self._model.destroy()
        self._unsubscribe()
        super().destroy()

    def _subscribe(self):
        self._sub: List[carb.events.ISubscription] = []
        self._sub.append(EventSystem.subscribe(EventSystem.BINDINGS_CHANGED_EVENT, self._bindings_updated_evt_callback))
        self._sub.append(EventSystem.subscribe(EventSystem.COMBOBOX_CHANGED_EVENT, self._combobox_changed_evt_callback))
        self._sub.append(EventSystem.subscribe(EventSystem.COMBOBOX_SOURCE_CHANGE_EVENT,
                                               self._ndi_sources_changed_evt_callback))
        self._sub.append(EventSystem.subscribe(EventSystem.NDI_STATUS_CHANGE_EVENT,
                                               self._ndi_status_change_evt_callback))
        self._sub.append(EventSystem.subscribe(EventSystem.STREAM_STOP_TIMEOUT_EVENT,
                                               self._stream_stop_timeout_evt_callback))
        self._sub.append(USDtools.subscribe_to_stage_events(self._stage_event_evt_callback))

    def _unsubscribe(self):
        for sub in self._sub:
            sub.unsubscribe()
            sub = None
        self._sub.clear()

    def _build_fn(self):
        with ui.VStack(style={"margin": 3}):
            self._ui_section_header()
            self._ui_section_bindings()

# region events callback
    def _bindings_updated_evt_callback(self, e: carb.events.IEvent):
        self.frame.rebuild()

    def _combobox_changed_evt_callback(self, e: carb.events.IEvent):
        value: str = e.payload["value"]
        dynamic_id = e.payload["id"]
        panel_index = e.payload["index"]

        self._model.apply_new_binding_source(dynamic_id, value)
        self._model.set_ndi_source_prim_attr(dynamic_id, value)

        if (len(self._bindingPanels) > panel_index):
            self._bindingPanels[panel_index].combobox_item_changed()

    def _ndi_sources_changed_evt_callback(self, e: carb.events.IEvent):
        for panel in self._bindingPanels:
            panel.combobox_items_changed(e.payload["sources"])

    def _ndi_status_change_evt_callback(self, e: carb.events.IEvent):
        for panel in self._bindingPanels:
            panel.check_for_ndi_status()

    def _stream_stop_timeout_evt_callback(self, e: carb.events.IEvent):
        panel: BindingPanel = next(x for x in self._bindingPanels if x.get_dynamic_id() == e.payload["dynamic_id"])
        panel.on_stop_stream()

    def _stage_event_evt_callback(self, e: carb.events.IEvent):
        if USDtools.is_StageEventType_OPENED(e.type):
            self._model.search_for_dynamic_material()
# endregion

# region UI
    def _ui_section_header(self):
        button_style = {"Button": {"stack_direction": ui.Direction.LEFT_TO_RIGHT}}

        with ui.HStack(height=0):
            self._dynamic_name = ui.StringField()
            self._dynamic_name.model.set_value(Window.DEFAULT_TEXTURE_NAME)
            ui.Button(Window.NEW_TEXTURE_BTN_TXT, image_url="resources/glyphs/menu_plus.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_create_dynamic_material)

        with ui.HStack(height=0):
            ui.Button(Window.DISCOVER_TEX_BTN_TXT, image_url="resources/glyphs/menu_refresh.svg", image_width=24,
                      style=button_style, clicked_fn=self._on_click_refresh_materials)
            ui.Button(Window.STOP_STREAMS_BTN_TXT, clicked_fn=self._on_click_stop_all_streams)

    def _ui_section_bindings(self):
        self._bindingPanels = []
        with ui.ScrollingFrame():
            with ui.VStack():
                count: int = self._model.get_bindings_count()
                if count == 0:
                    ui.Label(Window.EMPTY_TEXTURE_LIST_TXT)
                else:
                    for i in range(count):
                        self._bindingPanels.append(BindingPanel(i, self, height=0))
# endregion

# region controls
    def _on_click_create_dynamic_material(self):
        name: str = self._dynamic_name.model.get_value_as_string()
        self._model.create_dynamic_material(name)

    def _on_click_refresh_materials(self):
        self._model.search_for_dynamic_material()

    def _on_click_stop_all_streams(self):
        self._model.stop_all_streams()
        for panel in self._bindingPanels:
            panel.on_stop_stream()
# endregion

# region BindingPanel Callable
    def get_binding_data_from_index(self, index: int):
        return self._model.get_binding_data_from_index(index)

    def get_choices_for_combobox(self) -> List[str]:
        return self._model.get_ndi_source_list()

    def apply_lowbandwidth_value(self, dynamic_id: str, value: bool):
        self._model.apply_lowbandwidth_value(dynamic_id, value)
        self._model.set_lowbandwidth_prim_attr(dynamic_id, value)

    def try_add_stream(self, binding: Binding, lowbandwidth: bool, update_fps_fn) -> bool:
        return self._model.try_add_stream(binding, lowbandwidth, update_fps_fn)

    def stop_stream(self, binding: Binding):
        return self._model.stop_stream(binding)
# endregion


class BindingPanel(ui.CollapsableFrame):
    NDI_COLOR_STOPPED = "#E6E7E8"
    NDI_COLOR_PLAYING = "#78B159"
    NDI_COLOR_WARNING = "#F4900C"
    NDI_COLOR_INACTIVE = "#DD2E45"

    NDI_STATUS = "resources/glyphs/circle.svg"
    PLAY_ICON = "resources/glyphs/timeline_play.svg"
    PAUSE_ICON = "resources/glyphs/toolbar_pause.svg"
    COPY_ICON = "resources/glyphs/copy.svg"
    LOW_BANDWIDTH_ICON = "resources/glyphs/AOV_dark.svg"

    PLAYPAUSE_BTN_NAME = "play_pause_btn"
    BANDWIDTH_BTN_NAME = "low_bandwidth_btn"
    COPYPATH_BTN_NAME = "copy_path_btn"

    RUNNING_LABEL_SUFFIX = " - running"

    def __init__(self, index: int, window: Window, **kwargs):
        self._index = index
        self._window = window
        binding, _, ndi = self._get_data()
        choices = self._get_choices()
        self._dynamic_id = binding.dynamic_id
        self._lowbandwidth_value = binding.lowbandwidth
        self._is_playing = False

        super().__init__(binding.dynamic_id, **kwargs)

        self._info_window = None

        with self:
            with ui.HStack():
                self._status_icon = ui.Image(BindingPanel.NDI_STATUS, width=20,
                                             mouse_released_fn=self._show_info_window)
                self._set_ndi_status_icon(ndi.active)

                self._combobox_alt = ui.Label("")
                self._set_combobox_alt_text(binding.ndi_source)
                self._combobox_alt.visible = False

                self._combobox = ComboboxModel(choices, binding.ndi_source, binding.dynamic_id, self._index)
                self._combobox_ui = ui.ComboBox(self._combobox)

                self.play_pause_toolbutton = ui.Button(text="", image_url=BindingPanel.PLAY_ICON, height=30,
                                                       width=30, clicked_fn=self._on_click_play_pause_ndi,
                                                       name=BindingPanel.PLAYPAUSE_BTN_NAME)
                self._lowbandwidth_toolbutton = ui.ToolButton(image_url=BindingPanel.LOW_BANDWIDTH_ICON, width=30,
                                                              height=30, tooltip="Low bandwidth mode",
                                                              clicked_fn=self._set_low_bandwidth_value,
                                                              name=BindingPanel.BANDWIDTH_BTN_NAME)
                self._lowbandwidth_toolbutton.model.set_value(self._lowbandwidth_value)
                ui.Button("", image_url=BindingPanel.COPY_ICON, width=30, height=30, clicked_fn=self._on_click_copy,
                          tooltip="Copy dynamic texture path(dynamic://*)", name=BindingPanel.COPYPATH_BTN_NAME)

    def destroy(self):
        self._info_window_destroy()

    # region Info Window
    def _show_info_window(self, _x, _y, button, _modifier):
        if (button == 0):  # left click
            binding, _, _ = self._get_data()
            if not self._info_window:
                self._info_window = StreamInfoWindow(f"{self._dynamic_id} info", binding.ndi_source,
                                                     width=280, height=140)
                self._info_window.set_visibility_changed_fn(self._info_window_visibility_changed)
            elif self._info_window:
                self._info_window_destroy()

    def _info_window_visibility_changed(self, visible):
        if not visible:
            asyncio.ensure_future(self._info_window_destroy_async())

    def _info_window_destroy(self):
        if self._info_window:
            self._info_window.destroy()
            self._info_window = None

    async def _info_window_destroy_async(self):
        await omni.kit.app.get_app().next_update_async()
        if self._info_window:
            self._info_window_destroy()

    def update_fps(self, fps_current: float, fps_average: float, fps_expected: float):
        if self._info_window:
            self._info_window.set_fps_values(fps_current, fps_average, fps_expected)
    # endregion

    def combobox_items_changed(self, items: List[str]):
        binding, _, _ = self._get_data()
        self._combobox.set_items_and_current(items, binding.ndi_source)

    def check_for_ndi_status(self):
        _, _, ndi = self._get_data()
        self._set_ndi_status_icon(ndi.active)

    def combobox_item_changed(self):
        binding, _, ndi = self._get_data()
        self._set_combobox_alt_text(binding.ndi_source)
        self._set_ndi_status_icon(ndi.active)
        if self._info_window:
            self._info_window.set_stream_name(binding.ndi_source)

    def get_dynamic_id(self) -> str:
        return self._dynamic_id

    def _get_data(self):
        return self._window.get_binding_data_from_index(self._index)

    def _get_choices(self):
        return self._window.get_choices_for_combobox()

    def _on_click_copy(self):
        pyperclip.copy(f"{USDtools.PREFIX}{self._dynamic_id}")

    def _set_low_bandwidth_value(self):
        self._lowbandwidth_value = not self._lowbandwidth_value
        self._window.apply_lowbandwidth_value(self._dynamic_id, self._lowbandwidth_value)

    def _on_play_stream(self):
        self._is_playing = True
        self.play_pause_toolbutton.image_url = BindingPanel.PAUSE_ICON
        self._lowbandwidth_toolbutton.enabled = False
        self._combobox_ui.visible = False
        self._combobox_alt.visible = True
        self.check_for_ndi_status()

    def on_stop_stream(self):
        self._is_playing = False
        self.play_pause_toolbutton.image_url = BindingPanel.PLAY_ICON
        self._lowbandwidth_toolbutton.enabled = True
        self._combobox_ui.visible = True
        self._combobox_alt.visible = False
        self.check_for_ndi_status()

    def _on_click_play_pause_ndi(self):
        binding, _, _ = self._get_data()
        if self._is_playing:
            self._window.stop_stream(binding)
            self.on_stop_stream()
        else:
            if self._window.try_add_stream(binding, self._lowbandwidth_value, self.update_fps):
                self._on_play_stream()

    def _set_combobox_alt_text(self, text: str):
        self._combobox_alt.text = f"{text}{BindingPanel.RUNNING_LABEL_SUFFIX}"

    def _set_ndi_status_icon(self, active: bool):
        if active and self._is_playing:
            self._status_icon.style = {"color": ui.color(BindingPanel.NDI_COLOR_PLAYING)}
        elif active and not self._is_playing:
            self._status_icon.style = {"color": ui.color(BindingPanel.NDI_COLOR_STOPPED)}
        elif not active and self._is_playing:
            self._status_icon.style = {"color": ui.color(BindingPanel.NDI_COLOR_WARNING)}
        else:  # not active and not self._is_playing
            self._status_icon.style = {"color": ui.color(BindingPanel.NDI_COLOR_INACTIVE)}


class StreamInfoWindow(ui.Window):
    def __init__(self, dynamic_id: str, ndi_id: str, delegate=None, **kwargs):
        super().__init__(dynamic_id, **kwargs)
        self.frame.set_build_fn(self._build_fn)
        self._stream_name = ndi_id

    def destroy(self):
        super().destroy()

    def _build_fn(self):
        with ui.VStack(height=0):
            with ui.HStack():
                ui.Label("Stream name:")
                self._stream_name_model = ui.StringField(enabled=False).model
                self._stream_name_model.set_value(self._stream_name)
            with ui.HStack():
                ui.Label("current fps:")
                self._fps_current_model = ui.FloatField(enabled=False).model
                self._fps_current_model.set_value(0.0)
            with ui.HStack():
                ui.Label("average fps:")
                self._fps_average_model = ui.FloatField(enabled=False).model
                self._fps_average_model.set_value(0.0)
            with ui.HStack():
                ui.Label("expected fps:")
                self._fps_expected_model = ui.FloatField(enabled=False).model
                self._fps_expected_model.set_value(0.0)

    def set_fps_values(self, fps_current: float, fps_average: float, fps_expected: float):
        if hasattr(self, "_fps_expected_model"):
            self._fps_current_model.set_value(fps_current)
            self._fps_average_model.set_value(fps_average)
            self._fps_expected_model.set_value(fps_expected)

    def set_stream_name(self, name: str):
        self._stream_name_model.set_value(name)
