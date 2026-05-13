#!/usr/bin/python3
# coding:utf-8

from unittest import TestCase
from unittest import main

from xkits_file.template import Variable


class TestVariable(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.variable = Variable(1, 2, name="Alias", age=30)

    def tearDown(self):
        pass

    def test_iter(self):
        self.assertEqual(list(self.variable), [1, 2])

    def test_getitem_and_setitem(self):
        self.assertEqual(self.variable["name"], "Alias")
        self.assertEqual(self.variable["age"], 30)
        self.variable["name"] = "Beta"
        self.variable["age"] = 25
        self.assertEqual(self.variable["name"], "Beta")
        self.assertEqual(self.variable["age"], 25)

    def test_duplicate(self):
        new_variable = self.variable.duplicate(3, name="Gamma", city="New York")  # noqa:E501
        self.assertIsInstance(new_variable, Variable)
        self.assertEqual(list(new_variable), [1, 2, 3])
        self.assertEqual(new_variable["name"], "Gamma")
        self.assertEqual(new_variable["age"], 30)
        self.assertEqual(new_variable["city"], "New York")
        # Ensure original variable is unchanged
        self.assertEqual(self.variable["name"], "Alias")
        self.assertEqual(self.variable["age"], 30)
        self.assertIsNone(self.variable["city"])


if __name__ == "__main__":
    main()
