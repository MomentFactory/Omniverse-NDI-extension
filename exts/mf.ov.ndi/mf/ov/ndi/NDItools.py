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


class NDItools():
    NONE_DATA = NDIData(ComboboxModel.NONE_VALUE)
    PROXY_DATA = NDIData(ComboboxModel.PROXY_VALUE, True)

    def __init__(self):
        self._ndi_ok = False
        self._ndi_find = None

    def ndi_init(self):
        if not ndi.initialize():
            logger = logging.getLogger(__name__)
            logger.error("Could not initialize ndi")
            return
        self._ndi_ok = True

    def ndi_find_init(self):
        self._ndi_find = ndi.find_create_v2()
        if self._ndi_find is None:
            self._is_running = False
            logger = logging.getLogger(__name__)
            logger.error("Could not initialize ndi find")
            ndi.destroy()
            self._ndi_ok = False
            return

    def get_ndi_find(self):
        return self._ndi_find

    def is_ndi_ok(self):
        return self._ndi_ok

    def destroy(self):
        if self._ndi_ok:
            if self._ndi_find is not None:
                ndi.find_destroy(self._ndi_find)
            ndi.destroy()
        self._ndi_ok = False


class NDIfinder():
    SLEEP_INTERVAL: float = 2  # seconds

    def __init__(self, on_sources_changed, tools: NDItools):
        self._on_sources_changed = on_sources_changed
        self._previous_sources: List[str] = []

        if tools.is_ndi_ok():
            self._is_running = True
            self._ndi_find = tools.get_ndi_find()
            self._thread = threading.Thread(target=self._search)
            self._thread.start()

    def _search(self):
        if self._ndi_find is not None:
            while self._is_running:
                sources = ndi.find_get_current_sources(self._ndi_find)
                result = [s.ndi_name for s in sources]
                delta = set(result) ^ set(self._previous_sources)
                if len(delta) > 0:
                    self._previous_sources = result
                    self._on_sources_changed(result)
                time.sleep(NDIfinder.SLEEP_INTERVAL)

    def destroy(self):
        if self._is_running:
            self._is_running = False
            self._thread.join()
            self._thread = None


class NDIVideoStream():
    NO_FRAME_TIMEOUT = 5  # seconds

    def __init__(self, name: str, stream_uri: str, lowbandwidth: bool, tools: NDItools):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False
        self._thread: threading.Thread

        if not tools.is_ndi_ok():
            return

        ndi_find = tools.get_ndi_find()
        source = None
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
            logger = logging.getLogger(__name__)
            logger.error("Could not create ndi receiver")
            return

        ndi.recv_connect(self._ndi_recv, source)

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture, args=(name, ))
        self._thread.start()

        self.is_ok = True

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None
        ndi.recv_destroy(self._ndi_recv)

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
    def _update_texture(self, name: str):
        carb.profiler.begin(0, 'Omniverse NDI®::Init')
        dynamic_texture = omni.ui.DynamicTextureProvider(name)

        last_read = time.time() - 1  # Make sure we run on the first frame
        fps = 120.0
        no_frame_chances = NDIVideoStream.NO_FRAME_TIMEOUT * fps

        carb.profiler.end(0)
        while self._is_running:
            carb.profiler.begin(1, 'Omniverse NDI®::loop outer')
            now = time.time()
            time_delta = now - last_read
            if (time_delta < 1.0 / fps):
                carb.profiler.end(1)
                continue
            carb.profiler.begin(2, 'Omniverse NDI®::loop inner')
            last_read = now

            carb.profiler.begin(3, 'Omniverse NDI®::receive frame')
            t, v, _, _ = ndi.recv_capture_v2(self._ndi_recv, 0)
            carb.profiler.end(3)

            if t == ndi.FRAME_TYPE_VIDEO:
                carb.profiler.begin(4, 'Omniverse NDI®::set_data')
                fps = v.frame_rate_N / v.frame_rate_D
                # print(v.FourCC) = FourCCVideoType.FOURCC_VIDEO_TYPE_BGRA, might indicate omni.ui.TextureFormat
                frame = v.data
                frame[..., :3] = frame[..., 2::-1]  # BGRA to RGBA (Could be done in shader?)
                height, width, channels = frame.shape
                dynamic_texture.set_data_array(frame, [width, height, channels])
                ndi.recv_free_video_v2(self._ndi_recv, v)
                carb.profiler.end(4)

            if t == ndi.FRAME_TYPE_NONE:
                no_frame_chances -= 1
                if (no_frame_chances <= 0):
                    self._is_running = False
            else:
                no_frame_chances = NDIVideoStream.NO_FRAME_TIMEOUT * fps

            carb.profiler.end(2)
            carb.profiler.end(1)

class NDIVideoStreamProxy():
    def __init__(self, name: str, stream_uri: str, fps: float, lowbandwidth: bool):
        self.name = name
        self.uri = stream_uri
        self.is_ok = False

        denominator = 1
        if lowbandwidth:
            denominator = 3
        w = int(1920 / denominator)
        h = int(1080 / denominator)

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture, args=(name, fps, w, h, ))
        self._thread.start()

        self.is_ok = True

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None

    @carb.profiler.profile
    def _update_texture(self, name: str, fps: float, width: float, height: float):
        carb.profiler.begin(0, 'Omniverse NDI®::Init')
        color = np.array([255, 0, 0, 255], np.uint8)
        channels = len(color)
        dynamic_texture = omni.ui.DynamicTextureProvider(name)
        frame = np.full((height, width, channels), color, dtype=np.uint8)

        last_read = time.time() - 1  # Make sure we run on the first frame
        carb.profiler.end(0)
        while self._is_running:
            carb.profiler.begin(1, 'Omniverse NDI®::Proxy loop outer')
            now = time.time()
            time_delta = now - last_read
            if (time_delta < 1.0 / fps):
                carb.profiler.end(1)
                continue
            carb.profiler.begin(2, 'Omniverse NDI®::Proxy loop inner')
            last_read = now

            carb.profiler.begin(3, 'Omniverse NDI®::set_data')
            dynamic_texture.set_data_array(frame, [width, height, channels])
            carb.profiler.end(3)
            carb.profiler.end(2)
            carb.profiler.end(1)
