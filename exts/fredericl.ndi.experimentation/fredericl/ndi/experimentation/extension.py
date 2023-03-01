from .window import NDIWindow
# import omni.ui as ui
# from functools import partial
import omni.ext
import omni.kit.app
import asyncio


class FredericlNdiExperimentationExtension(omni.ext.IExt):
    MENU_PATH = f"Window/{NDIWindow.WINDOW_NAME}"

    def on_startup(self, ext_id):
        # ui.Workspace.set_show_window_fn(NDIWindow.WINDOW_NAME, partial(self.show_window, None))
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                FredericlNdiExperimentationExtension.MENU_PATH, self.show_window, toggle=True, value=True
            )

        # ui.Workspace.show_window(NDIWindow.WINDOW_NAME)
        self.show_window(None, True)

    def on_shutdown(self):
        self._menu = None
        self._window.destroy()
        self._window = None
        # ui.Workspace.set_show_window_fn(NDIWindow.WINDOW_NAME, None)

    def _set_menu(self, visible):
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(FredericlNdiExperimentationExtension.MENU_PATH, visible)

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
            self._window = NDIWindow(width=800, height=240)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
        elif self._window:
            self._window.destroy()
            self._window = None
