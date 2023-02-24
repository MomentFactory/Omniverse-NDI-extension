import omni.ui as ui
from typing import List


class ComboboxItem(ui.AbstractItem):
    def __init__(self, ndi):
        super().__init__()
        self.model = ui.SimpleStringModel(ndi.get_source())
        self._ndi = ndi

    def value(self):
        return self.model.get_value_as_string()

    def is_active(self):
        return self._ndi.is_active()


class ComboboxModel(ui.AbstractItemModel):
    NONE_VALUE = "NONE"
    items: List[ComboboxItem] = []
    watchers = []

    @staticmethod
    def clearAllItems():
        ComboboxModel.items = []
        ComboboxModel._notify()

    @staticmethod
    def AddItem(ndi):
        ComboboxModel.items.append(ComboboxItem(ndi))
        ComboboxModel._notify()

    @staticmethod
    def _notify():
        for watcher in ComboboxModel.watchers:
            watcher._item_changed(None)

    @staticmethod
    def ResetWatchers():
        ComboboxModel.watchers = []

    def __init__(self, name: str, model, value: str, on_change_fn):
        super().__init__()

        self._model = model
        self._name = name
        self._on_change_fn = on_change_fn

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(
            lambda a: self._current_index_changed_fn()
        )

        index = next((i for i, item in enumerate(self.items) if item.value() == value), 0)
        self._current_index.set_value(index)

        ComboboxModel.watchers.append(self)

    def _current_index_changed_fn(self):
        self._model.set_binding(self._name, self.currentvalue())
        self._item_changed(None)
        self._on_change_fn()

    def currentvalue(self):
        self._current_item = ComboboxModel.items[self._current_index.get_value_as_int()]
        return self._current_item.value()

    def currentItem(self):
        self._current_item = ComboboxModel.items[self._current_index.get_value_as_int()]
        return self._current_item

    def getCurrentItemIndex(self):
        return self._current_index.get_value_as_int()

    def get_item_children(self, item):
        return ComboboxModel.items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model

    def append_child_item(self, parentItem, text):
        ComboboxModel.AddItem(text)

    def select_none(self):
        self._current_index.set_value(0)
