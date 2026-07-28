from personal_bot.prototype_records.entities.data_item import DataItem
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError


class DataItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, DataItem] = {}
        self._next_id = 1

    def list_by_record(self, record_id: int) -> list[DataItem]:
        return [item for item in self._items.values() if item.record_id == record_id]

    def get(self, data_item_id: int, record_id: int) -> DataItem | None:
        item = self._items.get(data_item_id)
        return item if item is not None and item.record_id == record_id else None

    def create(self, record_id: int, name: str, type: str, value: object, sort_order: int, created_at: str, updated_at: str) -> DataItem:
        item = DataItem(
            id=self._next_id,
            record_id=record_id,
            name=name,
            type=type,
            value=value,
            sort_order=sort_order,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def delete(self, data_item_id: int, record_id: int) -> None:
        item = self.get(data_item_id, record_id)
        if item is None:
            raise EntityNotFoundError("DataItem not found")
        del self._items[data_item_id]

    def next_sort_order(self, record_id: int) -> int:
        items = self.list_by_record(record_id)
        return max((item.sort_order for item in items), default=0) + 1
