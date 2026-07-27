from datetime import datetime, timezone

from personal_bot.core.entities.folder import Folder
from personal_bot.db.repositories.folder_repository import FolderRepository


class FoldersService:
    def __init__(self, folder_repository: FolderRepository) -> None:
        self._folder_repository = folder_repository

    def list_root_folders(self, owner_user_id: int) -> list[Folder]:
        return self._folder_repository.list_root_folders(owner_user_id)

    def create_folder(self, owner_user_id: int, name: str) -> Folder:
        created_at = self._get_current_timestamp()
        return self._folder_repository.create(
            owner_user_id=owner_user_id,
            parent_id=None,
            name=name,
            sort_order=self._folder_repository.get_next_sort_order(owner_user_id),
            created_at=created_at,
            updated_at=created_at,
        )

    def find_root_folder_by_name(self, owner_user_id: int, name: str) -> Folder | None:
        return self._folder_repository.find_root_folder_by_name(owner_user_id, name)

    def get_folder(self, folder_id: int, owner_user_id: int) -> Folder | None:
        return self._folder_repository.find_by_id_and_owner(folder_id, owner_user_id)

    def update_folder_name(self, folder_id: int, owner_user_id: int, name: str) -> Folder | None:
        updated_at = self._get_current_timestamp()
        return self._folder_repository.update_name(
            folder_id=folder_id,
            owner_user_id=owner_user_id,
            name=name,
            updated_at=updated_at,
        )

    def delete_folder(self, folder_id: int, owner_user_id: int) -> bool:
        return self._folder_repository.delete(folder_id, owner_user_id)

    def can_delete_folder(self, folder_id: int, owner_user_id: int) -> bool:
        return self._folder_repository.is_empty(folder_id, owner_user_id)

    def build_folder_list_message(self, owner_user_id: int) -> str:
        folders = self.list_root_folders(owner_user_id)

        if not folders:
            return (
                "📝 Мої записи\n\n"
                "У вас поки немає жодної папки.\n"
                "Створіть першу папку."
            )

        lines = ["📝 Мої записи", ""]
        for folder in folders:
            lines.append(f"📁 {folder.name}")

        return "\n".join(lines)

    def build_folder_page_message(self, folder: Folder) -> str:
        return (
            f"📁 {folder.name}\n\n"
            "Папка порожня."
        )

    @staticmethod
    def _get_current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
