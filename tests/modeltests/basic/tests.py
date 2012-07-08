from __future__ import absolute_import, unicode_literals

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import Field, FieldDoesNotExist
from django.test import TestCase, skipIfDBFeature, skipUnlessDBFeature
from django.utils.translation import ugettext_lazy

from .models import Article

class SingleModelTest(TestCase):
    """
    A bunch of basic tests that work with a single model instance.
    """

    def setUp(self):
        # Create an Article for use in the tests:
        a = Article(
            id=None,
            headline='Area man programs in Python',
            pub_date=datetime(2005, 7, 28),
        )

        # Save it into the database. You have to call save() explicitly.
        a.save()

        self.test_model = a

    def test_model_instance_updated_correctly_after_save(self):
        """
        Ensure that after saving, the model instance has been updated.
        """
        a = self.test_model

        # Now it has an ID.
        self.assertTrue(a.id != None)

        # Models have a pk property that is an alias for the primary key
        # attribute (by default, the 'id' attribute).
        self.assertEqual(a.pk, a.id)

        # Access database columns via Python attributes.
        self.assertEqual(a.headline, 'Area man programs in Python')
        self.assertEqual(a.pub_date, datetime(2005, 7, 28, 0, 0))

    def test_model_updating_in_database(self):
        """
        Ensure that after updating an attribute and saving, newly loaded instances have the updated value.
        """
        a = self.test_model

        # Saving an object again doesn't create a new object -- it just saves
        # the old one.
        current_id = a.id
        a.save()
        self.assertEqual(a.id, current_id)

        # Change values by changing the attributes, then calling save().
        a.headline = 'Area woman programs in Python'
        a.save()

        self.assertEqual(a.id, current_id)
        # Article.objects.all() returns all the articles in the database.
        self.assertQuerysetEqual(Article.objects.all(),
            ['<Article: Area woman programs in Python>'])


    def test_model_objects_get(self):
        """
        Ensure that the saved instance can be loaded from the database using get on its attribute values.
        """
        a = self.test_model

        self.assertEqual(Article.objects.get(id__exact=a.id), a)
        self.assertEqual(Article.objects.get(headline__startswith='Area man'), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005, pub_date__month=7), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005, pub_date__month=7, pub_date__day=28), a)
        self.assertEqual(Article.objects.get(pub_date__week_day=5), a)
        # The "__exact" lookup type can be omitted, as a shortcut.
        self.assertEqual(Article.objects.get(id=a.id), a)
        self.assertEqual(Article.objects.get(headline='Area man programs in Python'), a)

    def test_model_objects_filter(self):
        """
        Ensure that filtering on attribute values return the expected model instances.
        """
        a = self.test_model

        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2005),
            ['<Article: Area man programs in Python>'],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2004),
            [],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2005, pub_date__month=7),
            ['<Article: Area man programs in Python>'],
        )

        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__week_day=5),
            ['<Article: Area man programs in Python>'],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__week_day=6),
            [],
        )
        # pk can be used as a shortcut for the primary key name in any query.
        self.assertQuerysetEqual(Article.objects.filter(pk__in=[a.id]),
            ["<Article: Area man programs in Python>"])

    def test_model_get_exceptions(self):
        """
        Ensure that the correct exceptions and error messages are raised when get cannot load the requested object.
        """

        # Django raises an Article.DoesNotExist exception for get() if the
        # parameters don't match any object.
        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            "Article matching query does not exist. Lookup parameters were "
            "{'id__exact': 2000}",
            Article.objects.get,
            id__exact=2000,
        )
        # To avoid dict-ordering related errors check only one lookup
        # in single assert.
        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            ".*'pub_date__year': 2005.*",
            Article.objects.get,
            pub_date__year=2005,
            pub_date__month=8,
        )
        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            ".*'pub_date__month': 8.*",
            Article.objects.get,
            pub_date__year=2005,
            pub_date__month=8,
        )

        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            "Article matching query does not exist. Lookup parameters were "
            "{'pub_date__week_day': 6}",
            Article.objects.get,
            pub_date__week_day=6,
        )

    def test_model_instances_with_identical_type_and_id_considered_equal(self):
        """
        Ensure model instances of the same type and same ID are considered equal.
        """
        article1 = Article.objects.get(pk=self.test_model.id)
        article2 = Article.objects.get(pk=self.test_model.id)
        self.assertEqual(article1, article2)

    def test_loaded_model_is_equal_to_original_instance(self):
        """
        Ensure that a model loaded from the database is considered equal to the original instance.
        """
        a = self.test_model
        self.assertEqual(Article.objects.get(pk=a.id), a)


