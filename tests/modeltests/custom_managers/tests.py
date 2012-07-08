from __future__ import absolute_import

from django.test import TestCase

from .models import Person, Book, Car, PersonManager, PublishedBookManager


class CustomManagerTests(TestCase):
    def setUp(self):
        p1 = Person.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        self.p2 = Person.objects.create(first_name="Droopy", last_name="Dog", fun=False)

        b1 = Book.published_objects.create(
            title="How to program", author="Rodney Dangerfield", is_published=True
        )
        self.b2 = Book.published_objects.create(
            title="How to be smart", author="Albert Einstein", is_published=False
        )
        c1 = Car.cars.create(name="Corvette", mileage=21, top_speed=180)
        c2 = Car.cars.create(name="Neon", mileage=31, top_speed=100)

    def test_custom_manager_is_correct_type(self):
        # The RelatedManager used on the 'books' descriptor extends the default
        # manager
        self.assertTrue(isinstance(self.p2.books, PublishedBookManager))

    def test_custom_manager_method(self):
        self.assertQuerysetEqual(
            Person.objects.get_fun_people(), [
                "Bugs Bunny"
            ],
            unicode
        )

    def test_default_manager_doesnt_exist_if_custom_manager_is_provided(self):
        # The default manager, "objects", doesn't exist, because a custom one
        # was provided.
        self.assertRaises(AttributeError, lambda: Book.objects)

    def test_related_manager_extends_default_manager(self):
        # The RelatedManager used on the 'authors' descriptor extends the
        # default manager
        self.assertTrue(isinstance(self.b2.authors, PersonManager))

    def test_assert_custom_manager_all_method_called_correctly(self):
        self.assertQuerysetEqual(
            Book.published_objects.all(), [
                "How to program",
                ],
            lambda b: b.title
        )

    def test_default_manager_correct(self):
        self.assertQuerysetEqual(
            Car.cars.order_by("name"), [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name
        )

    def test_custom_manager_correct(self):
        self.assertQuerysetEqual(
            Car.fast_cars.all(), [
                "Corvette",
            ],
            lambda c: c.name
        )

    def test_underscore_default_manager_attribute_correct(self):
        # Each model class gets a "_default_manager" attribute, which is a
        # reference to the first manager defined in the class. In this case,
        # it's "cars".

        self.assertQuerysetEqual(
            Car._default_manager.order_by("name"), [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name
        )
