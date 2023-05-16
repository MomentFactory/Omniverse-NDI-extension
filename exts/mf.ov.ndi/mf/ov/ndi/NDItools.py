from .eventsystem import EventSystem

import carb.profiler
import logging
import NDIlib as ndi
import numpy as np
import omni.ui
import threading
import time
from typing import List


class NDItools():
    def __init__(self):
        self._ndi_ok = False
        self._ndi_find = None

        self._ndi_init()
        self._ndi_find_init()

        self._finder = None
        self._create_finder()

        self._streams = []

        stream = omni.kit.app.get_app().get_update_event_stream()
        self._sub = stream.create_subscription_to_pop(self._on_update, name="update")

    def destroy(self):
        self._sub.unsubscribe()
        self._sub = None

        self._finder.destroy()

        for stream in self._streams:
            stream.destroy()
        self._streams.clear()

        if self._ndi_ok:
            if self._ndi_find is not None:
                ndi.find_destroy(self._ndi_find)
            ndi.destroy()
        self._ndi_ok = False

    def is_ndi_ok(self) -> bool:
        return self._ndi_ok

    def _on_update(self, e):
        to_remove = []
        for stream in self._streams:
            if not stream.is_running():
                to_remove.append(stream)

        for stream in to_remove:
            self._streams.remove(stream)
            EventSystem.send_event(EventSystem.STREAM_STOP_TIMEOUT_EVENT, payload={"dynamic_id": stream.get_id()})
            stream.destroy()

    def _ndi_init(self):
        if not ndi.initialize():
            logger = logging.getLogger(__name__)
            logger.error("Could not initialize NDI®")
            return
        self._ndi_ok = True

    def _ndi_find_init(self):
        self._ndi_find = ndi.find_create_v2()
        if self._ndi_find is None:
            logger = logging.getLogger(__name__)
            logger.error("Could not initialize NDI® find")
            return

    def _create_finder(self):
        if self._ndi_find:
            self._finder = NDIfinder(self)

    def get_ndi_find(self):
        return self._ndi_find

    def get_stream(self, dynamic_id):
        return next((x for x in self._streams if x.get_id() == dynamic_id), None)

    def try_add_stream(self, dynamic_id: str, ndi_source: str, lowbandwidth: bool,
                       update_fps_fn, update_dimensions_fn) -> bool:
        stream: NDIVideoStream = NDIVideoStream(dynamic_id, ndi_source, lowbandwidth, self,
                                                update_fps_fn, update_dimensions_fn)
        if not stream.is_ok:
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening stream: {ndi_source}")
            return False

        self._streams.append(stream)
        return True

    def try_add_stream_proxy(self, dynamic_id: str, ndi_source: str, fps: float,
                             lowbandwidth: bool, update_fps_fn, update_dimensions_fn) -> bool:
        stream: NDIVideoStreamProxy = NDIVideoStreamProxy(dynamic_id, ndi_source, fps, lowbandwidth,
                                                          update_fps_fn, update_dimensions_fn)
        if not stream.is_ok:
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening stream: {ndi_source}")
            return False

        self._streams.append(stream)
        return True

    def stop_stream(self, dynamic_id: str):
        stream = self.get_stream(dynamic_id)
        if stream is not None:
            self._streams.remove(stream)
            stream.destroy()

    def stop_all_streams(self):
        for stream in self._streams:
            stream.destroy()
        self._streams.clear()


class NDIfinder():
    SLEEP_INTERVAL: float = 2  # seconds

    def __init__(self, tools: NDItools):
        self._tools = tools
        self._previous_sources: List[str] = []

        self._is_running = True
        self._thread = threading.Thread(target=self._search)
        self._thread.start()

    def destroy(self):
        self._is_running = False
        self._thread.join()
        self._thread = None

    def _search(self):
        find = self._tools.get_ndi_find()
        if find:
            while self._is_running:
                sources = ndi.find_get_current_sources(find)
                result = [s.ndi_name for s in sources]
                delta = set(result) ^ set(self._previous_sources)
                if len(delta) > 0:
                    self._previous_sources = result
                    EventSystem.send_event(EventSystem.NDIFINDER_NEW_SOURCES, payload={"sources": result})
                time.sleep(NDIfinder.SLEEP_INTERVAL)
        self._is_running = False


class NDIVideoStream():
    NO_FRAME_TIMEOUT = 5  # seconds

    def __init__(self, dynamic_id: str, ndi_source: str, lowbandwidth: bool, tools: NDItools,
                 update_fps_fn, update_dimensions_fn):
        self._dynamic_id = dynamic_id
        self._ndi_source = ndi_source
        self._lowbandwidth = lowbandwidth
        self._thread: threading.Thread = None
        self._ndi_recv = None

        self._update_fps_fn = update_fps_fn
        self._fps_current = 0.0
        self._fps_avg_total = 0.0
        self._fps_avg_count = 0
        self._fps_expected = 0.0
        self._update_dimensions_fn = update_dimensions_fn

        self.is_ok = False

        if not tools.is_ndi_ok():
            return

        ndi_find = tools.get_ndi_find()
        source = None
        sources = ndi.find_get_current_sources(ndi_find)
        source_candidates = [s for s in sources if s.ndi_name == self._ndi_source]
        if len(source_candidates) != 0:
            source = source_candidates[0]

        if source is None:
            logger = logging.getLogger(__name__)
            logger.error(f"TIMEOUT: Could not find source at \"{self._ndi_source}\".")
            return

        if lowbandwidth:
            recv_create_desc = self.get_recv_low_bandwidth()
        else:
            recv_create_desc = self.get_recv_high_bandwidth()

        self._ndi_recv = ndi.recv_create_v3(recv_create_desc)
        if self._ndi_recv is None:
            logger = logging.getLogger(__name__)
            logger.error("Could not create NDI® receiver")
            return

        ndi.recv_connect(self._ndi_recv, source)

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture, args=(self._dynamic_id, ))
        self._thread.start()

        self.is_ok = True

    def _update_fps(self):
        self._update_fps_fn(self._fps_current, self._fps_avg_total / self._fps_avg_count, self._fps_expected)

    def destroy(self):
        self._update_fps()
        self._is_running = False
        self._thread.join()
        self._thread = None
        ndi.recv_destroy(self._ndi_recv)

    def get_id(self) -> str:
        return self._dynamic_id

    def is_running(self) -> bool:
        return self._is_running

    def get_recv_high_bandwidth(self):
        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create_desc.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
        return recv_create_desc

    def get_recv_low_bandwidth(self):
        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create_desc.bandwidth = ndi.RECV_BANDWIDTH_LOWEST
        return recv_create_desc

    @carb.profiler.profile
    def _update_texture(self, dynamic_id: str):
        carb.profiler.begin(0, 'Omniverse NDI®::Init')
        dynamic_texture = omni.ui.DynamicTextureProvider(dynamic_id)

        last_read = time.time() - 1  # Make sure we run on the first frame
        fps = 120.0
        no_frame_chances = NDIVideoStream.NO_FRAME_TIMEOUT * fps
        index = 0

        self._fps_avg_total = 0.0
        self._fps_avg_count = 0

        carb.profiler.end(0)
        while self._is_running:
            carb.profiler.begin(1, 'Omniverse NDI®::loop outer')
            now = time.time()
            time_delta = now - last_read
            if (time_delta < 1.0 / fps):
                carb.profiler.end(1)
                continue
            carb.profiler.begin(2, 'Omniverse NDI®::loop inner')
            self._fps_current = 1.0 / time_delta
            last_read = now

            carb.profiler.begin(3, 'Omniverse NDI®::receive frame')
            t, v, _, _ = ndi.recv_capture_v2(self._ndi_recv, 0)
            carb.profiler.end(3)

            if t == ndi.FRAME_TYPE_VIDEO:
                carb.profiler.begin(4, 'Omniverse NDI®::set_data')
                fps = v.frame_rate_N / v.frame_rate_D
                self._fps_expected = fps
                if (index == 0):
                    self._fps_current = fps
                color_format = v.FourCC
                frame = v.data
                frame[..., :3] = frame[..., 2::-1]  # TODO: BGRA to RGBA (Could be done in shader?)
                height, width, channels = frame.shape
                self._update_dimensions_fn(width, height, str(color_format))
                dynamic_texture.set_data_array(frame, [width, height, channels])
                ndi.recv_free_video_v2(self._ndi_recv, v)
                carb.profiler.end(4)
                self._fps_avg_total += self._fps_current
                self._fps_avg_count += 1
                self._update_fps()
                index += 1

            if t == ndi.FRAME_TYPE_NONE:
                no_frame_chances -= 1
                if (no_frame_chances <= 0):
                    self._is_running = False
            else:
                no_frame_chances = NDIVideoStream.NO_FRAME_TIMEOUT * fps

            carb.profiler.end(2)
            carb.profiler.end(1)


