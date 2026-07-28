from dataclasses import replace
from datetime import datetime, timezone

from personal_bot.core.entities.record import Record
from personal_bot.db.database import Database
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
        database: Database | None = None,
    ) -> None:
        self._record_repository = record_repository
        self._record_registry = record_registry
        self._database = database if database is not None else getattr(record_repository, "_database", None)

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

        if self._database is None:
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

        with self._database.transaction():
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
        payload = self._deserialize_record_payload(record_type, record.payload)
        return replace(record, payload=payload)

    def list_records(self, folder_id: int, owner_user_id: int) -> list[Record]:
        records = self._record_repository.list_by_folder_and_owner(
            folder_id,
            owner_user_id,
        )
        return [
            replace(
                record,
                payload=self._deserialize_record_payload(self._get_record_type(record.type), record.payload),
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
        update_data = dict(data)
        new_name = record.name

        if "name" in update_data:
            name_value = update_data.pop("name")
            if isinstance(name_value, str):
                trimmed_name = name_value.strip()
                if not trimmed_name:
                    raise ValueError("Назва запису не може бути порожньою.")
                new_name = trimmed_name
            else:
                raise ValueError("Назва запису має бути текстом.")

        existing_data = record_type.deserialize(record.payload)
        updated_data = existing_data | update_data
        if "fields" in update_data:
            payload = update_data
        else:
            record_type.validate(updated_data)
            payload = record_type.serialize(updated_data)

        updated_at = datetime.now(timezone.utc).isoformat()
        if self._database is None:
            updated_record = self._record_repository.update(
                record_id=record_id,
                owner_user_id=owner_user_id,
                name=new_name,
                payload=payload,
                updated_at=updated_at,
                preview_text=record.preview_text,
            )
            if updated_record is None:
                raise RecordNotFoundError(f"Запис не знайдено: {record_id}")
            return updated_record

        with self._database.transaction():
            updated_record = self._record_repository.update(
                record_id=record_id,
                owner_user_id=owner_user_id,
                name=new_name,
                payload=payload,
                updated_at=updated_at,
                preview_text=record.preview_text,
            )
        if updated_record is None:
            raise RecordNotFoundError(f"Запис не знайдено: {record_id}")
        return updated_record

    def delete_record(self, record_id: int, owner_user_id: int) -> None:
        if not self._record_repository.delete(record_id, owner_user_id):
            raise RecordNotFoundError(f"Запис не знайдено: {record_id}")

    def _deserialize_record_payload(self, record_type: RecordType, payload: dict[str, object] | None) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {}

        if isinstance(payload.get("fields"), list):
            return dict(payload)

        return record_type.deserialize(payload)

    def _get_record_type(self, type_code: str) -> RecordType:
        record_type = self._record_registry.get(type_code)
        if record_type is None:
            raise UnknownRecordTypeError(f"Невідомий тип запису: {type_code}")
        return record_type
