from personal_bot.records.types.base import RecordType


class ShortTextRecordType(RecordType):
    def create_initial_data(self) -> dict[str, object]:
        return {"value": ""}

    def validate(self, payload: dict[str, object]) -> None:
        self._get_value(payload)

    def serialize(self, data: dict[str, object]) -> dict[str, object]:
        return {"value": self._get_value(data)}

    def deserialize(self, payload: dict[str, object]) -> dict[str, object]:
        return {"value": self._get_value(payload)}

    def render(self, payload: dict[str, object]) -> str:
        return self._get_value(payload)

    def preview(self, payload: dict[str, object]) -> str:
        return self._get_value(payload)

    def build_editor_steps(self) -> tuple[object, ...]:
        return (
            {
                "field": "value",
                "prompt": "Введіть короткий текст.",
            },
        )

    @staticmethod
    def _get_value(payload: dict[str, object]) -> str:
        value = payload.get("value")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Короткий текст має містити непорожнє значення.")
        return value
