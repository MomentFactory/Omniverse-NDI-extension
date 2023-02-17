import NDIlib as ndi
import carb.profiler
import time
import omni.ui
import numpy as np

DEFAULT_STREAM_URI = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"


class NDItools():
    def find_ndi_sources():
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
        # result.insert(0, DEFAULT_STREAM_URI)
        return result

    def find_ndi_sources_long(seconds: int = 10):
        if not ndi.initialize():
            return []

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            return []

        timeout = time.time() + 10
        changed = True
        while changed and time.time() < timeout:
            if not ndi.find_wait_for_sources(ndi_find, 5000):
                print("No change to the sources found.")
                changed = False
                continue
            sources = ndi.find_get_current_sources(ndi_find)
            print("Network sources (%s found)." % len(sources))
            for i, s in enumerate(sources):
                print('%s. %s' % (i + 1, s.ndi_name))

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
            print(f"TIMEOUT: Could not find source at \"{stream_uri}\".")
            return

        recv_create_desc = ndi.RecvCreateV3()
        recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA

        self._ndi_recv = ndi.recv_create_v3(recv_create_desc)
        if self._ndi_recv is None:
            return 0

        ndi.recv_connect(self._ndi_recv, source)
        ndi.find_destroy(ndi_find)

        self.fps = 30
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

        t, v, _, _ = ndi.recv_capture_v2(self._ndi_recv, 5000)  # t (type), v (video), a (audio) _ (?)

        if t == ndi.FRAME_TYPE_VIDEO:
            # print('Video data received (%dx%d).' % (v.xres, v.yres))
            frame = v.data
            height, width, channels = frame.shape
            self._dynamic_texture.set_bytes_data(frame.flatten().tolist(), [width, height],
                                                 omni.ui.TextureFormat.BGRA8_UNORM)
            ndi.recv_free_video_v2(self._ndi_recv, v)

        # if t == ndi.FRAME_TYPE_AUDIO:
        #    print('Audio data received (%d samples).' % a.no_samples)
