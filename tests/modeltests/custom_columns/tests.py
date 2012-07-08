from __future__ import absolute_import

from django.core.exceptions import FieldError
from django.test import TestCase

from .models import Author, Article


class CustomColumnsTests(TestCase):
    def setUp(self):
        # Although the table and column names on Author have been set to custom
        # values, nothing about using the Author model has changed...
        a1 = Author.objects.create(first_name="John", last_name="Smith")
        a2 = Author.objects.create(first_name="Peter", last_name="Jones")

        art = Article.objects.create(headline="Django lets you build Web apps easily")
        art.authors = [a1, a2]

        self.a1 = a1
        self.art = art

    def test_objects_saved_correctly(self):
        self.assertQuerysetEqual(
            Author.objects.all(), [
                "Peter Jones", "John Smith",
                ],
            unicode
        )

    def test_obtain_with_filter(self):
        self.assertQuerysetEqual(
            Author.objects.filter(first_name__exact="John"), [
                "John Smith",
                ],
            unicode
        )

    def test_obtain_with_get(self):
        self.assertEqual(
            Author.objects.get(first_name__exact="John"),
            self.a1,
        )

    def test_field_error_raised_if_filter_param_incorrect(self):
        self.assertRaises(FieldError,
            lambda: Author.objects.filter(firstname__exact="John")
        )

    def test_attribute_error_raised_when_attribute_name_is_incorrect(self):
        a = Author.objects.get(last_name__exact="Smith")
        a.first_name = "John"
        a.last_name = "Smith"

        self.assertRaises(AttributeError, lambda: a.firstname)
        self.assertRaises(AttributeError, lambda: a.last)

    def test_many_to_many_all(self):
        # Although the Article table uses a custom m2m table,
        # nothing about using the m2m relationship has changed...

        # Get all the authors for an article
        self.assertQuerysetEqual(
            self.art.authors.all(), [
                "Peter Jones",
                "John Smith",
                ],
            unicode
        )

    def test_many_to_many_reverse_all(self):
        # Although the Article table uses a custom m2m table,
        # nothing about using the m2m relationship has changed...

        # Get the articles for an author
        author = Author.objects.get(last_name__exact="Smith")
        self.assertQuerysetEqual(
            author.article_set.all(), [
                "Django lets you build Web apps easily",
                ],
            lambda a: a.headline
        )


    def test_db_column(self):

        # Query the authors across the m2m relation
        self.assertQuerysetEqual(
            self.art.authors.filter(last_name='Jones'), [
                "Peter Jones"
            ],
            unicode
        )
