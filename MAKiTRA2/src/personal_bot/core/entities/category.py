from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    id: int
    owner_user_id: int
    parent_id: int | None
    name: str
    icon: str