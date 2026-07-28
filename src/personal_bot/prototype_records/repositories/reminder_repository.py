from personal_bot.prototype_records.entities.reminder import Reminder
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError


class ReminderRepository:
    def __init__(self) -> None:
        self._reminders: dict[int, Reminder] = {}
        self._next_id = 1

    def list_by_record(self, record_id: int) -> list[Reminder]:
        return [reminder for reminder in self._reminders.values() if reminder.record_id == record_id]

    def create(self, record_id: int, data_item_id: int | None, due_at: str, message: str, created_at: str, updated_at: str) -> Reminder:
        reminder = Reminder(
            id=self._next_id,
            record_id=record_id,
            data_item_id=data_item_id,
            due_at=due_at,
            message=message,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._reminders[self._next_id] = reminder
        self._next_id += 1
        return reminder

    def delete(self, reminder_id: int) -> None:
        reminder = self._reminders.get(reminder_id)
        if reminder is None:
            raise EntityNotFoundError("Reminder not found")
        del self._reminders[reminder_id]
