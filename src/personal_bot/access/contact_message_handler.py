from telegram import Update
from telegram.ext import ContextTypes

from personal_bot.access.access_request_notification_sender import (
    AccessRequestNotificationSender,
)
from personal_bot.access.service import AccessService
from personal_bot.core.enums import ContactRegistrationResult, UserRole
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_keyboard,
    get_main_menu_message,
)


class ContactMessageHandler:
    def __init__(
        self,
        access_service: AccessService,
        access_request_notification_sender: AccessRequestNotificationSender,
    ) -> None:
        self._access_service = access_service
        self._access_request_notification_sender = access_request_notification_sender

    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        telegram_user = update.effective_user
        message = update.effective_message

        if telegram_user is None or message is None or message.contact is None:
            return

        contact = message.contact

        if not self.is_contact_owned_by_telegram_user(
            contact.user_id,
            telegram_user.id,
        ):
            await message.reply_text(
                "Можна надсилати лише власний номер телефону."
            )
            return

        full_name = " ".join(
            part for part in (telegram_user.first_name, telegram_user.last_name) if part
        ) or None

        registration_outcome = self._access_service.register_contact(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            phone_number=contact.phone_number,
            is_bot=telegram_user.is_bot,
            full_name=full_name,
            timezone=None,
            language_code=telegram_user.language_code,
            is_premium=getattr(telegram_user, "is_premium", None),
            added_to_attachment_menu=getattr(telegram_user, "added_to_attachment_menu", None),
            allows_write_to_pm=getattr(telegram_user, "allows_write_to_pm", None),
            can_join_groups=getattr(telegram_user, "can_join_groups", None),
            can_read_all_group_messages=getattr(telegram_user, "can_read_all_group_messages", None),
            supports_inline_queries=getattr(telegram_user, "supports_inline_queries", None),
            can_connect_to_business=getattr(telegram_user, "can_connect_to_business", None),
            has_main_web_app=getattr(telegram_user, "has_main_web_app", None),
            has_topics_enabled=getattr(telegram_user, "has_topics_enabled", None),
            allows_users_to_create_topics=getattr(telegram_user, "allows_users_to_create_topics", None),
            can_manage_bots=getattr(telegram_user, "can_manage_bots", None),
            supports_guest_queries=getattr(telegram_user, "supports_guest_queries", None),
        )

        if (
            registration_outcome.result
            is ContactRegistrationResult.FIRST_SUPER_ADMIN_CREATED
        ):
            await message.reply_photo(
                "https://telegram.org/img/t_logo.png",
                caption="Вас зареєстровано як Super Admin.\n\n"
                f"{get_main_menu_message()}",
                reply_markup=get_main_menu_keyboard(user_role=UserRole.SUPER_ADMIN),
            )
            return

        if (
            registration_outcome.result
            is ContactRegistrationResult.AUTOMATIC_REGISTRATION_COMPLETED
        ):
            if self._access_service.get_notify_new_users():
                await self._access_request_notification_sender.notify_super_admins_about_registration(
                    context.bot,
                    registration_outcome.super_admins,
                    self._access_service.find_user_by_telegram_id(telegram_user.id),
                )
            await message.reply_text(
                "Ви успішно зареєстровані.\n\n"
                f"{get_main_menu_message()}",
                reply_markup=get_main_menu_keyboard(UserRole.USER),
            )
            return

        if (
            registration_outcome.result
            is ContactRegistrationResult.USER_ALREADY_REGISTERED
        ):
            user = self._access_service.find_user_by_telegram_id(telegram_user.id)
            role = user.role if user is not None else None
            await message.reply_photo(
                "https://telegram.org/img/t_logo.png",
                caption=get_main_menu_message(),
                reply_markup=get_main_menu_keyboard(role),
            )
            return

        if (
            registration_outcome.result
            is ContactRegistrationResult.ACCESS_REQUEST_ALREADY_PENDING
        ):
            await message.reply_text(
                "Ваша заявка вже отримана.\n"
                "Вона очікує підтвердження адміністратора."
            )
            return

        if registration_outcome.access_request is None:
            return

        if self._access_service.get_registration_mode() == "manual" or self._access_service.get_notify_new_users():
            await self._access_request_notification_sender.notify_super_admins(
                context.bot,
                registration_outcome.super_admins,
                registration_outcome.access_request,
            )
        await message.reply_text(
            "Вашу заявку отримано.\n"
            "Вона очікує підтвердження адміністратора."
        )

    @staticmethod
    def is_contact_owned_by_telegram_user(
        contact_user_id: int | None,
        telegram_user_id: int,
    ) -> bool:
        return contact_user_id == telegram_user_id
