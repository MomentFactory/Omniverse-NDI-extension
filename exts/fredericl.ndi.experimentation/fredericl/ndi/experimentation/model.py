from .comboboxModel import ComboboxModel
from .USDtools import USDtools, DynamicPrim
from .NDItools import NDItools, NDIData, NDIVideoStream
from typing import List
import carb
import omni.kit.app


class NDIBinding():
    def __init__(self, dynamic_id: str, ndi: NDIData, path: str):
        self._dynamic_id = dynamic_id
        self._ndi = ndi
        self._path = path

    def get_id(self) -> str:
        return self._dynamic_id

    def get_id_full(self):
        return USDtools.PREFIX + self._dynamic_id

    def get_source(self) -> str:
        return self._ndi.get_source()

    def set_ndi_id(self, ndi: NDIData):
        self._ndi = ndi
        USDtools.set_prim_ndi_attribute(self._path, self._ndi.get_source())

    def register_status_fn(self, fn):
        self._ndi.set_active_value_changed_fn(fn)

    def get_ndi_status(self) -> bool:
        return self._ndi.is_active()


class NDIModel():
    def __init__(self, ):
        self._bindings: List[NDIBinding] = []
        self._ndi_feeds: List[NDIData] = []

        stream = omni.kit.app.get_app().get_update_event_stream()
        self._sub = stream.create_subscription_to_pop(self._on_update, name="update")
        self._streams: List[NDIVideoStream] = []
        # TODO: kill streams and refresh ui when opening new scene (there must be a subscription for that)

# region update loop
    def add_stream(self, name: str, uri: str):
        video_stream = NDIVideoStream(name, uri)
        if not video_stream.is_ok:
            carb.log_error(f"Error opening stream: {uri}")
            return
        self._streams.append(video_stream)

    def kill_all_streams(self):
        self._streams = []

    def remove_stream(self, name: str, uri: str):
        stream: NDIVideoStream = next((x for x in self._streams if x.name == name and x.uri == uri), None)
        if stream is None:
            carb.log_error(f"Could not find stream with name={name} and source={uri}")
            return
        self._streams.remove(stream)

    @carb.profiler.profile
    def _on_update(self, e):
        for stream in self._streams:
            stream.update()

    def on_shutdown(self):
        self._sub.unsubscribe()
        self._streams = []
# endregion

# region dynamic
    def create_dynamic_material(self, name: str):
        USDtools.create_dynamic_material(name)
        self.search_for_dynamic_material()

    def search_for_dynamic_material(self):
        result: List[DynamicPrim] = USDtools.find_all_dynamic_materials()

        # Add new shader sources as bindings
        for dynamic_prim in result:
            dynamic_id = dynamic_prim.name
            ndi_source = dynamic_prim.ndi
            binding = self._get_binding_from_id(dynamic_id)
            if binding is None:
                source = NDIData(ndi_source, False) if ndi_source is not None else NDItools.NONE_DATA
                binding = NDIBinding(dynamic_id, source, dynamic_prim.path)
                self._bindings.append(binding)

        # Remove unresolved bindings
        to_remove: List[int] = []
        for i in range(len(self._bindings)):
            binding = self._bindings[i]
            found: bool = False
            for dynamic_prim in result:
                if binding.get_id() == dynamic_prim.name:
                    found = True
            if not found:
                to_remove.append(i)
        for index in reversed(to_remove):
            self._bindings.pop(index)

        self._sort_bindings()
        self._search_for_ndi_in_bindings()
# endregion

# region bindings
    def get_bindings(self) -> List[NDIBinding]:
        return self._bindings

    def set_binding(self, dynamic_id: str, ndi_source: str):
        binding: NDIBinding = self._get_binding_from_id(dynamic_id)
        if binding is None:
            carb.log_error(f"No binding found for {dynamic_id}")
        else:
            ndi = self._find_ndidata_from_source(ndi_source)
            if ndi is None:
                carb.log_error(f"No ndi source found for {ndi_source}")
            else:
                binding.set_ndi_id(ndi)

    def _get_binding_from_id(self, dynamic_id: str) -> NDIBinding:
        return next((x for x in self._bindings if x.get_id() == dynamic_id), None)

    def _get_binding_from_source(self, source: str) -> NDIBinding:
        return next((x for x in self._bindings if x.get_source() == source), None)

    def _sort_bindings(self):
        self._bindings.sort(key=lambda x: x.get_id())
# endregion

# region NDI
    def _find_ndidata_from_source(self, source: str) -> NDIData:
        return next((x for x in self._ndi_feeds if x.get_source() == source), None)

    def _add_bindings_to_feeds(self):
        for binding in self._bindings:
            ndi = binding.get_source()
            found = self._find_ndidata_from_source(ndi)
            if found is None:
                self._ndi_feeds.append(NDIData(ndi))

    def _search_for_ndi_in_bindings(self):
        self._add_bindings_to_feeds()
        self._push_ndi_to_combobox()

    def search_for_ndi_feeds(self):
        self._reset_ndi_feeds()
        self._add_bindings_to_feeds()

        others = NDItools.find_ndi_sources_long()
        for other in others:
            found: NDIData = self._find_ndidata_from_source(other)
            if found is None:
                self._ndi_feeds.append(NDIData(other, True))
            else:
                found.set_active()

        # TODO: Make inactive if in self._ndi_feeds but not in others

        self._push_ndi_to_combobox()

    def _reset_ndi_feeds(self):
        self._ndi_feeds = [NDItools.NONE_DATA]

    def _push_ndi_to_combobox(self):
        ComboboxModel.clearAllItems()
        for x in self._ndi_feeds:
            ComboboxModel.AddItem(x)
# endregion
