import asyncio
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from personal_bot.reminders.service import RemindersService


class FakeUsersService:
    def __init__(self) -> None:
        self.users: dict[int, SimpleNamespace] = {}

    def find_user_by_id(self, user_id: int) -> SimpleNamespace | None:
        return self.users.get(user_id)


class FakeReminderRepository:
    def __init__(self) -> None:
        self.created_items = []
        self.sent_ids = []
        self.active_due = []

    def create(self, *, owner_user_id: int, record_id: int, text: str, remind_at: str, status: str, created_at: str) -> dict[str, object]:
        item = {
            "id": 1,
            "owner_user_id": owner_user_id,
            "record_id": record_id,
            "text": text,
            "remind_at": remind_at,
            "status": status,
            "created_at": created_at,
        }
        self.created_items.append(item)
        return item

    def list_active_due(self, now: str) -> list[dict[str, object]]:
        return list(self.active_due)

    def mark_sent(self, reminder_id: int) -> None:
        self.sent_ids.append(reminder_id)


class FakeBot:
    def __init__(self) -> None:
        self.sent_messages = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append((chat_id, text))


class RemindersServiceTests(unittest.TestCase):
    def test_create_reminder_normalizes_datetime_to_utc(self) -> None:
        repository = FakeReminderRepository()
        users_service = FakeUsersService()
        service = RemindersService(repository, users_service)

        reminder = service.create_reminder(
            owner_user_id=7,
            record_id=3,
            text="Підтвердити зустріч",
            remind_at="25.07.2026 12:00",
        )

        self.assertEqual(reminder["status"], "active")
        parsed_remind_at = datetime.fromisoformat(reminder["remind_at"])
        self.assertIsNotNone(parsed_remind_at.tzinfo)
        self.assertEqual(parsed_remind_at.tzinfo, timezone.utc)

    def test_dispatch_due_reminders_sends_and_marks_sent(self) -> None:
        repository = FakeReminderRepository()
        repository.active_due = [
            {
                "id": 10,
                "owner_user_id": 7,
                "record_id": 3,
                "text": "Підтвердити зустріч",
                "remind_at": "2026-07-25T12:00:00+00:00",
                "status": "active",
                "created_at": "2026-07-25T11:00:00+00:00",
            }
        ]
        users_service = FakeUsersService()
        users_service.users[7] = SimpleNamespace(id=7, telegram_id=12345)
        service = RemindersService(repository, users_service)
        bot = FakeBot()

        asyncio.run(service.dispatch_due_reminders(bot, now=datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)))

        self.assertEqual(bot.sent_messages, [(12345, "🔔 Нагадування\n\nПідтвердити зустріч")])
        self.assertEqual(repository.sent_ids, [10])


if __name__ == "__main__":
    unittest.main()
