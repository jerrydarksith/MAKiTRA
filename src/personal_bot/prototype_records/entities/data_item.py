from dataclasses import dataclass


@dataclass(frozen=True)
class DataItem:
    id: int
    record_id: int
    name: str
    type: str
    value: object
    sort_order: int
    created_at: str
    updated_at: str
