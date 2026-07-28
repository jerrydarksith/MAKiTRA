from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from personal_bot.db.repositories.folder_repository import FolderRepository
from personal_bot.db.repositories.record_repository import RecordRepository
from personal_bot.users.service import UsersService


class ReminderRepositoryProtocol(Protocol):
    def create(self, *, owner_user_id: int, record_id: int, text: str, remind_at: str, status: str, created_at: str) -> object:
        raise NotImplementedError

    def list_active_due(self, now: str) -> list[object]:
        raise NotImplementedError

    def mark_sent(self, reminder_id: int) -> None:
        raise NotImplementedError


class RemindersService:
    def __init__(
        self,
        reminder_repository: ReminderRepositoryProtocol,
        users_service: UsersService,
        record_repository: RecordRepository,
        folder_repository: FolderRepository,
    ) -> None:
        self._reminder_repository = reminder_repository
        self._users_service = users_service
        self._record_repository = record_repository
        self._folder_repository = folder_repository

    def create_reminder(self, *, record_id: int, text: str, remind_at: str, owner_user_id: int | None = None) -> object:
        created_at = datetime.now(timezone.utc).isoformat()
        normalized_remind_at = self._normalize_remind_at(remind_at)
        return self._reminder_repository.create(
            owner_user_id=owner_user_id,
            record_id=record_id,
            text=text,
            remind_at=normalized_remind_at,
            status="active",
            created_at=created_at,
        )

    async def dispatch_due_reminders(self, bot, now: datetime | None = None) -> list[object]:
        current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        due_reminders = self._reminder_repository.list_active_due(current_time.isoformat())
        for reminder in due_reminders:
            reminder_id = reminder.get("id")
            owner_user_id = reminder.get("owner_user_id")
            reminder_text = reminder.get("text", "")
            try:
                if owner_user_id is None or not hasattr(bot, "send_message"):
                    continue

                user = self._users_service.find_user_by_id(owner_user_id)
                if user is None:
                    print(f"Reminder dispatch skipped: user not found for owner_user_id={owner_user_id}")
                    continue

                telegram_id = getattr(user, "telegram_id", None)
                if telegram_id is None:
                    print(f"Reminder dispatch skipped: missing telegram_id for user id={owner_user_id}")
                    continue

                record_id = reminder.get("record_id")
                record = self._record_repository.get_by_id(record_id) if record_id is not None else None
                record_name = record.name if record is not None else "Невідомий"
                if record is not None and record.folder_id is not None:
                    folder_names: list[str] = []
                    current_folder_id = record.folder_id
                    while current_folder_id is not None:
                        folder = self._folder_repository.find_by_id(current_folder_id)
                        if folder is None:
                            break
                        folder_names.append(folder.name)
                        current_folder_id = folder.parent_id
                    folder_names.reverse()
                    path_text = "Мої записи"
                    if folder_names:
                        path_text += " / " + " / ".join(folder_names)
                else:
                    path_text = "Мої записи"

                message_text = (
                    "🔔 Нагадування\n\n"
                    "📂 Шлях:\n"
                    f"{path_text}\n\n"
                    "📄 Запис:\n"
                    f"{record_name}\n\n"
                    "📝 Текст:\n"
                    f"{reminder_text}"
                )
                await bot.send_message(chat_id=telegram_id, text=message_text)
            finally:
                if reminder_id is not None:
                    self._reminder_repository.mark_sent(reminder_id)
        return due_reminders

    def _normalize_remind_at(self, remind_at: str | datetime) -> str:
        if isinstance(remind_at, datetime):
            parsed_value = remind_at
        else:
            trimmed_value = remind_at.strip()
            try:
                parsed_value = datetime.fromisoformat(trimmed_value)
            except ValueError:
                parsed_value = datetime.strptime(trimmed_value, "%d.%m.%Y %H:%M")

        if parsed_value.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo or timezone.utc
            parsed_value = parsed_value.replace(tzinfo=local_tz)

        return parsed_value.astimezone(timezone.utc).isoformat()
