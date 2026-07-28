from dataclasses import dataclass


@dataclass(frozen=True)
class Folder:
    id: int
    owner_user_id: int
    parent_id: int | None
    name: str
    sort_order: int
    created_at: str
    updated_at: str
