import unittest

from personal_bot.core.entities.record import Record
from personal_bot.records.service import (
    RecordNotFoundError,
    RecordsService,
    UnknownRecordTypeError,
)


class FakeRecordType:
    def __init__(self) -> None:
        self.create_initial_data_calls = 0
        self.validated_data: list[dict[str, object]] = []
        self.serialized_data: list[dict[str, object]] = []
        self.deserialized_payloads: list[dict[str, object]] = []

    def create_initial_data(self) -> dict[str, object]:
        self.create_initial_data_calls += 1
        return {"value": "initial"}

    def validate(self, payload: dict[str, object]) -> None:
        self.validated_data.append(payload)

    def serialize(self, data: dict[str, object]) -> dict[str, object]:
        self.serialized_data.append(data)
        return {"stored": data["value"]}

    def deserialize(self, payload: dict[str, object]) -> dict[str, object]:
        self.deserialized_payloads.append(payload)
        return {"value": payload["stored"]}

    def render(self, payload: dict[str, object]) -> str:
        return str(payload["value"])

    def preview(self, payload: dict[str, object]) -> str:
        return str(payload["value"])

    def build_editor_steps(self) -> tuple[object, ...]:
        return ()


class FakeRegistry:
    def __init__(self, record_types: dict[str, FakeRecordType]) -> None:
        self._record_types = record_types
        self.requested_type_codes: list[str] = []

    def get(self, type_code: str) -> FakeRecordType | None:
        self.requested_type_codes.append(type_code)
        return self._record_types.get(type_code)


class FakeRepository:
    def __init__(self) -> None:
        self.created_arguments: dict[str, object] | None = None
        self.records_by_id: dict[int, Record] = {}
        self.records_by_folder: dict[tuple[int, int], list[Record]] = {}

    def create(self, **kwargs) -> Record:
        self.created_arguments = kwargs
        record = Record(id=1, preview_text=None, **kwargs)
        self.records_by_id[record.id] = record
        self.records_by_folder.setdefault(
            (record.folder_id, record.owner_user_id),
            [],
        ).append(record)
        return record

    def get_next_sort_order(self, folder_id: int, owner_user_id: int) -> int:
        return 1

    def get_by_id_and_owner(self, record_id: int, owner_user_id: int) -> Record | None:
        record = self.records_by_id.get(record_id)
        if record is None or record.owner_user_id != owner_user_id:
            return None
        return record

    def list_by_folder_and_owner(self, folder_id: int, owner_user_id: int) -> list[Record]:
        return self.records_by_folder.get((folder_id, owner_user_id), [])

    def update(
        self,
        record_id: int,
        owner_user_id: int,
        name: str,
        payload: dict[str, object],
        updated_at: str,
        preview_text: str | None,
    ) -> Record | None:
        record = self.get_by_id_and_owner(record_id, owner_user_id)
        if record is None:
            return None
        updated_record = Record(
            id=record.id,
            owner_user_id=record.owner_user_id,
            folder_id=record.folder_id,
            type=record.type,
            name=name,
            payload=payload,
            sort_order=record.sort_order,
            created_at=record.created_at,
            updated_at=updated_at,
            preview_text=preview_text,
        )
        self.records_by_id[record_id] = updated_record
        return updated_record

    def delete(self, record_id: int, owner_user_id: int) -> bool:
        record = self.get_by_id_and_owner(record_id, owner_user_id)
        if record is None:
            return False
        del self.records_by_id[record_id]
        return True


class RecordsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record_type = FakeRecordType()
        self.registry = FakeRegistry({"fake": self.record_type})
        self.repository = FakeRepository()
        self.service = RecordsService(self.repository, self.registry)

    def test_create_record_uses_registry_and_type_lifecycle(self) -> None:
        record = self.service.create_record(
            owner_user_id=10,
            folder_id=20,
            type_code="fake",
            name="Назва",
            data={"value": "Текст"},
        )

        self.assertEqual(record.payload, {"stored": "Текст"})
        self.assertEqual(self.registry.requested_type_codes, ["fake"])
        self.assertEqual(self.record_type.create_initial_data_calls, 1)
        self.assertEqual(self.record_type.validated_data, [{"value": "Текст"}])
        self.assertEqual(self.record_type.serialized_data, [{"value": "Текст"}])
        self.assertIsNotNone(self.repository.created_arguments)
        self.assertEqual(
            self.repository.created_arguments["payload"],
            {"stored": "Текст"},
        )

    def test_get_record_deserializes_payload_with_registered_type(self) -> None:
        stored_record = Record(
            id=1,
            owner_user_id=10,
            folder_id=20,
            type="fake",
            name="Назва",
            payload={"stored": "Текст"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text=None,
        )
        self.repository.records_by_id[stored_record.id] = stored_record

        record = self.service.get_record(record_id=1, owner_user_id=10)

        self.assertIsNotNone(record)
        self.assertEqual(record.payload, {"value": "Текст"})
        self.assertEqual(self.registry.requested_type_codes, ["fake"])
        self.assertEqual(self.record_type.deserialized_payloads, [{"stored": "Текст"}])

    def test_list_records_deserializes_each_payload(self) -> None:
        records = [
            Record(
                id=1,
                owner_user_id=10,
                folder_id=20,
                type="fake",
                name="Перший",
                payload={"stored": "Один"},
                sort_order=1,
                created_at="2026-01-01T00:00:00+00:00",
                updated_at="2026-01-01T00:00:00+00:00",
                preview_text=None,
            ),
            Record(
                id=2,
                owner_user_id=10,
                folder_id=20,
                type="fake",
                name="Другий",
                payload={"stored": "Два"},
                sort_order=2,
                created_at="2026-01-01T00:00:00+00:00",
                updated_at="2026-01-01T00:00:00+00:00",
                preview_text=None,
            ),
        ]
        self.repository.records_by_folder[(20, 10)] = records

        result = self.service.list_records(folder_id=20, owner_user_id=10)

        self.assertEqual([record.payload for record in result], [{"value": "Один"}, {"value": "Два"}])
        self.assertEqual(self.registry.requested_type_codes, ["fake", "fake"])
        self.assertEqual(
            self.record_type.deserialized_payloads,
            [{"stored": "Один"}, {"stored": "Два"}],
        )

    def test_unknown_type_code_raises_error(self) -> None:
        with self.assertRaises(UnknownRecordTypeError):
            self.service.create_record(
                owner_user_id=10,
                folder_id=20,
                type_code="unknown",
                name="Назва",
                data={"value": "Текст"},
            )

    def test_update_record_deserializes_validates_and_serializes_data(self) -> None:
        stored_record = Record(
            id=1,
            owner_user_id=10,
            folder_id=20,
            type="fake",
            name="Назва",
            payload={"stored": "До"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text=None,
        )
        self.repository.records_by_id[stored_record.id] = stored_record

        updated_record = self.service.update_record(
            record_id=1,
            owner_user_id=10,
            data={"value": "Після"},
        )

        self.assertEqual(updated_record.payload, {"stored": "Після"})
        self.assertEqual(self.registry.requested_type_codes, ["fake"])
        self.assertEqual(self.record_type.deserialized_payloads, [{"stored": "До"}])
        self.assertEqual(self.record_type.validated_data, [{"value": "Після"}])
        self.assertEqual(self.record_type.serialized_data, [{"value": "Після"}])

    def test_update_record_raises_error_for_unknown_type_code(self) -> None:
        self.repository.records_by_id[1] = Record(
            id=1,
            owner_user_id=10,
            folder_id=20,
            type="unknown",
            name="Назва",
            payload={"stored": "Текст"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text=None,
        )

        with self.assertRaises(UnknownRecordTypeError):
            self.service.update_record(1, owner_user_id=10, data={"value": "Текст"})

    def test_update_record_raises_error_when_record_is_missing(self) -> None:
        with self.assertRaises(RecordNotFoundError):
            self.service.update_record(1, owner_user_id=10, data={"value": "Текст"})

    def test_delete_record_delegates_to_repository(self) -> None:
        self.repository.records_by_id[1] = Record(
            id=1,
            owner_user_id=10,
            folder_id=20,
            type="fake",
            name="Назва",
            payload={"stored": "Текст"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text=None,
        )

        self.assertIsNone(self.service.delete_record(1, owner_user_id=10))
        self.assertNotIn(1, self.repository.records_by_id)

    def test_delete_record_raises_error_when_record_is_missing(self) -> None:
        with self.assertRaises(RecordNotFoundError):
            self.service.delete_record(1, owner_user_id=10)


if __name__ == "__main__":
    unittest.main()
