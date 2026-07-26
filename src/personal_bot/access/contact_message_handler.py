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

        registration_outcome = self._access_service.register_contact(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            phone_number=contact.phone_number,
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
