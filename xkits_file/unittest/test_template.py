#!/usr/bin/python3
# coding:utf-8

from unittest import TestCase
from unittest import main
from unittest.mock import mock_open
from unittest.mock import patch

from xkits_file.template import Template
from xkits_file.template import Variable


class FakeTemplate(Template):
    PRESET = "[{}] Hello, {name}!"


class TestVariable(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.template = FakeTemplate()

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

    def test_populate(self):
        self.assertEqual(Variable(1, name="Alpha").populate(self.template), "[1] Hello, Alpha!")  # noqa:E501
        self.assertEqual(Variable(2, name="World").populate(self.template), "[2] Hello, World!")  # noqa:E501


class TestTemplate(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_format(self):
        with patch("builtins.open", mock_open(read_data="Hello, {name}!")) as mocked_file:  # noqa:E501
            template = Template.from_file("dummy.txt")
            self.assertEqual(template.format(1, name="Alpha"), "Hello, Alpha!")  # noqa:E501
            self.assertEqual(template.format(2, name="World"), "Hello, World!")  # noqa:E501
            mocked_file.assert_called_once_with("dummy.txt", "r", encoding="utf-8")  # noqa:E501


if __name__ == "__main__":
    main()
