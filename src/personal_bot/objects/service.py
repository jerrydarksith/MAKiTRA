from personal_bot.core.entities.object import Object


class ObjectsService:
    def __init__(self) -> None:
        self._objects: list[Object] = []

    def create_object(
        self,
        owner_user_id: int,
        name: str,
        object_type: str,
        category_id: int | None = None,
        description: str | None = None,
    ) -> Object:
        object_id = len(self._objects) + 1
        created_object = Object(
            id=object_id,
            owner_user_id=owner_user_id,
            category_id=category_id,
            name=name,
            object_type=object_type,
            description=description,
        )
        self._objects.append(created_object)
        return created_object

    def list_objects(self, owner_user_id: int) -> list[Object]:
        return [object_item for object_item in self._objects if object_item.owner_user_id == owner_user_id]

    def build_objects_message(self, owner_user_id: int) -> str:
        objects = self.list_objects(owner_user_id)
        if not objects:
            return "📦 Об’єкти\n\nПоки що немає об’єктів."

        lines = ["📦 Об’єкти", ""]
        for object_item in objects:
            lines.append(f"- {object_item.name} ({object_item.object_type})")
            if object_item.description:
                lines.append(f"  {object_item.description}")
        return "\n".join(lines)
