from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from personal_bot.access.service import AccessService
from personal_bot.core.enums import UserStatus
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_keyboard,
    get_main_menu_message,
)


class StartCommandHandler:
    def __init__(self, access_service: AccessService) -> None:
        self._access_service = access_service

    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        del context
        telegram_user = update.effective_user
        message = update.effective_message

        if telegram_user is None or message is None:
            return

        user = self._access_service.find_user_by_telegram_id(telegram_user.id)

        if user is None:
            await message.reply_text(
                "Щоб отримати доступ, подайте заявку та поділіться номером телефону.",
                reply_markup=self._create_phone_number_keyboard(),
            )
            return

        sync_user_profile = getattr(self._access_service, "sync_user_profile", None)
        if sync_user_profile is not None:
            sync_user_profile(
                telegram_user.id,
                is_bot=telegram_user.is_bot,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_premium=getattr(telegram_user, "is_premium", None),
                added_to_attachment_menu=getattr(telegram_user, "added_to_attachment_menu", None),
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
        user = self._access_service.find_user_by_telegram_id(telegram_user.id)

        if user.status is UserStatus.ACTIVE:
            await message.reply_photo(
                "src/personal_bot/assets/welcome.jpg",
                caption=get_main_menu_message(),
                reply_markup=get_main_menu_keyboard(user.role),
            )
            return

        await message.reply_text("Ваш доступ до бота заблоковано.")

    @staticmethod
    def _create_phone_number_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("Поділитися номером телефону", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )