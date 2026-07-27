import unittest

from personal_bot.objects.service import ObjectsService


class ObjectsServiceTests(unittest.TestCase):
    def test_create_and_list_objects(self) -> None:
        objects_service = ObjectsService()

        created_object = objects_service.create_object(
            owner_user_id=1,
            name="Ноутбук",
            object_type="device",
            description="Мій ноутбук",
        )

        objects = objects_service.list_objects(owner_user_id=1)

        self.assertEqual(created_object.name, "Ноутбук")
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].description, "Мій ноутбук")


if __name__ == "__main__":
    unittest.main()
