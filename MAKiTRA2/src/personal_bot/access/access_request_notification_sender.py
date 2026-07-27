from collections.abc import Sequence
from typing import Protocol

from telegram import InlineKeyboardMarkup

from personal_bot.core.entities.access_request import AccessRequest
from personal_bot.core.entities.user import User
from personal_bot.telegram.menus.access_request_review_menu import (
    create_access_request_review_menu,
)


class TelegramMessageSender(Protocol):
    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup,
    ) -> object: ...


class AccessRequestNotificationSender:
    async def notify_super_admins(
        self,
        bot: TelegramMessageSender,
        super_admins: Sequence[User],
        access_request: AccessRequest,
    ) -> None:
        for super_admin in super_admins:
            await bot.send_message(
                chat_id=super_admin.telegram_id,
                text=self._format_access_request(access_request),
                reply_markup=create_access_request_review_menu(access_request.id),
            )

    @staticmethod
    def _format_access_request(access_request: AccessRequest) -> str:
        full_name = " ".join(
            part
            for part in (access_request.first_name, access_request.last_name)
            if part
        )
        username = f"@{access_request.username}" if access_request.username else "не вказано"

        return (
            "Нова заявка на доступ\n\n"
            f"Ім'я: {full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: {access_request.telegram_id}\n"
            f"Номер телефону: {access_request.phone_number}\n"
            f"Створено: {access_request.created_at}"
        )
