import omni.ui as ui
from typing import List


class ComboboxItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)

    def value(self):
        return self.model.get_value_as_string()


class ComboboxModel(ui.AbstractItemModel):
    NONE = ComboboxItem("NONE")
    items: List[str] = [NONE]
    watchers = []

    @staticmethod
    def clearAllItems():
        ComboboxModel.items = []
        ComboboxModel._notify()

    @staticmethod
    def AddItem(text: str):
        ComboboxModel.items.append(ComboboxItem(text))
        ComboboxModel._notify()

    @staticmethod
    def _notify():
        for watcher in ComboboxModel.watchers:
            watcher._item_changed(None)

    @staticmethod
    def ResetWatchers():
        ComboboxModel.watchers = []

    def __init__(self, name: str, model):
        super().__init__()

        self._model = model
        self._name = name

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(
            lambda a: self._current_index_changed_fn()
        )

        self._current_index_changed_fn()

        ComboboxModel.watchers.append(self)

    def _current_index_changed_fn(self):
        self._item_changed(None), self._model.set_binding(self._name, self.currentvalue())

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
