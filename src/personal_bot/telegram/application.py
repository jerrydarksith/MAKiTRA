import re

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from personal_bot.access.access_request_notification_sender import (
    AccessRequestNotificationSender,
)
from personal_bot.access.callback_handlers.access_request_callback_handler import (
    AccessRequestCallbackHandler,
)
from personal_bot.access.contact_message_handler import ContactMessageHandler
from personal_bot.access.service import AccessService
from personal_bot.access.start_command_handler import StartCommandHandler
from personal_bot.categories.callback_handlers import CategoriesCallbackHandler, CategoriesMessageHandler
from personal_bot.categories.service import CategoriesService
from personal_bot.folders.callback_handlers import FoldersMessageHandler
from personal_bot.folders.service import FoldersService
from personal_bot.objects.callback_handlers import ObjectsMessageHandler
from personal_bot.objects.service import ObjectsService
from personal_bot.records.registry import RecordRegistry
from personal_bot.records.service import RecordsService
from personal_bot.reminders.service import RemindersService
from personal_bot.users.callback_handlers import UsersMessageHandler


def get_admin_settings_menu_regex() -> str:
    labels = [
        "📝 Записи",
        "⚙️ Налаштування",
        "🛡 Адміністрування",
        "👥 Користувачі",
        "📨 Заявки",
        "🟢 Реєстрація: Автоматична",
        "🔴 Реєстрація: Через підтвердження",
        "🟢 Повідомлення адміну: Увімкнено",
        "🔴 Повідомлення адміну: Вимкнено",
        "Режим реєстрації: Автоматична",
        "Режим реєстрації: Через підтвердження",
        "Повідомлення адміну: Увімкнено",
        "Повідомлення адміну: Вимкнено",
        "⬅️ Назад",
        "⬅ Назад",
        "⬅ Попередня",
        "➡ Наступна",
        "🗑 Видалити",
        "🗑 Видалити користувача",
        "🚫 Забанити",
        "✅ Розбанити",
        "✅ Так",
        "❌ Ні",
    ]
    escaped_labels = [re.escape(label) for label in labels]
    return rf"^(?:{'|'.join(escaped_labels)}|👥 Користувачі \(\d+\)|👤 .+)$"


async def _dispatch_due_reminders(application: Application, reminders_service: RemindersService) -> None:
    await reminders_service.dispatch_due_reminders(application.bot)
from personal_bot.users.service import UsersService


def create_telegram_application(
    telegram_bot_token: str,
    access_service: AccessService,
    users_service: UsersService,
    categories_service: CategoriesService,
    folders_service: FoldersService,
    records_service: RecordsService,
    reminders_service: RemindersService,
    record_registry: RecordRegistry,
    objects_service: ObjectsService,
) -> Application:
    telegram_application = ApplicationBuilder().token(telegram_bot_token).build()
    start_command_handler = StartCommandHandler(access_service)
    contact_message_handler = ContactMessageHandler(
        access_service,
        AccessRequestNotificationSender(),
    )
    access_request_callback_handler = AccessRequestCallbackHandler(access_service)
    users_message_handler = UsersMessageHandler(users_service, access_service)
    categories_message_handler = CategoriesMessageHandler(categories_service)
    categories_callback_handler = CategoriesCallbackHandler(categories_service)
    folders_message_handler = FoldersMessageHandler(
        folders_service,
        users_service,
        records_service,
        reminders_service,
        record_registry,
    )
    objects_message_handler = ObjectsMessageHandler(objects_service)
    telegram_application.add_handler(
        CommandHandler("start", start_command_handler.handle)
    )
    telegram_application.add_handler(
        MessageHandler(filters.CONTACT, contact_message_handler.handle)
    )
    telegram_application.add_handler(
        MessageHandler(
            filters.TEXT & folders_message_handler.get_filter(),
            folders_message_handler.handle,
        )
    )
    telegram_application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(get_admin_settings_menu_regex()),
            users_message_handler.handle,
        )
    )
    telegram_application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^📚 Категорії$|^⬅ Назад$"),
            categories_message_handler.handle,
        )
    )
    telegram_application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^📦 Об’єкти$|^⬅ Назад$"),
            objects_message_handler.handle,
        )
    )
    telegram_application.add_handler(
        MessageHandler(filters.TEXT, users_message_handler.handle)
    )
    telegram_application.add_handler(
        CallbackQueryHandler(
            access_request_callback_handler.handle,
            pattern=r"^access_request:(approve|reject):\d+$",
        )
    )
    telegram_application.job_queue.run_repeating(
        lambda context: _dispatch_due_reminders(telegram_application, reminders_service),
        interval=60,
        first=0,
    )
    telegram_application.add_handler(
        CallbackQueryHandler(
            categories_callback_handler.handle,
            pattern=r"^categories:back$",
        )
    )

    return telegram_application
