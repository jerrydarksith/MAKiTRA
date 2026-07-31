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
        reply_markup: InlineKeyboardMarkup | None,
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

    async def notify_super_admins_about_registration(
        self,
        bot: TelegramMessageSender,
        super_admins: Sequence[User],
        user: User,
    ) -> None:
        for super_admin in super_admins:
            await bot.send_message(
                chat_id=super_admin.telegram_id,
                text=self._format_registration_message(user),
                reply_markup=None,
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

    @staticmethod
    def _format_registration_message(user: User) -> str:
        full_name = " ".join(
            part
            for part in (user.first_name, user.last_name)
            if part
        )
        username = f"@{user.username}" if user.username else "не вказано"

        return (
            "Зареєстровано нового користувача\n\n"
            f"Ім'я: {full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"Номер телефону: {user.phone_number}"
        )
