from datetime import datetime, timezone

from personal_bot.prototype_records.entities.folder import Folder
from personal_bot.prototype_records.exceptions.entity import EntityNotFoundError
from personal_bot.prototype_records.exceptions.validation import ValidationError
from personal_bot.prototype_records.repositories.folder_repository import FolderRepository


class PrototypeFolderService:
    def __init__(self, folder_repository: FolderRepository) -> None:
        self._folder_repository = folder_repository

    def list_children(self, owner_user_id: int, parent_id: int | None) -> list[Folder]:
        return self._folder_repository.list_children(parent_id, owner_user_id)

    def get_folder(self, folder_id: int, owner_user_id: int) -> Folder:
        folder = self._folder_repository.get(folder_id, owner_user_id)
        if folder is None:
            raise EntityNotFoundError("Folder not found")
        return folder

    def create_folder(self, owner_user_id: int, parent_id: int | None, name: str) -> Folder:
        if not name.strip():
            raise ValidationError("Folder name is required")
        now = datetime.now(timezone.utc).isoformat()
        return self._folder_repository.create(
            owner_user_id=owner_user_id,
            parent_id=parent_id,
            name=name,
            sort_order=self._folder_repository.next_sort_order(owner_user_id, parent_id),
            created_at=now,
            updated_at=now,
        )

    def rename_folder(self, folder_id: int, owner_user_id: int, name: str) -> Folder:
        if not name.strip():
            raise ValidationError("Folder name is required")
        now = datetime.now(timezone.utc).isoformat()
        return self._folder_repository.update_name(folder_id, owner_user_id, name, now)

    def delete_folder(self, folder_id: int, owner_user_id: int) -> None:
        self._folder_repository.delete(folder_id, owner_user_id)
