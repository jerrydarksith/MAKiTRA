from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    id: int
    owner_user_id: int
    folder_id: int
    name: str
    created_at: str
    updated_at: str
