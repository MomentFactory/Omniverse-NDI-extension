from .bindings import Binding, BindingsModel
from .comboboxModel import ComboboxModel
from .NDItools import NDItools
from .USDtools import DynamicPrim, USDtools

import logging
import re
from typing import List


class Model():
    def __init__(self):
        self._bindings_model: BindingsModel = BindingsModel()
        self._ndi: NDItools = NDItools()

    def destroy(self):
        self._ndi.destroy()
        self._bindings_model.destroy()

# region bindings
    def get_bindings_count(self) -> int:
        return self._bindings_model.count()

    def get_binding_data_from_index(self, index: int):
        return self._bindings_model.get(index)

    def get_ndi_source_list(self) -> List[str]:
        return self._bindings_model.get_source_list()

    def apply_new_binding_source(self, dynamic_id: str, new_source: str):
        self._bindings_model.bind(dynamic_id, new_source)

    def apply_lowbandwidth_value(self, dynamic_id: str, value: bool):
        self._bindings_model.set_low_bandwidth(dynamic_id, value)
# endregion

# region dynamic
    def create_dynamic_material(self, name: str):
        safename = USDtools.make_name_valid(name)
        if name != safename:
            logger = logging.getLogger(__name__)
            logger.warn(f"Name \"{name}\" was not a valid USD identifier, changed it to \"{safename}\"")

        if self._bindings_model.find_binding_from_id(safename) is not None:
            logger = logging.getLogger(__name__)
            logger.warning(f"There's already a texture with the name {safename}")
            return

        USDtools.create_dynamic_material(safename)
        self.search_for_dynamic_material()

    def search_for_dynamic_material(self):
        result: List[DynamicPrim] = USDtools.find_all_dynamic_sources()
        self._bindings_model.update_dynamic_prims(result)

    def _get_prims_with_id(self, dynamic_id: str) -> List[DynamicPrim]:
        prims: List[DynamicPrim] = self._bindings_model.get_prim_list()
        return [x for x in prims if x.dynamic_id == dynamic_id]

    def set_ndi_source_prim_attr(self, dynamic_id: str, source: str):
        for prim in self._get_prims_with_id(dynamic_id):
            USDtools.set_prim_ndi_attribute(prim.path, source)

    def set_lowbandwidth_prim_attr(self, dynamic_id: str, value: bool):
        for prim in self._get_prims_with_id(dynamic_id):
            USDtools.set_prim_lowbandwidth_attribute(prim.path, value)
# endregion

# region stream
    def try_add_stream(self, binding: Binding, lowbandwidth: bool) -> bool:
        if self._ndi.get_stream(binding.dynamic_id) is not None:
            logger = logging.getLogger(__name__)
            logger.warning(f"There's already a stream running for {binding.dynamic_id}")
            return False

        if binding.ndi_source == ComboboxModel.NONE_VALUE:
            logger = logging.getLogger(__name__)
            logger.warning("Won't create stream without NDI® source")
            return False

        if binding.ndi_source == ComboboxModel.PROXY_VALUE:
            fps = float(re.search("\((.*)\)", binding.ndi_source).group(1).split("p")[1])
            success: bool = self._ndi.try_add_stream_proxy(binding.dynamic_id, binding.ndi_source, fps, lowbandwidth)
            return success
        else:
            success: bool = self._ndi.try_add_stream(binding.dynamic_id, binding.ndi_source, lowbandwidth)
            return success

    def stop_stream(self, binding: Binding):
        self._ndi.stop_stream(binding.dynamic_id)

    def stop_all_streams(self):
        self._ndi.stop_all_streams()
# endregion
