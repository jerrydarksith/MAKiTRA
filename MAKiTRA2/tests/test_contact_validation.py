import unittest

from personal_bot.access.contact_message_handler import ContactMessageHandler


class ContactValidationTests(unittest.TestCase):
    def test_contact_from_another_user_is_rejected(self) -> None:
        is_owned_by_telegram_user = (
            ContactMessageHandler.is_contact_owned_by_telegram_user(
                contact_user_id=999,
                telegram_user_id=123456,
            )
        )

        self.assertFalse(is_owned_by_telegram_user)

    def test_contact_from_current_user_is_accepted(self) -> None:
        is_owned_by_telegram_user = (
            ContactMessageHandler.is_contact_owned_by_telegram_user(
                contact_user_id=123456,
                telegram_user_id=123456,
            )
        )

        self.assertTrue(is_owned_by_telegram_user)


if __name__ == "__main__":
    unittest.main()
