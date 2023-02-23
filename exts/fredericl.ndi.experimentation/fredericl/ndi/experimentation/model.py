from .comboboxModel import ComboboxModel
from .USDtools import USDtools
from .NDItools import NDItools
from typing import List
import carb
from dataclasses import dataclass


@dataclass
class NDIBinding():
    # TODO: Make serializable (custom properties in prim) and read at start + write when changed
    # So window refresh doesn't erase all data
    def __init__(self, dynamic_id: str, ndi_id: str, path: str):
        self._dynamic_id = dynamic_id
        self._ndi_id = ndi_id
        self._path = path

    def get_id(self) -> str:
        return self._dynamic_id

    def get_source(self) -> str:
        return self._ndi_id

    def set_ndi_id(self, ndi_id: str):
        self._ndi_id = ndi_id
        USDtools.set_prim_ndi_attribute(self._path, self._ndi_id)


class NDIModel():
    def __init__(self):
        self._bindings: List[NDIBinding] = []
        self._ndi_feeds: List[str] = []

# region dynamic
    def create_dynamic_material(self, name: str):
        USDtools.create_dynamic_material(name)
        self.search_for_dynamic_material()

    def search_for_dynamic_material(self):
        result = USDtools.find_all_dynamic_materials()

        # Add new shader sources as bindings
        for dynamic_prim in result:
            dynamic_id = dynamic_prim.name
            binding = self._get_binding_from_id(dynamic_id)
            if binding is None:
                binding = NDIBinding(dynamic_id, ComboboxModel.NONE.value(), dynamic_prim.path)
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
# endregion

# region bindings
    def get_bindings(self) -> List[NDIBinding]:
        return self._bindings

    def set_binding(self, dynamic_id: str, ndi_id: str):
        binding: NDIBinding = self._get_binding_from_id(dynamic_id)
        if binding is None:
            carb.log_error(f"No binding found for {dynamic_id}")
        else:
            binding.set_ndi_id(ndi_id)
            print(f"Binding successful between: {binding.get_id()} with {binding.get_source()}")

    def remove_binding(self, binding: NDIBinding):
        self._bindings.remove(binding)
        # TODO: Remove Material?

    def _get_binding_from_id(self, dynamic_id: str) -> NDIBinding:
        return next((x for x in self._bindings if x.get_id() == dynamic_id), None)

    def _get_binding_from_source(self, source: str) -> NDIBinding:
        return next((x for x in self._bindings if x.get_source() == source), None)

    def _sort_bindings(self):
        self._bindings.sort(key=lambda x: x.get_id())
# endregion

# region NDI
    def get_ndi_feeds(self) -> List[str]:
        return self._ndi_feeds

    def search_for_ndi_feeds(self):
        self._ndi_feeds = [ComboboxModel.NONE.value()]
        others = NDItools.find_ndi_sources_long()
        self._ndi_feeds.extend(others)

        # TODO: NDI feed disappeared
        # for binding in self._bindings:
        # source = binding.get_source()
        # match = next((x for x in self._ndi_feeds if x == source), None)
        # if match is None:
        # TODO: make status unknown & keep the feed in the list, change the index to correspond

        ComboboxModel.clearAllItems()
        for x in self._ndi_feeds:
            ComboboxModel.AddItem(x)
# endregion
