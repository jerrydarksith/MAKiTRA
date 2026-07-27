from collections.abc import Mapping

from personal_bot.records.types.base import RecordType


class RecordRegistry:
    def __init__(self, record_types: Mapping[str, RecordType] | None = None) -> None:
        self._record_types = dict(record_types or {})

    def register(self, type_code: str, implementation: RecordType) -> None:
        self._record_types[type_code] = implementation

    def get(self, type_code: str) -> RecordType | None:
        return self._record_types.get(type_code)

    def list_available_types(self) -> tuple[str, ...]:
        return tuple(self._record_types)


def create_record_registry() -> RecordRegistry:
    return RecordRegistry()
