from personal_bot.access.service import AccessService
from personal_bot.categories.service import CategoriesService
from personal_bot.config import load_application_settings
from personal_bot.db.database import Database
from personal_bot.db.repositories.access_request_repository import AccessRequestRepository
from personal_bot.db.repositories.category_repository import CategoryRepository
from personal_bot.db.repositories.folder_repository import FolderRepository
from personal_bot.db.repositories.record_repository import RecordRepository
from personal_bot.db.repositories.reminder_repository import ReminderRepository
from personal_bot.db.repositories.settings_repository import SettingsRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.folders.service import FoldersService
from personal_bot.objects.service import ObjectsService
from personal_bot.records.registry import create_record_registry
from personal_bot.records.service import RecordsService
from personal_bot.records.types.short_text import ShortTextRecordType
from personal_bot.reminders.service import RemindersService
from personal_bot.telegram.application import create_telegram_application
from personal_bot.users.service import UsersService


def run_application() -> None:
    application_settings = load_application_settings()
    database = Database(application_settings.database_path)

    try:
        initialize_database_schema(database)
        user_repository = UserRepository(database)
        settings_repository = SettingsRepository(database)
        access_request_repository = AccessRequestRepository(database)
        category_repository = CategoryRepository(database)
        folder_repository = FolderRepository(database)
        record_repository = RecordRepository(database)
        reminder_repository = ReminderRepository(database)
        access_service = AccessService(
            database,
            user_repository,
            settings_repository,
            access_request_repository,
        )
        users_service = UsersService(user_repository)
        categories_service = CategoriesService(category_repository)
        folders_service = FoldersService(database, folder_repository)
        record_registry = create_record_registry()
        record_registry.register("short_text", ShortTextRecordType())
        records_service = RecordsService(record_repository, record_registry)
        record_repository = RecordRepository(database)
        folder_repository = FolderRepository(database)
        reminders_service = RemindersService(
            reminder_repository,
            users_service,
            record_repository,
            folder_repository,
        )
        objects_service = ObjectsService()
        telegram_application = create_telegram_application(
            application_settings.telegram_bot_token,
            access_service,
            users_service,
            categories_service,
            folders_service,
            records_service,
            reminders_service,
            record_registry,
            objects_service,
        )
        telegram_application.run_polling()
    finally:
        database.close()
