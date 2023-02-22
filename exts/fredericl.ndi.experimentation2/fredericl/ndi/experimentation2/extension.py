from .NDItools import NDIVideoStream
from .window import NDIWindow
import omni.ext
import omni.ui as ui
import omni.kit.app
import carb
import carb.profiler
from typing import List
from functools import partial
import asyncio


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
