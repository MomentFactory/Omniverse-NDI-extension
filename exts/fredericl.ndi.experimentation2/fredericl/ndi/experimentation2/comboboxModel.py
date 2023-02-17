import omni.ui as ui


class ComboboxItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)

    def value(self):
        return self.model.get_value_as_string()


class ComboboxModel(ui.AbstractItemModel):
    def __init__(self):
        super().__init__()

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(
            lambda a: self._item_changed(None)
        )

        self._items = []

    def currentvalue(self):
        self._current_item = self._items[self._current_index.get_value_as_int()]
        return self._current_item.value()

    def currentItem(self):
        self._current_item = self._items[self._current_index.get_value_as_int()]
        return self._current_item

    def getCurrentItemIndex(self):
        return self._current_index.get_value_as_int()

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model

    def append_child_item(self, parentItem, text):
        self._items.append(ComboboxItem(text))
        self._item_changed(None)

    def clearAllItems(self):
        self._items = []
        self._item_changed(None)
