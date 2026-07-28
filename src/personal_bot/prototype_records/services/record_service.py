from datetime import datetime, timezone

from personal_bot.prototype_records.entities.record import Record
from personal_bot.prototype_records.entities.data_item import DataItem
from personal_bot.prototype_records.entities.reminder import Reminder
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError
from personal_bot.prototype_records.exceptions.validation import ValidationError
from personal_bot.prototype_records.repositories.data_item_repository import DataItemRepository
from personal_bot.prototype_records.repositories.folder_repository import FolderRepository
from personal_bot.prototype_records.repositories.record_repository import RecordRepository
from personal_bot.prototype_records.repositories.reminder_repository import ReminderRepository


class PrototypeRecordService:
    def __init__(
        self,
        folder_repository: FolderRepository,
        record_repository: RecordRepository,
        data_item_repository: DataItemRepository,
        reminder_repository: ReminderRepository,
    ) -> None:
        self._folder_repository = folder_repository
        self._record_repository = record_repository
        self._data_item_repository = data_item_repository
        self._reminder_repository = reminder_repository

    def create_record(self, owner_user_id: int, folder_id: int, name: str) -> Record:
        folder = self._folder_repository.get(folder_id, owner_user_id)
        if folder is None:
            raise EntityNotFoundError("Folder not found")
        if not name.strip():
            raise ValidationError("Record name is required")
        now = datetime.now(timezone.utc).isoformat()
        return self._record_repository.create(
            owner_user_id=owner_user_id,
            folder_id=folder_id,
            name=name,
            sort_order=self._record_repository.next_sort_order(folder_id, owner_user_id),
            created_at=now,
            updated_at=now,
        )

    def get_record(self, record_id: int, owner_user_id: int) -> Record:
        record = self._record_repository.get(record_id, owner_user_id)
        if record is None:
            raise EntityNotFoundError("Record not found")
        return record

    def list_records(self, owner_user_id: int, folder_id: int) -> list[Record]:
        return self._record_repository.list_by_folder(folder_id, owner_user_id)

    def rename_record(self, record_id: int, owner_user_id: int, name: str) -> Record:
        if not name.strip():
            raise ValidationError("Record name is required")
        now = datetime.now(timezone.utc).isoformat()
        return self._record_repository.update_name(record_id, owner_user_id, name, now)

    def delete_record(self, record_id: int, owner_user_id: int) -> None:
        self._record_repository.delete(record_id, owner_user_id)

    def add_data_item(self, owner_user_id: int, record_id: int, name: str, type: str, value: object) -> DataItem:
        record = self._record_repository.get(record_id, owner_user_id)
        if record is None:
            raise EntityNotFoundError("Record not found")
        if not name.strip():
            raise ValidationError("Data item name is required")
        now = datetime.now(timezone.utc).isoformat()
        return self._data_item_repository.create(
            record_id=record_id,
            name=name,
            type=type,
            value=value,
            sort_order=self._data_item_repository.next_sort_order(record_id),
            created_at=now,
            updated_at=now,
        )

    def list_data_items(self, record_id: int) -> list[DataItem]:
        return self._data_item_repository.list_by_record(record_id)

    def delete_data_item(self, data_item_id: int, record_id: int) -> None:
        self._data_item_repository.delete(data_item_id, record_id)

    def add_reminder(self, owner_user_id: int, record_id: int, due_at: str, message: str, data_item_id: int | None = None) -> Reminder:
        record = self._record_repository.get(record_id, owner_user_id)
        if record is None:
            raise EntityNotFoundError("Record not found")
        now = datetime.now(timezone.utc).isoformat()
        return self._reminder_repository.create(
            record_id=record_id,
            data_item_id=data_item_id,
            due_at=due_at,
            message=message,
            created_at=now,
            updated_at=now,
        )

    def list_reminders(self, record_id: int) -> list[Reminder]:
        return self._reminder_repository.list_by_record(record_id)