class NDIVideoStreamProxy():
    def __init__(self, dynamic_id: str, ndi_source: str, fps: float, lowbandwidth: bool,
                 fps_update_fn, update_dimensions_fn):
        self._dynamic_id = dynamic_id
        self._ndi_source = ndi_source
        self._fps = fps
        self._lowbandwidth = lowbandwidth
        self._thread: threading.Thread = None

        self._update_fps_fn = fps_update_fn
        self._fps_current = 0.0
        self._fps_avg_total = 0.0
        self._fps_avg_count = 0
        self._fps_expected = 0.0
        self._update_dimensions_fn = update_dimensions_fn

        self.is_ok = False

        denominator = 1
        if lowbandwidth:
            denominator = 3
        w = int(1920 / denominator)  # TODO: dimensions from name like for fps
        h = int(1080 / denominator)

        self._is_running = True
        self._thread = threading.Thread(target=self._update_texture, args=(self._dynamic_id, self._fps, w, h, ))
        self._thread.start()

        self.is_ok = True

    def _update_fps(self):
        self._update_fps_fn(self._fps_current, self._fps_avg_total / self._fps_avg_count, self._fps_expected)

    def destroy(self):
        self._update_fps()
        self._is_running = False
        self._thread.join()
        self._thread = None

    def get_id(self) -> str:
        return self._dynamic_id

    def is_running(self) -> bool:
        return self._is_running

    @carb.profiler.profile
    def _update_texture(self, dynamic_id: str, fps: float, width: float, height: float):
        carb.profiler.begin(0, 'Omniverse NDI®::Init')
        color = np.array([255, 0, 0, 255], np.uint8)
        channels = len(color)
        dynamic_texture = omni.ui.DynamicTextureProvider(dynamic_id)
        frame = np.full((height, width, channels), color, dtype=np.uint8)

        last_read = time.time() - 1
        self._fps_avg_total = 0.0
        self._fps_avg_count = 0
        self._fps_expected = fps
        carb.profiler.end(0)
        while self._is_running:
            carb.profiler.begin(1, 'Omniverse NDI®::Proxy loop outer')
            now = time.time()
            time_delta = now - last_read
            if (time_delta < 1.0 / fps):
                carb.profiler.end(1)
                continue
            carb.profiler.begin(2, 'Omniverse NDI®::Proxy loop inner')
            self._fps_current = 1.0 / time_delta
            self._fps_avg_total += self._fps_current
            self._fps_avg_count += 1
            self._update_fps()
            last_read = now

            carb.profiler.begin(3, 'Omniverse NDI®::set_data')
            dynamic_texture.set_data_array(frame, [width, height, channels])
            carb.profiler.end(3)

            carb.profiler.end(2)
            carb.profiler.end(1)
