from .comboboxModel import ComboboxModel
from .USDtools import USDtools, DynamicPrim
from .NDItools import NDItools, NDIData, NDIVideoStream, NDIVideoStreamProxy, NDIfinder
from typing import List
import logging
import re
import omni


class NDIBinding():
    def __init__(self, dynamic_id: str, ndi: NDIData, path: str, lowbandwidth: bool):
        self._dynamic_id = dynamic_id
        self._ndi = ndi
        self._path = path
        self._lowbandwidth = lowbandwidth

    def get_id(self) -> str:
        return self._dynamic_id

    def get_id_full(self):
        return USDtools.PREFIX + self._dynamic_id

    def get_source(self) -> str:
        return self._ndi.get_source()

    def set_ndi_id(self, ndi: NDIData):
        self._ndi = ndi
        USDtools.set_prim_ndi_attribute(self._path, self._ndi.get_source())

    def set_lowbandwidth(self, value: bool):
        self._lowbandwidth = value
        USDtools.set_prim_bandwidth_attribute(self._path, self._lowbandwidth)

    def get_lowbandwidth(self) -> bool:
        return self._lowbandwidth

    def register_status_fn(self, fn):
        self._ndi.set_active_value_changed_fn(fn)

    def get_ndi_status(self) -> bool:
        return self._ndi.is_active()


class NDIModel():
    def __init__(self, window):
        self._bindings: List[NDIBinding] = []
        self._ndi_feeds: List[NDIData] = []
        self._reset_ndi_feeds()
        self._window = window

        self._ndi_source_update: List[str] = []
        stream = omni.kit.app.get_app().get_update_event_stream()
        self._sub = stream.create_subscription_to_pop(self._on_update, name="update")

        self._streams: List[NDIVideoStream] = []
        self._ndi_tools = NDItools()
        self._ndi_tools.ndi_init()
        self._ndi_tools.ndi_find_init()
        self._ndi_finder: NDIfinder = NDIfinder(self._on_ndi_source_changed, self._ndi_tools)
        # TODO: kill streams and refresh ui when opening new scene (there must be a subscription for that)

    def _on_update(self, e):
        self._check_for_ndi_source_change()
        self._check_for_stream_not_running()

    def _on_ndi_source_changed(self, sources: List[str]):
        self._ndi_source_update = sources.copy()

    def _check_for_ndi_source_change(self):
        if len(self._ndi_source_update) > 0:
            self._apply_ndi_feeds(self._ndi_source_update)
            self._ndi_source_update = []

    def _check_for_stream_not_running(self):
        to_remove = []
        for stream in self._streams:
            if not stream._is_running:
                to_remove.append(stream)
        for r in to_remove:
            self._streams.remove(r)
            r.destroy()

    def on_shutdown(self):
        self.kill_all_streams()
        if self._ndi_finder:
            self._ndi_finder.destroy()
        self._ndi_tools.destroy()
        self._sub.unsubscribe()

# region streams
    def add_stream(self, name: str, uri: str, lowbandwidth: bool) -> bool:
        if uri == ComboboxModel.NONE_VALUE:
            logger = logging.getLogger(__name__)
            logger.warning("Won't create stream without ndi source")
            return False

        if uri == ComboboxModel.PROXY_VALUE:
            fps = float(re.search("\((.*)\)", uri).group(1).split("p")[1])
            video_stream = NDIVideoStreamProxy(name, uri, fps, lowbandwidth)
            return self._add_stream(video_stream, uri)
        else:
            video_stream = NDIVideoStream(name, uri, lowbandwidth, self._ndi_tools)
            return self._add_stream(video_stream, uri)

    def _add_stream(self, video_stream, uri) -> bool:
        if not video_stream.is_ok:
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening stream: {uri}")
            return False

        self._streams.append(video_stream)
        return True

    def kill_all_streams(self):
        self._window.on_kill_all_streams()
        for stream in self._streams:
            stream.destroy()
        self._streams = []

    def remove_stream(self, name: str, uri: str):
        stream: NDIVideoStream = next((x for x in self._streams if x.name == name and x.uri == uri), None)
        if stream is not None:  # could be none if already stopped
            self._streams.remove(stream)
            stream.destroy()
# endregion

# region dynamic
    def create_dynamic_material(self, name: str):
        USDtools.create_dynamic_material(name)
        self.search_for_dynamic_material()

    def search_for_dynamic_material(self):
        result: List[DynamicPrim] = USDtools.find_all_dynamic_sources()

        # Add new shader sources as bindings
        for dynamic_prim in result:
            dynamic_id = dynamic_prim.name
            ndi_source = dynamic_prim.ndi
            binding = self._get_binding_from_id(dynamic_id)
            lowbandwidth = dynamic_prim.low
            if binding is None:
                source = NDIData(ndi_source, False) if ndi_source is not None else NDItools.NONE_DATA
                binding = NDIBinding(dynamic_id, source, dynamic_prim.path, lowbandwidth)
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
        logger = logging.getLogger(__name__)
        if binding is None:
            logger.error(f"No binding found for {dynamic_id}")
        else:
            ndi = self._find_ndidata_from_source(ndi_source)
            if ndi is None:
                logger.error(f"No ndi source found for {ndi_source}")
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

    def _apply_ndi_feeds(self, others: List[str]):
        previous_sources =  [feed.get_source() for feed in self._ndi_feeds
                             if feed.get_source() is not ComboboxModel.NONE_VALUE
                             and feed.get_source() is not ComboboxModel.PROXY_VALUE]
        new_sources = set(others) - set(previous_sources)
        sources_inactive = set(previous_sources) - set(others)
        sources_active = set(others) & set(previous_sources)

        for other in new_sources:
            self._ndi_feeds.append(NDIData(other, True))

        for other in sources_inactive:
            found: NDIData = self._find_ndidata_from_source(other)
            if found is not None:
                found.set_active(False)

        for other in sources_active:
            found: NDIData = self._find_ndidata_from_source(other)
            if found is not None:
                found.set_active(True)

        self._push_ndi_to_combobox()

    # def force_search_for_ndi_feeds(self):
    #    if self._ndi_finder:
    #        self._ndi_finder.force_search()

    def _reset_ndi_feeds(self):
        self._ndi_feeds = [NDItools.NONE_DATA, NDItools.PROXY_DATA]

    def _push_ndi_to_combobox(self):
        ComboboxModel.SetItems(self._ndi_feeds)

# endregion
