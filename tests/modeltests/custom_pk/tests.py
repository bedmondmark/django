# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import transaction, IntegrityError
from django.test import TestCase, skipIfDBFeature

from .models import Employee, Business, Bar, Foo


class CustomPKTests(TestCase):
    def setUp(self):
        self.dan = Employee.objects.create(
            employee_code=123, first_name="Dan", last_name="Jones"
        )
        self.fran = Employee.objects.create(
            employee_code=456, first_name="Fran", last_name="Bones"
        )

    def test_objects_with_custom_pk_created_successfully(self):
        self.assertQuerysetEqual(
            Employee.objects.all(), [
                "Fran Bones",
                "Dan Jones",
            ],
            unicode
        )

    def test_pk_param_to_get_associated_correctly(self):
        self.assertEqual(Employee.objects.get(pk=123), self.dan)
        self.assertEqual(Employee.objects.get(pk=456), self.fran)

    def test_exception_raised_if_employee_non_existent(self):
        self.assertRaises(Employee.DoesNotExist,
            lambda: Employee.objects.get(pk=42)
        )

    def test_get_by_explicit_primary_key(self):
        # Use the name of the primary key, rather than pk.
        self.assertEqual(Employee.objects.get(employee_code=123), self.dan)

    def test_filter_with_pk(self):
        # pk can be used as a substitute for the primary key.
        self.assertQuerysetEqual(
            Employee.objects.filter(pk__in=[123, 456]), [
                "Fran Bones",
                "Dan Jones",
                ],
            unicode
        )

    def test_get_with_pk_param(self):
        # The primary key can be accessed via the pk property on the model.
        e = Employee.objects.get(pk=123)
        self.assertEqual(e.pk, 123)
        # Or we can use the real attribute name for the primary key:
        self.assertEqual(e.employee_code, 123)

    def test_modify_existing_object(self):
        # Fran got married and changed her last name.
        fran = Employee.objects.get(pk=456)
        fran.last_name = "Jones"
        fran.save()

        self.assertQuerysetEqual(
            Employee.objects.filter(last_name="Jones"), [
                "Dan Jones",
                "Fran Jones",
                ],
            unicode
        )


class CustomPKRelationshipTests(TestCase):
    def setUp(self):
        self.dan = Employee.objects.create(
            employee_code=123, first_name="Dan", last_name="Jones"
        )
        self.fran = Employee.objects.create(
            employee_code=456, first_name="Fran", last_name="Bones"
        )
        self.b = Business.objects.create(name="Sears")
        self.b.employees.add(self.dan, self.fran)

    def test_m2m_with_custom_pk(self):
        self.assertQuerysetEqual(
            self.b.employees.all(), [
                "Fran Bones",
                "Dan Jones",
                ],
            unicode
        )

    def test_reverse_m2m_with_custom_pk(self):
        self.assertQuerysetEqual(
            self.fran.business_set.all(), [
                "Sears",
                ],
            lambda b: b.name
        )

    def test_in_bulk(self):
        emps = Employee.objects.in_bulk([123, 456])
        self.assertEqual(emps[123], self.dan)
        self.assertEqual(Business.objects.in_bulk(["Sears"]), {
            "Sears": self.b,
        })

    def test_filter_with_custom_key_and_custom_type(self):
        self.assertQuerysetEqual(
            Business.objects.filter(name="Sears"), [
                "Sears"
            ],
            lambda b: b.name
        )

    def test_filter_with_pk_and_custom_type(self):
        self.assertQuerysetEqual(
            Business.objects.filter(pk="Sears"), [
                "Sears",
                ],
            lambda b: b.name
        )

    def test_filter_with_related_custom_key_value(self):
        # Queries across tables, involving primary key
        self.assertQuerysetEqual(
            Employee.objects.filter(business__name="Sears"), [
                "Fran Bones",
                "Dan Jones",
                ],
            unicode,
        )
        self.assertQuerysetEqual(
            Business.objects.filter(employees__employee_code=123), [
                "Sears",
                ],
            lambda b: b.name
        )

    def test_filter_with_related_pk_value(self):
        self.assertQuerysetEqual(
            Employee.objects.filter(business__pk="Sears"), [
                "Fran Bones",
                "Dan Jones",
                ],
            unicode,
        )
        self.assertQuerysetEqual(
            Business.objects.filter(employees__pk=123), [
                "Sears",
                ],
            lambda b: b.name,
        )

    def test_filter_with_related_custom_key_comparison(self):
        self.assertQuerysetEqual(
            Business.objects.filter(employees__first_name__startswith="Fran"), [
                "Sears",
            ],
            lambda b: b.name
        )

    def test_unicode_pk(self):
        # Primary key may be unicode string
        bus = Business.objects.create(name='jaźń')

    def test_unique_pk(self):
        # The primary key must also obviously be unique, so trying to create a
        # new object with the same primary key will fail.
        self.assertRaises(IntegrityError,
            Employee.objects.create, employee_code=123, first_name="Fred", last_name="Jones"
        )

    def test_custom_field_pk(self):
        # Regression for #10785 -- Custom fields can be used for primary keys.
        new_bar = Bar.objects.create()
        new_foo = Foo.objects.create(bar=new_bar)

        f = Foo.objects.get(bar=new_bar.pk)
        self.assertEqual(f, new_foo)
        self.assertEqual(f.bar, new_bar)

        f = Foo.objects.get(bar=new_bar)
        self.assertEqual(f, new_foo),
        self.assertEqual(f.bar, new_bar)

    # SQLite lets objects be saved with an empty primary key, even though an
    # integer is expected. So we can't check for an error being raised in that
    # case for SQLite. Remove it from the suite for this next bit.
    @skipIfDBFeature('supports_unspecified_pk')
    def test_required_pk(self):
        # The primary key must be specified, so an error is raised if you
        # try to create an object without it.
        sid = transaction.savepoint()
        self.assertRaises(IntegrityError,
            Employee.objects.create, first_name="Tom", last_name="Smith"
        )
        transaction.savepoint_rollback(sid)
