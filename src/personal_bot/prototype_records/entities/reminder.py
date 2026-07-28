from dataclasses import dataclass


@dataclass(frozen=True)
class Reminder:
    id: int
    record_id: int
    data_item_id: int | None
    due_at: str
    message: str
    created_at: str
    updated_at: str
