from typing import Iterator

from personal_bot.prototype_records.entities.folder import Folder
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError, DuplicateNameError


class FolderRepository:
    def __init__(self) -> None:
        self._folders: dict[int, Folder] = {}
        self._next_id = 1

    def list_by_owner(self, owner_user_id: int) -> list[Folder]:
        return [folder for folder in self._folders.values() if folder.owner_user_id == owner_user_id]

    def list_children(self, parent_id: int | None, owner_user_id: int) -> list[Folder]:
        return [
            folder
            for folder in self._folders.values()
            if folder.owner_user_id == owner_user_id and folder.parent_id == parent_id
        ]

    def get(self, folder_id: int, owner_user_id: int) -> Folder | None:
        folder = self._folders.get(folder_id)
        return folder if folder is not None and folder.owner_user_id == owner_user_id else None

    def create(self, owner_user_id: int, parent_id: int | None, name: str, sort_order: int, created_at: str, updated_at: str) -> Folder:
        if any(
            folder.owner_user_id == owner_user_id and folder.parent_id == parent_id and folder.name == name
            for folder in self._folders.values()
        ):
            raise DuplicateNameError(f"Folder with name '{name}' already exists")

        folder = Folder(
            id=self._next_id,
            owner_user_id=owner_user_id,
            parent_id=parent_id,
            name=name,
            sort_order=sort_order,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._folders[self._next_id] = folder
        self._next_id += 1
        return folder

    def update_name(self, folder_id: int, owner_user_id: int, name: str, updated_at: str) -> Folder:
        folder = self.get(folder_id, owner_user_id)
        if folder is None:
            raise EntityNotFoundError("Folder not found")
        updated = Folder(
            id=folder.id,
            owner_user_id=folder.owner_user_id,
            parent_id=folder.parent_id,
            name=name,
            sort_order=folder.sort_order,
            created_at=folder.created_at,
            updated_at=updated_at,
        )
        self._folders[folder_id] = updated
        return updated

    def delete(self, folder_id: int, owner_user_id: int) -> None:
        folder = self.get(folder_id, owner_user_id)
        if folder is None:
            raise EntityNotFoundError("Folder not found")
        del self._folders[folder_id]

    def next_sort_order(self, owner_user_id: int, parent_id: int | None) -> int:
        children = self.list_children(parent_id, owner_user_id)
        return max((folder.sort_order for folder in children), default=0) + 1
