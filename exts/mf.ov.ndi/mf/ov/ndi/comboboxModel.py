from .eventsystem import EventSystem

import omni.ui as ui
from typing import List


class ComboboxItem(ui.AbstractItem):
    def __init__(self, value: str):
        super().__init__()
        self.model = ui.SimpleStringModel(value)

    def value(self):
        return self.model.get_value_as_string()


class ComboboxModel(ui.AbstractItemModel):
    NONE_VALUE = "NONE"
    PROXY_VALUE = "PROXY (1080p30) - RED"

    def __init__(self, items: List[str], selected: str, name: str, index: int):
        super().__init__()
        self._name = name
        self._index = index

        # minimal model implementation
        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(lambda a: self._current_index_changed_fn())

        self.set_items_and_current(items, selected)

    def _current_index_changed_fn(self):
        self._item_changed(None)
        EventSystem.send_event(EventSystem.COMBOBOX_CHANGED_EVENT,
                               payload={"id": self._name, "index": self._index, "value": self._current_value()})

    def set_items_and_current(self, items: List[str], current: str):
        self._items = [ComboboxItem(text) for text in items]
        self._set_current_from_value(current)

    def _set_current_from_value(self, current: str):
        index = next((i for i, item in enumerate(self._items) if item.value() == current), 0)
        self._current_index.set_value(index)
        self._item_changed(None)

    def _current_value(self) -> str:
        current_item = self._items[self._current_index.get_value_as_int()]
        return current_item.value()

    # minimal model implementation
    def get_item_children(self, item):
        return self._items

    # minimal model implementation
    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model
