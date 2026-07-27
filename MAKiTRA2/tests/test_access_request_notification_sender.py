import asyncio
import unittest

from personal_bot.access.access_request_notification_sender import (
    AccessRequestNotificationSender,
)
from personal_bot.core.entities.access_request import AccessRequest
from personal_bot.core.entities.user import User
from personal_bot.core.enums import AccessRequestStatus, UserRole, UserStatus


class AccessRequestNotificationSenderTests(unittest.TestCase):
    def test_notify_super_admins_sends_review_message_to_every_super_admin(self) -> None:
        bot = BotStub()
        super_admins = (
            User(
                id=1,
                telegram_id=100001,
                username="first_admin",
                first_name="Перший",
                last_name="Адмін",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
            ),
            User(
                id=2,
                telegram_id=100002,
                username=None,
                first_name="Другий",
                last_name=None,
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
            ),
        )
        access_request = AccessRequest(
            id=10,
            telegram_id=200001,
            username="applicant",
            first_name="Користувач",
            last_name="Тестовий",
            phone_number="+380000000002",
            status=AccessRequestStatus.PENDING,
            created_at="2026-01-01T00:00:00+00:00",
        )

        asyncio.run(
            AccessRequestNotificationSender().notify_super_admins(
                bot,
                super_admins,
                access_request,
            )
        )

        self.assertEqual([message["chat_id"] for message in bot.messages], [100001, 100002])
        self.assertIn("Користувач Тестовий", bot.messages[0]["text"])
        self.assertIn("@applicant", bot.messages[0]["text"])
        self.assertIn("200001", bot.messages[0]["text"])
        self.assertEqual(
            bot.messages[0]["reply_markup"].inline_keyboard[0][0].callback_data,
            "access_request:approve:10",
        )


class BotStub:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: object,
    ) -> object:
        self.messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        )
        return object()


if __name__ == "__main__":
    unittest.main()