class TestModelInstantiation(TestCase):
    """
    A bunch of tests which test model instantiation.
    """

    def test_model_instantiation_with_positional_params(self):
        """
        Ensure you can initialize a model instance using positional arguments.
        """
        article = Article(None, 'Second article', datetime(2005, 7, 29))
        article.save()
        self.assertEqual(article.headline, 'Second article')
        self.assertEqual(article.pub_date, datetime(2005, 7, 29, 0, 0))

    def test_model_instances_unique(self):
        """
        Ensure that models are saved with unique ids.
        """
        a = Article(
            id=None,
            headline='Area man programs in Python',
            pub_date=datetime(2005, 7, 28),
        )
        a.save()

        a2 = Article(None, 'Second article', datetime(2005, 7, 29))
        a2.save()

        a3 = Article(
            id=None,
            headline='Third article',
            pub_date=datetime(2005, 7, 30),
        )
        a3.save()

        self.assertNotEqual(a2.id, a.id)
        self.assertNotEqual(a3.id, a.id)
        self.assertNotEqual(a3.id, a2.id)

    def test_model_instantiation_with_named_params(self):
        """
        Ensure instances can be created using named params.
        """
        a = Article(
            id=None,
            headline='Third article',
            pub_date=datetime(2005, 7, 30),
        )
        a.save()
        self.assertEqual(a.headline, 'Third article')
        self.assertEqual(a.pub_date, datetime(2005, 7, 30, 0, 0))

    def test_model_instantiation_with_mixed_params(self):
        """
        Ensure instances can be created using mixed params.
        """
        # You can also mix and match position and keyword arguments, but
        # be sure not to duplicate field information.
        a = Article(None, 'Fourth article', pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, 'Fourth article')

    def test_model_instantiation_with_invalid_keyword_arguments(self):
        """
        Attempting to instantiate a model with an invalid keyword argument raises a TypeError.
        """
        self.assertRaisesRegexp(
            TypeError,
            "'foo' is an invalid keyword argument for this function",
            Article,
            id=None,
            headline='Invalid',
            pub_date=datetime(2005, 7, 31),
            foo='bar',
        )

    def test_autofield_set_when_missing_from_constructor_call(self):
        """
        You can leave off the value for an AutoField when creating an object, because it'll get filled in automatically when you save().
        """
        # id is an autofield, and is not provided in the following call:
        a = Article(headline='Article 6', pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, 'Article 6')

    def test_default_field_set_when_missing_from_constructor_call(self):
        """
        Ensure that if you leave off a field with "default" set, Django will use the default.
        """
        a = Article(pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, 'Default headline')

    def test_partial_datetime_params(self):
        """
        Ensure that Django stores imprecise datetime information.
        """
        a1 = Article(
            headline='Article 7',
            pub_date=datetime(2005, 7, 31, 12, 30),
        )
        a1.save()
        self.assertEqual(Article.objects.get(id__exact=a1.id).pub_date,
            datetime(2005, 7, 31, 12, 30))

        a2 = Article(
            headline='Article 8',
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a2.save()
        self.assertEqual(Article.objects.get(id__exact=a2.id).pub_date,
            datetime(2005, 7, 31, 12, 30, 45))


class ObjectDateTest(TestCase):
    def setUp(self):
        # Create four articles published on sequential days:
        for i, d in enumerate(range(28, 32)):
            article = Article(
                headline = "Article {0}".format(i+1),
                pub_date = datetime(2005, 7, d)
            )
            article.save()

    def test_objects_dates(self):
        """
        Ensure dates() returns a list of available dates of the given scope for the given field.
        """
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'year'),
            ["datetime.datetime(2005, 1, 1, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'month'),
            ["datetime.datetime(2005, 7, 1, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day'),
            ["datetime.datetime(2005, 7, 28, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 31, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day', order='ASC'),
            ["datetime.datetime(2005, 7, 28, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 31, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day', order='DESC'),
            ["datetime.datetime(2005, 7, 31, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 28, 0, 0)"])

    def test_objects_dates_iterator(self):
        """
        Ensure dates iterator method works.
        """
        dates = []
        for article in Article.objects.dates('pub_date', 'day', order='DESC').iterator():
            dates.append(article)
        self.assertEqual(dates, [
            datetime(2005, 7, 31, 0, 0),
            datetime(2005, 7, 30, 0, 0),
            datetime(2005, 7, 29, 0, 0),
            datetime(2005, 7, 28, 0, 0)])

    def test_objects_dates_exceptions(self):
        """
        Ensure calling dates() with invalid arguments raises the correct exceptions.
        """
        self.assertRaisesRegexp(
            TypeError,
            "dates\(\) takes at least 3 arguments \(1 given\)",
            Article.objects.dates,
        )

        self.assertRaisesRegexp(
            FieldDoesNotExist,
            "Article has no field named 'invalid_field'",
            Article.objects.dates,
            "invalid_field",
            "year",
        )

        self.assertRaisesRegexp(
            AssertionError,
            "'kind' must be one of 'year', 'month' or 'day'.",
            Article.objects.dates,
            "pub_date",
            "bad_kind",
        )

        self.assertRaisesRegexp(
            AssertionError,
            "'order' must be either 'ASC' or 'DESC'.",
            Article.objects.dates,
            "pub_date",
            "year",
            order="bad order",
        )

class MultipleModelTest(TestCase):
    def setUp(self):
        self.a1 = Article(None, 'Article 1', datetime(2005, 7, 31, 12, 28))
        self.a2 = Article(None, 'Article 2', datetime(2005, 7, 31, 12, 29))
        self.a3 = Article(None, 'Article 3', datetime(2005, 7, 31, 12, 30))
        self.a1.save()
        self.a2.save()
        self.a3.save()
        Article(None, 'Article 4', datetime(2005, 7, 31, 12, 31)).save()

        self.s1 = Article.objects.filter(id__exact=self.a1.id)
        self.s2 = Article.objects.filter(id__exact=self.a2.id)
        self.s3 = Article.objects.filter(id__exact=self.a3.id)

    def test_combine_queries_with_or(self):
        self.assertQuerysetEqual(self.s1 | self.s2,
            ["<Article: Article 1>",
             "<Article: Article 2>"])

    def test_combine_queries_with_and(self):
        self.assertQuerysetEqual(self.s1 & self.s2, [])

    def test_get_queryset_len(self):
        # You can get the number of objects like this:
        self.assertEqual(len(Article.objects.filter(id__exact=self.a1.id)), 1)

    def test_queryset_indexes(self):
        self.assertEqual(Article.objects.all()[0], self.a1)

    def test_queryset_slicing_with_ints(self):
        self.assertQuerysetEqual(Article.objects.all()[1:3],
            ["<Article: Article 2>", "<Article: Article 3>"])
        self.assertQuerysetEqual((self.s1 | self.s2 | self.s3)[::2],
            ["<Article: Article 1>",
             "<Article: Article 3>"])

    def test_queryset_slicing_with_longs(self):
        self.assertEqual(Article.objects.all()[0L], self.a1)
        self.assertQuerysetEqual(Article.objects.all()[1L:3L],
            ["<Article: Article 2>", "<Article: Article 3>"])
        self.assertQuerysetEqual((self.s1 | self.s2 | self.s3)[::2L],
            ["<Article: Article 1>",
             "<Article: Article 3>"])

    def test_queryset_slicing_with_mixed_types(self):
        # And can be mixed with ints.
        self.assertQuerysetEqual(Article.objects.all()[1:3L],
            ["<Article: Article 2>", "<Article: Article 3>"])

    def test_queryset_slice_filter(self):
        # Slices (without step) are lazy:
        self.assertQuerysetEqual(Article.objects.all()[0:5].filter(),
            ["<Article: Article 1>",
             "<Article: Article 2>",
             "<Article: Article 3>",
             "<Article: Article 4>"])

    def test_slicing_queryset_slices(self):
        # Slicing again works:
        self.assertQuerysetEqual(Article.objects.all()[0:4][0:2],
            ["<Article: Article 1>",
             "<Article: Article 2>"])
        self.assertQuerysetEqual(Article.objects.all()[0:4][:2],
            ["<Article: Article 1>",
             "<Article: Article 2>"])
        self.assertQuerysetEqual(Article.objects.all()[0:4][3:],
            ["<Article: Article 4>"])
        self.assertQuerysetEqual(Article.objects.all()[0:4][4:], [])

        # Some more tests!
        self.assertQuerysetEqual(Article.objects.all()[1:][0:2],
            ["<Article: Article 2>", "<Article: Article 3>"])
        self.assertQuerysetEqual(Article.objects.all()[1:][:2],
            ["<Article: Article 2>", "<Article: Article 3>"])
        self.assertQuerysetEqual(Article.objects.all()[1:][1:2],
            ["<Article: Article 3>"])

        # Using an offset without a limit is also possible.
        self.assertQuerysetEqual(Article.objects.all()[1:],
            ["<Article: Article 2>",
             "<Article: Article 3>",
             "<Article: Article 4>"])

    def test_reorder_slice_exception(self):
        self.assertRaisesRegexp(
            AssertionError,
            "Cannot reorder a query once a slice has been taken.",
            Article.objects.all()[0:5].order_by,
            'id',
        )

    def test_filter_slice_exception(self):
        self.assertRaisesRegexp(
            AssertionError,
            "Cannot filter a query once a slice has been taken.",
            Article.objects.all()[0:5].filter,
            id=self.a1.id,
        )

    def test_combine_slice_exception(self):
        self.assertRaisesRegexp(
            AssertionError,
            "Cannot combine queries once a slice has been taken.",
            lambda: Article.objects.all()[0:1] & Article.objects.all()[4:5],
        )

    def test_negative_slice_exception(self):
        # Negative slices are not supported, due to database constraints.
        # (hint: inverting your ordering might do what you need).
        self.assertRaisesRegexp(
            AssertionError,
            "Negative indexing is not supported.",
            lambda: Article.objects.all()[-1]
        )

    def test_article_instance_has_no_objects_attribute(self):
        # An Article instance doesn't have access to the "objects" attribute.
        # That's only available on the class.
        self.assertRaisesRegexp(
            AttributeError,
            "Manager isn't accessible via Article instances",
            getattr,
            self.a1,
            "objects",
        )

    def test_bulk_delete(self):
        # Bulk delete test: How many objects before and after the delete?
        self.assertQuerysetEqual(Article.objects.all(),
            ["<Article: Article 1>",
             "<Article: Article 2>",
             "<Article: Article 3>",
             "<Article: Article 4>"])

        Article.objects.filter(id__lte=self.a2.id).delete()
        self.assertQuerysetEqual(Article.objects.all(),
            ["<Article: Article 3>",
             "<Article: Article 4>"])

    def test_instance_equality(self):
        # Check that != and == operators behave as expected on instances
        a1 = self.a1
        a2 = self.a2

        self.assertTrue(a1 != a2)
        self.assertFalse(a1 == a2)
        self.assertEqual(a2, Article.objects.get(id__exact=a2.id))

        self.assertTrue(Article.objects.get(id__exact=a2.id) != Article.objects.get(id__exact=a1.id))
        self.assertFalse(Article.objects.get(id__exact=a2.id) == Article.objects.get(id__exact=a1.id))

    def test_in_operator_with_queryset(self):
        # You can use 'in' to test for membership...
        self.assertTrue(self.a2 in Article.objects.all())

    def test_queryset_exists(self):
        # there will often be more efficient ways if that is all you need:
        self.assertTrue(Article.objects.filter(id=self.a2.id).exists())


class ModelTest(TestCase):
    @skipUnlessDBFeature('supports_microsecond_precision')
    def test_microsecond_precision(self):
        # In PostgreSQL, microsecond-level precision is available.
        a9 = Article(
            headline='Article 9',
            pub_date=datetime(2005, 7, 31, 12, 30, 45, 180),
        )
        a9.save()
        self.assertEqual(Article.objects.get(pk=a9.pk).pub_date,
            datetime(2005, 7, 31, 12, 30, 45, 180))

    @skipIfDBFeature('supports_microsecond_precision')
    def test_microsecond_precision_not_supported(self):
        # In MySQL, microsecond-level precision isn't available. You'll lose
        # microsecond-level precision once the data is saved.
        a9 = Article(
            headline='Article 9',
            pub_date=datetime(2005, 7, 31, 12, 30, 45, 180),
        )
        a9.save()
        self.assertEqual(Article.objects.get(id__exact=a9.id).pub_date,
            datetime(2005, 7, 31, 12, 30, 45))

    def test_manually_specify_primary_key(self):
        # You can manually specify the primary key when creating a new object.
        a101 = Article(
            id=101,
            headline='Article 101',
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a101.save()
        a101 = Article.objects.get(pk=101)
        self.assertEqual(a101.headline, 'Article 101')

    def test_create_method(self):
        # You can create saved objects in a single step
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        self.assertEqual(Article.objects.get(headline="Article 10"), a10)

    def test_year_lookup_edge_case(self):
        # Edge-case test: A year lookup should retrieve all objects in
        # the given year, including Jan. 1 and Dec. 31.
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )
        self.assertQuerysetEqual(Article.objects.filter(pub_date__year=2008),
            ["<Article: Article 11>", "<Article: Article 12>"])

    def test_unicode_data(self):
        # Unicode data works, too.
        a = Article(
            headline='\u6797\u539f \u3081\u3050\u307f',
            pub_date=datetime(2005, 7, 28),
        )
        a.save()
        self.assertEqual(Article.objects.get(pk=a.id).headline,
            '\u6797\u539f \u3081\u3050\u307f')

    def test_hash_function(self):
        # Model instances have a hash function, so they can be used in sets
        # or as dictionary keys. Two models compare as equal if their primary
        # keys are equal.
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        s = set([a10, a11, a12])
        self.assertTrue(Article.objects.get(headline='Article 11') in s)

    def test_field_ordering(self):
        """
        Field instances have a `__lt__` comparison function to define an
        ordering based on their creation. Prior to #17851 this ordering
        comparison relied on the now unsupported `__cmp__` and was assuming
        compared objects were both Field instances raising `AttributeError`
        when it should have returned `NotImplemented`.
        """
        f1 = Field()
        f2 = Field(auto_created=True)
        f3 = Field()
        self.assertTrue(f2 < f1)
        self.assertTrue(f3 > f1)
        self.assertFalse(f1 == None)
        self.assertFalse(f2 in (None, 1, ''))

    def test_extra_method_select_argument_with_dashes_and_values(self):
        # The 'select' argument to extra() supports names with dashes in
        # them, as long as you use values().
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        dicts = Article.objects.filter(
            pub_date__year=2008).extra(
                select={'dashed-value': '1'}
            ).values('headline', 'dashed-value')
        self.assertEqual([sorted(d.items()) for d in dicts],
            [[('dashed-value', 1), ('headline', 'Article 11')], [('dashed-value', 1), ('headline', 'Article 12')]])

    def test_extra_method_select_argument_with_dashes(self):
        # If you use 'select' with extra() and names containing dashes on a
        # query that's *not* a values() query, those extra 'select' values
        # will silently be ignored.
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        articles = Article.objects.filter(
            pub_date__year=2008).extra(
                select={'dashed-value': '1', 'undashedvalue': '2'})
        self.assertEqual(articles[0].undashedvalue, 2)

    def test_create_relation_with_ugettext_lazy(self):
        """
        Test that ugettext_lazy objects work when saving model instances
        through various methods. Refs #10498.
        """
        notlazy = 'test'
        lazy = ugettext_lazy(notlazy)
        reporter = Article.objects.create(headline=lazy, pub_date=datetime.now())
        article = Article.objects.get()
        self.assertEqual(article.headline, notlazy)
        # test that assign + save works with Promise objecs
        article.headline = lazy
        article.save()
        self.assertEqual(article.headline, notlazy)
        # test .update()
        Article.objects.update(headline=lazy)
        article = Article.objects.get()
        self.assertEqual(article.headline, notlazy)
        # still test bulk_create()
        Article.objects.all().delete()
        Article.objects.bulk_create([Article(headline=lazy, pub_date=datetime.now())])
        article = Article.objects.get()
        self.assertEqual(article.headline, notlazy)
