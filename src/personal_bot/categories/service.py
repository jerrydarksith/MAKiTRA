from datetime import datetime, timezone

from personal_bot.core.entities.category import Category
from personal_bot.db.repositories.category_repository import CategoryRepository


class CategoriesService:
    def __init__(self, category_repository: CategoryRepository) -> None:
        self._category_repository = category_repository

    def create_category(
        self,
        owner_user_id: int,
        name: str,
        icon: str = "📁",
        parent_id: int | None = None,
    ) -> Category:
        created_at = self._get_current_timestamp()
        return self._category_repository.create(
            owner_user_id=owner_user_id,
            parent_id=parent_id,
            name=name,
            icon=icon,
            created_at=created_at,
            updated_at=created_at,
        )

    def build_tree_message(self, owner_user_id: int) -> str:
        categories = self._category_repository.list_by_owner(owner_user_id)
        by_id = {category.id: category for category in categories}
        roots = [category for category in categories if category.parent_id is None]

        lines = ["🌳 Дерево категорій", ""]
        if not roots:
            lines.append("Категорій ще немає.")
            return "\n".join(lines)

        for root in roots:
            lines.append(self._format_branch(root, by_id, 0))

        return "\n".join(lines).rstrip()

    def build_creation_message(self, category: Category) -> str:
        return (
            f"Створено категорію '{category.name}'."
            f"\nІконка: {category.icon}"
        )

    @staticmethod
    def _format_branch(category: Category, by_id: dict[int, Category], depth: int) -> str:
        prefix = "  " * depth
        result = [f"{prefix}{category.icon} {category.name}"]
        children = [child for child in by_id.values() if child.parent_id == category.id]
        children.sort(key=lambda item: item.name.lower())
        for child in children:
            result.append(CategoriesService._format_branch(child, by_id, depth + 1))
        return "\n".join(result)

    @staticmethod
    def _get_current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
