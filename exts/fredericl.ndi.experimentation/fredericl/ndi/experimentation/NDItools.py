from .comboboxModel import ComboboxModel
import NDIlib as ndi
import carb.profiler
import logging
import time
from typing import List
import omni.ui
import numpy as np


class NDIData():
    def __init__(self, source: str, active: bool = False):
        self._source = source
        self._active = active
        self._on_value_changed_fn = None

    def get_source(self) -> str:
        return self._source

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool = True):
        self._active = active
        if self._on_value_changed_fn is not None:
            self._on_value_changed_fn()

    def set_active_value_changed_fn(self, fn):
        self._on_value_changed_fn = fn


class NDItools():
    NONE_DATA = NDIData(ComboboxModel.NONE_VALUE)
    PROXY_DATA = NDIData(ComboboxModel.PROXY_VALUE, True)

    def find_ndi_sources() -> List[str]:
        if not ndi.initialize():
            return []

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            return []

        if not ndi.find_wait_for_sources(ndi_find, 5000):
            return []
        sources = ndi.find_get_current_sources(ndi_find)

        result = [s.ndi_name for s in sources]

        ndi.find_destroy(ndi_find)
        ndi.destroy()
        return result

    def find_ndi_sources_long(seconds: int = 10) -> List[str]:
        if not ndi.initialize():
            return []

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            return []

        timeout = time.time() + 10
        changed = True
        while changed and time.time() < timeout:
            if not ndi.find_wait_for_sources(ndi_find, 5000):
                # print("No change to the sources found.")
                changed = False
                continue
            sources = ndi.find_get_current_sources(ndi_find)
            # print("Network sources (%s found)." % len(sources))
            # for i, s in enumerate(sources):
            #    print('%s. %s' % (i + 1, s.ndi_name))

        result = [s.ndi_name for s in sources]

        ndi.find_destroy(ndi_find)
        ndi.destroy()
        return result

    def get_name_from_ndi_name(ndi_name):
        return ndi_name.split("(")[0].strip()


class NDIVideoStream():
    def __init__(self, name: str, stream_uri: str):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False
        self._dynamic_texture = omni.ui.DynamicTextureProvider(name)

        if not ndi.initialize():
            return

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            return 0

        sources = []
        source = None
        timeout = time.time() + 10
        while source is None and time.time() < timeout:
            ndi.find_wait_for_sources(ndi_find, 1000)
            sources = ndi.find_get_current_sources(ndi_find)

            source_candidates = [s for s in sources if s.ndi_name == stream_uri]
            if len(source_candidates) != 0:
                source = source_candidates[0]

        if source is None:
            logger = logging.getLogger(__name__)
            logger.error(f"TIMEOUT: Could not find source at \"{stream_uri}\".")
            return

        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA

        self._ndi_recv = ndi.recv_create_v3(recv_create_desc)
        if self._ndi_recv is None:
            return 0

        ndi.recv_connect(self._ndi_recv, source)
        ndi.find_destroy(ndi_find)

        self.fps = 120
        self._last_read = time.time()
        self.is_ok = True

    def destroy(self):
        super.destroy()
        ndi.recv_destroy(self._ndi_recv)
        ndi.destroy()

    @carb.profiler.profile
    def update(self):
        now = time.time()
        time_delta = now - self._last_read
        if (time_delta < 1.0 / self.fps):
            return
        self._last_read = now

        t, v, _, _ = ndi.recv_capture_v2(self._ndi_recv, 5000)

        if t == ndi.FRAME_TYPE_VIDEO:
            self.fps = v.frame_rate_N / v.frame_rate_D
            # print(v.FourCC) = FourCCVideoType.FOURCC_VIDEO_TYPE_BGRA, might indicate omni.ui.TextureFormat
            frame = v.data
            height, width, _ = frame.shape
            self._dynamic_texture.set_bytes_data(frame.flatten().tolist(), [width, height],
                                                 omni.ui.TextureFormat.BGRA8_UNORM)
            ndi.recv_free_video_v2(self._ndi_recv, v)


class NDIVideoStreamProxy(NDIVideoStream):
    def __init__(self, name: str, stream_uri: str):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False
        self._dynamic_texture = omni.ui.DynamicTextureProvider(name)

        w = 1920
        h = 1080
        c = np.array([255, 0, 0, 255], np.uint8)
        frame = np.full((h, w, len(c)), c, dtype=np.uint8)
        self._frame = frame
        self._width = w
        self._height = h

        self.fps = 30
        self._last_read = time.time()
        self.is_ok = True

    def destroy(self):
        super.destroy()

    @carb.profiler.profile
    def update(self):
        now = time.time()
        time_delta = now - self._last_read
        if (time_delta < 1.0 / self.fps):
            return
        self._last_read = now

        self._dynamic_texture.set_bytes_data(self._frame.flatten().tolist(), [self._width, self._height],
                                             omni.ui.TextureFormat.RGBA8_UNORM)
