from telegram import Update
from telegram.ext import ContextTypes

from personal_bot.objects.service import ObjectsService
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_message,
    get_super_admin_keyboard,
)


class ObjectsMessageHandler:
    def __init__(self, objects_service: ObjectsService) -> None:
        self._objects_service = objects_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        message = update.effective_message

        if message is None or message.text is None:
            return

        text = message.text.strip()

        if text == "📦 Об’єкти":
            await message.reply_text(
                self._objects_service.build_objects_message(owner_user_id=1)
            )
            return

        if text == "⬅ Назад":
            await message.reply_text(
                get_main_menu_message(),
                reply_markup=get_super_admin_keyboard(),
            )
