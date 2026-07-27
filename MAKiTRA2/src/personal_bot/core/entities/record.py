from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    id: int
    owner_user_id: int
    folder_id: int
    type: str
    name: str
    payload: dict[str, object]
    sort_order: int
    created_at: str
    updated_at: str
    preview_text: str | None
