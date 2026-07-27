import unittest

from personal_bot.records.types.short_text import ShortTextRecordType


class ShortTextRecordTypeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record_type = ShortTextRecordType()

    def test_create_initial_data_returns_empty_value(self) -> None:
        self.assertEqual(self.record_type.create_initial_data(), {"value": ""})

    def test_validate_accepts_non_empty_text(self) -> None:
        self.assertIsNone(self.record_type.validate({"value": "Привіт"}))

    def test_validate_rejects_missing_empty_and_non_text_values(self) -> None:
        for payload in ({}, {"value": ""}, {"value": "   "}, {"value": 42}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.record_type.validate(payload)

    def test_serialize_returns_payload_with_text_value(self) -> None:
        self.assertEqual(
            self.record_type.serialize({"value": "Привіт"}),
            {"value": "Привіт"},
        )

    def test_deserialize_returns_data_with_text_value(self) -> None:
        self.assertEqual(
            self.record_type.deserialize({"value": "Привіт"}),
            {"value": "Привіт"},
        )

    def test_render_returns_text_value(self) -> None:
        self.assertEqual(self.record_type.render({"value": "Привіт"}), "Привіт")

    def test_preview_returns_text_value(self) -> None:
        self.assertEqual(self.record_type.preview({"value": "Привіт"}), "Привіт")

    def test_build_editor_steps_describes_value_input(self) -> None:
        self.assertEqual(
            self.record_type.build_editor_steps(),
            (
                {
                    "field": "value",
                    "prompt": "Введіть короткий текст.",
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()
