from dataclasses import replace
from datetime import datetime, timezone

from personal_bot.core.entities.record import Record
from personal_bot.db.repositories.record_repository import RecordRepository
from personal_bot.records.registry import RecordRegistry
from personal_bot.records.types.base import RecordType


class UnknownRecordTypeError(ValueError):
    pass


class RecordNotFoundError(ValueError):
    pass


class RecordsService:
    def __init__(
        self,
        record_repository: RecordRepository,
        record_registry: RecordRegistry,
    ) -> None:
        self._record_repository = record_repository
        self._record_registry = record_registry

    def create_record(
        self,
        owner_user_id: int,
        folder_id: int,
        type_code: str,
        name: str,
        data: dict[str, object] | None = None,
    ) -> Record:
        record_type = self._get_record_type(type_code)
        initial_data = record_type.create_initial_data()
        record_data = data if data is not None else initial_data
        record_type.validate(record_data)
        payload = record_type.serialize(record_data)
        created_at = datetime.now(timezone.utc).isoformat()

        return self._record_repository.create(
            owner_user_id=owner_user_id,
            folder_id=folder_id,
            type=type_code,
            name=name,
            payload=payload,
            sort_order=self._record_repository.get_next_sort_order(
                folder_id,
                owner_user_id,
            ),
            created_at=created_at,
            updated_at=created_at,
        )

    def get_record(self, record_id: int, owner_user_id: int) -> Record | None:
        record = self._record_repository.get_by_id_and_owner(record_id, owner_user_id)
        if record is None:
            return None

        record_type = self._get_record_type(record.type)
        return replace(record, payload=record_type.deserialize(record.payload))

    def list_records(self, folder_id: int, owner_user_id: int) -> list[Record]:
        records = self._record_repository.list_by_folder_and_owner(
            folder_id,
            owner_user_id,
        )
        return [
            replace(
                record,
                payload=self._get_record_type(record.type).deserialize(record.payload),
            )
            for record in records
        ]

    def update_record(
        self,
        record_id: int,
        owner_user_id: int,
        data: dict[str, object],
    ) -> Record:
        record = self._record_repository.get_by_id_and_owner(record_id, owner_user_id)
        if record is None:
            raise RecordNotFoundError(f"Запис не знайдено: {record_id}")

        record_type = self._get_record_type(record.type)
        updated_data = record_type.deserialize(record.payload) | data
        record_type.validate(updated_data)
        payload = record_type.serialize(updated_data)
        updated_record = self._record_repository.update(
            record_id=record_id,
            owner_user_id=owner_user_id,
            name=record.name,
            payload=payload,
            updated_at=datetime.now(timezone.utc).isoformat(),
            preview_text=record.preview_text,
        )
        if updated_record is None:
            raise RecordNotFoundError(f"Запис не знайдено: {record_id}")
        return updated_record

    def delete_record(self, record_id: int, owner_user_id: int) -> None:
        if not self._record_repository.delete(record_id, owner_user_id):
            raise RecordNotFoundError(f"Запис не знайдено: {record_id}")

    def _get_record_type(self, type_code: str) -> RecordType:
        record_type = self._record_registry.get(type_code)
        if record_type is None:
            raise UnknownRecordTypeError(f"Невідомий тип запису: {type_code}")
        return record_type
