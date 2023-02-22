from .comboboxModel import ComboboxModel
from .NDItools import NDItools as ndi
from .USDtools import USDtools as usd
import omni.ui as ui
from pxr import Tf


class NDIWindow(ui.Window):

    def __init__(self, add_stream_fn, remove_stream_fn, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)
        self.frame.set_build_fn(self._build_fn)
        self._add_stream_fn = add_stream_fn
        self._remove_stream_fn = remove_stream_fn

    def destroy(self):
        super().destroy()

    def _build_fn(self):
        with self.frame:
            with ui.VStack(style={"margin": 3}):
                self._row1_ndi_source()
                self._row2_parent_path()
                self._row3_create_prim()

    def _row1_ndi_source(self):
        with ui.HStack(height=30):
            ui.Label("Source:", width=100, alignment=ui.Alignment.RIGHT_CENTER)

            self._label = ui.Label("No NDI source found")

            self._minimal_model = ComboboxModel()
            self._combobox = ui.ComboBox(self._minimal_model)
            self._refresh_combobox(self._minimal_model)

            ui.Button("R", clicked_fn=lambda: self._refresh_combobox(self._minimal_model), width=30)
            ui.Button("L", clicked_fn=lambda: self._refresh_combobox_long(self._minimal_model), width=30)

    def _row2_parent_path(self):
        with ui.HStack(height=30):
            ui.Label("Parent Prim:", width=100, alignment=ui.Alignment.RIGHT_CENTER)
            self._parent_prim_path = ui.StringField()

    def _row3_create_prim(self):
        with ui.HStack():
            ui.Button("Start Stream", clicked_fn=self._on_click_start_stream, width=ui.Percent(25))
            ui.Button("Stop Streams", clicked_fn=self._on_click_stop_streams, width=ui.Percent(25))
            ui.Button("Create Scene element", clicked_fn=self._on_click_create_scene_elements, width=ui.Percent(50))

    def _on_click_start_stream(self):
        name = self.get_current_item_tfvalid_name()
        stream_uri = self.get_current_item_fullname()
        stream_success: bool = self._add_stream_fn(name, stream_uri)
        if stream_success:
            print("Stream ok")
        else:
            print("Stream not ok")

    def _on_click_stop_streams(self):
        self._remove_stream_fn()

    def _on_click_create_scene_elements(self):
        name = self.get_current_item_tfvalid_name()
        path = self._parent_prim_path.model.get_value_as_string()
        usd.on_click_create(name, path, 192, 108)

    def _display_label(self):
        self._label.visible = True
        self._combobox.visible = False

    def _display_combobox(self):
        self._label.visible = False
        self._combobox.visible = True

    def _refresh_combobox_long(self, model):
        model.clearAllItems()

        sources = ndi.find_ndi_sources_long()
        if len(sources) == 0:
            self._display_label()
        else:
            self._display_combobox()

        for s in sources:
            model.append_child_item(None, s)

    def _refresh_combobox(self, model):
        model.clearAllItems()

        sources = ndi.find_ndi_sources()
        if len(sources) == 0:
            self._display_label()
        else:
            self._display_combobox()

        for s in sources:
            model.append_child_item(None, s)

    def get_current_item_tfvalid_name(self):
        return Tf.MakeValidIdentifier(ndi.get_name_from_ndi_name(self._minimal_model.currentvalue()))

    def get_current_item_fullname(self):
        return self._minimal_model.currentvalue()
