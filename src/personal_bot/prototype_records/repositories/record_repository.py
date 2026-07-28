from personal_bot.prototype_records.entities.record import Record
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError, DuplicateNameError


class RecordRepository:
    def __init__(self) -> None:
        self._records: dict[int, Record] = {}
        self._next_id = 1

    def list_by_folder(self, folder_id: int, owner_user_id: int) -> list[Record]:
        return [
            record
            for record in self._records.values()
            if record.folder_id == folder_id and record.owner_user_id == owner_user_id
        ]

    def get(self, record_id: int, owner_user_id: int) -> Record | None:
        record = self._records.get(record_id)
        return record if record is not None and record.owner_user_id == owner_user_id else None

    def create(self, owner_user_id: int, folder_id: int, name: str, sort_order: int, created_at: str, updated_at: str) -> Record:
        if any(
            record.owner_user_id == owner_user_id and record.folder_id == folder_id and record.name == name
            for record in self._records.values()
        ):
            raise DuplicateNameError(f"Record with name '{name}' already exists in folder")

        record = Record(
            id=self._next_id,
            owner_user_id=owner_user_id,
            folder_id=folder_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._records[self._next_id] = record
        self._next_id += 1
        return record

    def update_name(self, record_id: int, owner_user_id: int, name: str, updated_at: str) -> Record:
        record = self.get(record_id, owner_user_id)
        if record is None:
            raise EntityNotFoundError("Record not found")
        updated = Record(
            id=record.id,
            owner_user_id=record.owner_user_id,
            folder_id=record.folder_id,
            name=name,
            created_at=record.created_at,
            updated_at=updated_at,
        )
        self._records[record_id] = updated
        return updated

    def delete(self, record_id: int, owner_user_id: int) -> None:
        record = self.get(record_id, owner_user_id)
        if record is None:
            raise EntityNotFoundError("Record not found")
        del self._records[record_id]

    def next_sort_order(self, folder_id: int, owner_user_id: int) -> int:
        records = self.list_by_folder(folder_id, owner_user_id)
        return max((record.sort_order for record in records), default=0) + 1
