from dataclasses import dataclass


@dataclass(frozen=True)
class Object:
    id: int
    owner_user_id: int
    category_id: int | None
    name: str
    object_type: str
    description: str | None = None
