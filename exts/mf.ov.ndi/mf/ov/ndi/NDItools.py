from .comboboxModel import ComboboxModel
import NDIlib as ndi
import carb.profiler
import logging
import time
from typing import List
import omni.ui
import numpy as np
import threading


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


class NDIfinder():
    SLEEP_INTERVAL: float = 2  # seconds

    def __init__(self, on_sources_changed):
        self._on_sources_changed = on_sources_changed
        self._previous_sources: List[str] = []

        self._is_running = True
        self._thread = threading.Thread(target=self._search)
        self._thread.setDaemon(True)
        self._thread.start()

    def _search(self):
        logger = logging.getLogger(__name__)

        if not ndi.initialize():
            logger.error("Could not initialize ndi")
            return

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            logger.error("Could not initialize ndi find")
            return

        while self._is_running:
            sources = ndi.find_get_current_sources(ndi_find)
            result = [s.ndi_name for s in sources]
            delta = set(result) ^ set(self._previous_sources)
            if len(delta) > 0:
                self._previous_sources = result
                self._on_sources_changed(result)
            time.sleep(NDIfinder.SLEEP_INTERVAL)

        ndi.find_destroy(ndi_find)
        ndi.destroy()

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None


class NDItools():
    NONE_DATA = NDIData(ComboboxModel.NONE_VALUE)
    PROXY_DATA = NDIData(ComboboxModel.PROXY_VALUE, True)


class NDIVideoStream():
    def __init__(self, name: str, stream_uri: str, lowbandwidth: bool):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False
        self._dynamic_texture = omni.ui.DynamicTextureProvider(name)
        self._thread: threading.Thread

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

        if lowbandwidth:
            recv_create_desc = self.get_recv_low_bandwidth()
        else:
            recv_create_desc = self.get_recv_high_bandwidth()

        self._ndi_recv = ndi.recv_create_v3(recv_create_desc)
        if self._ndi_recv is None:
            return 0

        ndi.recv_connect(self._ndi_recv, source)
        ndi.find_destroy(ndi_find)

        self.fps = 120  # high value so we can fetch the real value when we receive the first video frame
        self._last_read = time.time()

        self._no_frame_chances = 5

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture)
        self._thread.daemon = True
        self._thread.start()

        self.is_ok = True

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None
        ndi.recv_destroy(self._ndi_recv)
        ndi.destroy()

    def get_recv_high_bandwidth(self):
        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        # defaults to BANDWIDTH_HIGHEST
        return recv_create_desc

    def get_recv_low_bandwidth(self):
        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create_desc.bandwidth = ndi.RECV_BANDWIDTH_LOWEST
        return recv_create_desc

    @carb.profiler.profile
    def _update_texture(self):
        while self._is_running:
            now = time.time()
            time_delta = now - self._last_read
            if (time_delta < 1.0 / self.fps):
                continue
            self._last_read = now

            t, v, _, _ = ndi.recv_capture_v2(self._ndi_recv, 1000)

            if t == ndi.FRAME_TYPE_VIDEO:
                self.fps = v.frame_rate_N / v.frame_rate_D
                # print(v.FourCC) = FourCCVideoType.FOURCC_VIDEO_TYPE_BGRA, might indicate omni.ui.TextureFormat
                frame = v.data
                frame[..., :3] = frame[..., 2::-1]  # BGRA to RGBA (Could be done in shader?)
                height, width, channels = frame.shape
                self._dynamic_texture.set_data_array(frame, [width, height, channels])
                ndi.recv_free_video_v2(self._ndi_recv, v)

            if t == ndi.FRAME_TYPE_NONE:
                self._no_frame_chances -= 1
                if (self._no_frame_chances <= 0):
                    self._is_running = False
            else:
                self._no_frame_chances = 5


class NDIVideoStreamProxy(NDIVideoStream):
    def __init__(self, name: str, stream_uri: str, fps: float, lowbandwidth: bool):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False
        self._dynamic_texture = omni.ui.DynamicTextureProvider(name)

        denominator = 1
        if lowbandwidth:
            denominator = 3

        w = int(1920 / denominator)
        h = int(1080 / denominator)
        c = np.array([255, 0, 0, 255], np.uint8)
        frame = np.full((h, w, len(c)), c, dtype=np.uint8)
        self._frame = frame

        self.fps = fps
        self._last_read = time.time()

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture)
        self._thread.daemon = True
        self._thread.start()

        self.is_ok = True

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None

    @carb.profiler.profile
    def update_texture(self):
        while self._is_running:
            now = time.time()
            time_delta = now - self._last_read
            if (time_delta < 1.0 / self.fps):
                continue
            self._last_read = now

            height, width, channels = self._frame.shape
            self._dynamic_texture.set_data_array(self._frame, [width, height, channels])
