from .window import Window

import asyncio
import omni.ext
import omni.kit.app
import omni.kit.ui


class MFOVNdiExtension(omni.ext.IExt):
    MENU_PATH = f"Window/{Window.WINDOW_NAME}"

    def on_startup(self, _):
        self._menu = None
        self._window: Window = None

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                MFOVNdiExtension.MENU_PATH, self._show_window, toggle=True, value=True
            )

        self._show_window(None, True)

    def on_shutdown(self):
        if self._menu:
            self._menu = None
        if self._window:
            self._destroy_window()

    def _destroy_window(self):
        self._window.destroy()
        self._window = None

    def _set_menu(self, visible):
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(MFOVNdiExtension.MENU_PATH, visible)

    async def _destroy_window_async(self):
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._destroy_window()

    def _visibility_changed_fn(self, visible):
        self._set_menu(visible)
        if not visible:
            asyncio.ensure_future(self._destroy_window_async())

    def _show_window(self, menu, value):
        if value:
            self._window = Window(width=800, height=275)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
        elif self._window:
            self._destroy_window()
