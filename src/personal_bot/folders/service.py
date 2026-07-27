from datetime import datetime, timezone

from personal_bot.core.entities.folder import Folder
from personal_bot.db.database import Database
from personal_bot.db.repositories.folder_repository import FolderRepository


class FoldersService:
    def __init__(self, database: Database, folder_repository: FolderRepository) -> None:
        self._database = database
        self._folder_repository = folder_repository

    def list_root_folders(self, owner_user_id: int) -> list[Folder]:
        return self._folder_repository.list_root_folders(owner_user_id)

    def list_child_folders(self, parent_id: int | None, owner_user_id: int) -> list[Folder]:
        return self._folder_repository.list_by_parent_and_owner(parent_id, owner_user_id)

    def create_folder(
        self,
        owner_user_id: int,
        name: str,
        parent_id: int | None = None,
    ) -> Folder:
        name = name.strip()
        if not name:
            raise ValueError("Назва папки не може бути порожньою.")

        with self._database.transaction():
            if parent_id is not None:
                parent_folder = self._folder_repository.find_by_id_and_owner(parent_id, owner_user_id)
                if parent_folder is None:
                    raise ValueError("Папку не знайдено.")

            created_at = self._get_current_timestamp()
            return self._folder_repository.create(
                owner_user_id=owner_user_id,
                parent_id=parent_id,
                name=name,
                sort_order=self._folder_repository.get_next_sort_order(owner_user_id),
                created_at=created_at,
                updated_at=created_at,
            )

    def find_root_folder_by_name(self, owner_user_id: int, name: str) -> Folder | None:
        return self._folder_repository.find_root_folder_by_name(owner_user_id, name)

    def find_folder_by_name_and_parent(
        self,
        owner_user_id: int,
        name: str,
        parent_id: int | None,
    ) -> Folder | None:
        return self._folder_repository.find_by_name_and_parent(owner_user_id, name, parent_id)

    def get_folder(self, folder_id: int, owner_user_id: int) -> Folder | None:
        return self._folder_repository.find_by_id_and_owner(folder_id, owner_user_id)

    def update_folder_name(self, folder_id: int, owner_user_id: int, name: str) -> Folder | None:
        name = name.strip()
        if not name:
            raise ValueError("Назва папки не може бути порожньою.")

        updated_at = self._get_current_timestamp()

        with self._database.transaction():
            return self._folder_repository.update_name(
                folder_id=folder_id,
                owner_user_id=owner_user_id,
                name=name,
                updated_at=updated_at,
            )

    def delete_folder(self, folder_id: int, owner_user_id: int) -> bool:
        with self._database.transaction():
            return self._folder_repository.delete(folder_id, owner_user_id)

    def can_delete_folder(self, folder_id: int, owner_user_id: int) -> bool:
        return self._folder_repository.is_empty(folder_id, owner_user_id)

    def build_folder_list_message(self, owner_user_id: int) -> str:
        del owner_user_id
        return "📝 Мої записи"

    def build_folder_page_message(self, folder: Folder) -> str:
        return f"📝 Мої записи / {folder.name}"

    @staticmethod
    def _get_current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
