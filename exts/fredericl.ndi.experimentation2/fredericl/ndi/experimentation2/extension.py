from .NDItools import NDIVideoStream
from .window import NDIWindow
import omni.ext
import omni.ui as ui
import omni.kit.app
# import cv2 as cv
# import numpy as np
import carb
import carb.profiler
# import time
from typing import List
from functools import partial
import asyncio


"""
class OpenCvVideoStream():
    def __init__(self, name: str, stream_uri: str):
        self.name = name
        self.uri = stream_uri
        self._video_capture = cv.VideoCapture(stream_uri)
        self.fps: float = self._video_capture.get(cv.CAP_PROP_FPS)
        self.width: int = self._video_capture.get(cv.CAP_PROP_FRAME_WIDTH)
        self.height: int = self._video_capture.get(cv.CAP_PROP_FRAME_HEIGHT)
        self._dynamic_texture = omni.ui.DynamicTextureProvider(name)
        self._last_read = time.time()
        self.is_ok = self._video_capture.isOpened()
        if self.fps == 0:
            self.fps = 24

    @carb.profiler.profile
    def update(self):
        now = time.time()
        time_delta = now - self._last_read
        if (time_delta < 1.0/self.fps):
            return
        self._last_read = now

        ret, frame = self._video_capture.read()
        if not ret:
            return

        frame: np.ndarray
        frame = cv.cvtColor(frame, cv.COLOR_BGR2BGRA)
        height, width, channels = frame.shape
        self._dynamic_texture.set_bytes_data(frame.flatten().tolist(), [width, height],
                                             omni.ui.TextureFormat.BGRA8_UNORM)
"""


class FredericlNdiExperimentation2Extension(omni.ext.IExt):
    WINDOW_NAME = "NDI Connect 2"
    MENU_PATH = f"Window/{WINDOW_NAME}"

    def on_startup(self, ext_id):
        stream = omni.kit.app.get_app().get_update_event_stream()
        self._sub = stream.create_subscription_to_pop(self._on_update, name="update")
        self._streams: List[NDIVideoStream] = []

        ui.Workspace.set_show_window_fn(
            FredericlNdiExperimentation2Extension.WINDOW_NAME, partial(self.show_window, None)
        )

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                FredericlNdiExperimentation2Extension.MENU_PATH, self.show_window, toggle=True, value=True
            )

        ui.Workspace.show_window(FredericlNdiExperimentation2Extension.WINDOW_NAME)

    def _add_stream(self, name, uri) -> bool:
        video_stream = NDIVideoStream(name, uri)
        if not video_stream.is_ok:
            carb.log_error(f"Error opening stream: {uri}")
            return False
        self._streams.append(video_stream)
        return True

    def _remove_streams(self):
        self._streams = []
        print("Streams reset")

    @carb.profiler.profile
    def _on_update(self, e):
        for stream in self._streams:
            stream.update()

    def on_shutdown(self):
        self._sub.unsubscribe()
        self._streams = []

        self._menu = None
        if self._window:
            self._window.destroy()
            self._window = None

        ui.Workspace.set_show_window_fn(FredericlNdiExperimentation2Extension.WINDOW_NAME, None)

    def _set_menu(self, value):
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(FredericlNdiExperimentation2Extension.MENU_PATH, value)

    async def _destroy_window_async(self):
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _visibility_changed_fn(self, visible):
        self._set_menu(visible)
        if not visible:
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, menu, value):
        if value:
            self._window = NDIWindow(self._add_stream, self._remove_streams,
                                     FredericlNdiExperimentation2Extension.WINDOW_NAME, width=800, height=200)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
        elif self._window:
            self._window.visible = False
