from .comboboxModel import ComboboxModel
from .eventsystem import EventSystem

import carb.events
from dataclasses import dataclass
from typing import List


@dataclass
class DynamicPrim:
    path: str
    dynamic_id: str
    ndi_source_attr: str
    lowbandwidth_attr: bool


@dataclass
class Binding():
    dynamic_id: str
    ndi_source: str
    lowbandwidth: bool


@dataclass
class NDIData():
    source: str
    active: bool


class BindingsModel():
    NONE_DATA = NDIData(ComboboxModel.NONE_VALUE, False)

    def __init__(self):
        self._bindings: List[Binding] = []
        self._dynamic_prims: List[DynamicPrim] = []
        self._ndi_sources: List[NDIData] = []

        self._ndi_sources.append(BindingsModel.NONE_DATA)

        self._sub = EventSystem.subscribe(EventSystem.NDIFINDER_NEW_SOURCES, self._ndi_sources_change_evt_callback)

    def destroy(self):
        self._sub.unsubscribe()
        self._sub = None

        self._dynamic_prims = []
        self._bindings = []
        self._ndi_sources = []

    def count(self):
        return len(self._bindings)

    def get(self, index: int) -> Binding:
        binding: Binding = self._bindings[index]
        prim: DynamicPrim = self.find_binding_from_id(binding.dynamic_id)
        ndi: NDIData = self._find_ndi_from_source(binding.ndi_source)
        return binding, prim, ndi

    def get_source_list(self) -> List[str]:
        return [x.source for x in self._ndi_sources]

    def _get_non_static_source_list(self) -> List[NDIData]:
        return self._ndi_sources[1:]  # Excludes NONE_DATA

    def get_prim_list(self) -> List[str]:
        return [x for x in self._dynamic_prims]

    def bind(self, dynamic_id, new_source):
        binding: Binding = self.find_binding_from_id(dynamic_id)
        binding.ndi_source = new_source

    def set_low_bandwidth(self, dynamic_id: str, value: bool):
        binding: Binding = self.find_binding_from_id(dynamic_id)
        binding.lowbandwidth = value

    def find_binding_from_id(self, dynamic_id: str) -> Binding:
        return next((x for x in self._bindings if x.dynamic_id == dynamic_id), None)

    def _find_binding_from_ndi(self, ndi_source: str) -> Binding:
        return next((x for x in self._bindings if x.source == ndi_source), None)

    def _find_ndi_from_source(self, ndi_source: str) -> NDIData:
        if ndi_source is None:
            return self._ndi_sources[0]
        return next((x for x in self._ndi_sources if x.source == ndi_source), None)

    def update_dynamic_prims(self, prims: List[DynamicPrim]):
        self._dynamic_prims = prims
        self._update_ndi_from_prims()
        self._update_bindings_from_prims()
        EventSystem.send_event(EventSystem.BINDINGS_CHANGED_EVENT)

    def _update_ndi_from_prims(self):
        for dynamic_prim in self._dynamic_prims:
            ndi: NDIData = self._find_ndi_from_source(dynamic_prim.ndi_source_attr)
            if ndi is None:
                self._ndi_sources.append(NDIData(dynamic_prim.ndi_source_attr, False))

    def _update_bindings_from_prims(self):
        self._bindings.clear()
        for dynamic_prim in self._dynamic_prims:
            source_attr = dynamic_prim.ndi_source_attr
            source: str = source_attr if source_attr is not None else BindingsModel.NONE_DATA.source
            self._bindings.append(Binding(dynamic_prim.dynamic_id, source, dynamic_prim.lowbandwidth_attr))

    def _ndi_sources_change_evt_callback(self, e: carb.events.IEvent):
        sources = e.payload["sources"]
        self._update_ndi_new_and_active_sources(sources)
        self._update_ndi_inactive_sources(sources)
        EventSystem.send_event(EventSystem.COMBOBOX_SOURCE_CHANGE_EVENT,
                               payload={"sources": [x.source for x in self._ndi_sources]})
        EventSystem.send_event(EventSystem.NDI_STATUS_CHANGE_EVENT)

    def _update_ndi_new_and_active_sources(self, sources: List[str]):
        for source in sources:
            data: NDIData = self._find_ndi_from_source(source)
            if data is None:
                data = NDIData(source, True)
                self._ndi_sources.append(data)
            else:
                data.active = True

    def _update_ndi_inactive_sources(self, sources: List[str]):
        for ndi in self._get_non_static_source_list():
            is_active = next((x for x in sources if x == ndi.source), None)
            if is_active is None:
                ndi.active = False
