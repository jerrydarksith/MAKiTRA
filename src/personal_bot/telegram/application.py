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
from personal_bot.users.callback_handlers import UsersCallbackHandler, UsersMessageHandler
from personal_bot.users.service import UsersService


def create_telegram_application(
    telegram_bot_token: str,
    access_service: AccessService,
    users_service: UsersService,
    categories_service: CategoriesService,
    folders_service: FoldersService,
    objects_service: ObjectsService,
) -> Application:
    telegram_application = ApplicationBuilder().token(telegram_bot_token).build()
    start_command_handler = StartCommandHandler(access_service)
    contact_message_handler = ContactMessageHandler(
        access_service,
        AccessRequestNotificationSender(),
    )
    access_request_callback_handler = AccessRequestCallbackHandler(access_service)
    users_message_handler = UsersMessageHandler(users_service)
    users_callback_handler = UsersCallbackHandler(users_service)
    categories_message_handler = CategoriesMessageHandler(categories_service)
    categories_callback_handler = CategoriesCallbackHandler(categories_service)
    folders_message_handler = FoldersMessageHandler(folders_service, users_service)
    objects_message_handler = ObjectsMessageHandler(objects_service)
    telegram_application.add_handler(
        CommandHandler("start", start_command_handler.handle)
    )
    telegram_application.add_handler(
        MessageHandler(filters.CONTACT, contact_message_handler.handle)
    )
    telegram_application.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.Regex(
                r"^📁 Папки$|^⚙️ Налаштування$|^🛡 Адміністрування$|^👥 Користувачі(?: \(\d+\))?$|^📨 Заявки$|^⬅ Назад$"
            ),
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
        CallbackQueryHandler(
            access_request_callback_handler.handle,
            pattern=r"^access_request:(approve|reject):\d+$",
        )
    )
    telegram_application.add_handler(
        CallbackQueryHandler(
            users_callback_handler.handle,
            pattern=r"^users:(page|back):?.*$",
        )
    )
    telegram_application.add_handler(
        CallbackQueryHandler(
            categories_callback_handler.handle,
            pattern=r"^categories:back$",
        )
    )

    return telegram_application
