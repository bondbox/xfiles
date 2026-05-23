#!/usr/bin/python3
# coding:utf-8

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest import main
from unittest.mock import mock_open
from unittest.mock import patch

from xkits_file.template import Template
from xkits_file.template import TemplateManagerPath
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
        self.assertEqual(self.variable["age"], 30)
        self.variable.set_default("city", "Shanghai")
        self.variable.set_default("city", "New York")
        self.variable["name"] = "Beta"
        self.variable["age"] = 25
        self.assertEqual(self.variable["city"], "Shanghai")
        self.assertEqual(self.variable["name"], "Beta")
        self.assertEqual(self.variable["age"], 25)

    def test_duplicate(self):
        new_variable = self.variable.duplicate(3, name="Gamma", city="New York")  # noqa:E501
        self.assertIsInstance(new_variable, Variable)
        self.assertEqual(list(new_variable), [1, 2, 3])
        self.assertEqual(new_variable["city"], "New York")
        self.assertEqual(new_variable["name"], "Gamma")
        self.assertEqual(new_variable["age"], 30)
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
        template = Template(text="Hello, {name}!")
        self.assertEqual(template.format(1, name="Alpha"), "Hello, Alpha!")
        self.assertEqual(template.format(2, name="World"), "Hello, World!")

    def test_load(self):
        with patch("builtins.open", mock_open(read_data="Hello, {name}!")) as mocked_file:  # noqa:E501
            Template.load(filepath="dummy.old")
            mocked_file.assert_called_once_with("dummy.old", "r", encoding="utf-8")  # noqa:E501

    def test_save(self):
        with TemporaryDirectory() as tmpdir:
            filepath: Path = Path(tmpdir) / "unittest" / "fake" / "dummy.new"
            Template(text="Hello, {name}!").save(filepath=filepath.as_posix())
            self.assertTrue(filepath.is_file())


class TestTemplateManagerPath(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.templates = Path(__file__).parent / "templates"
        cls.name = "demo"

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.variables = Variable(name=self.name)
        self.template_manager = TemplateManagerPath(self.variables)
        self.template_manager.load(self.templates)

    def tearDown(self):
        pass

    def test_iter(self):
        for key, tpl in self.template_manager:
            self.assertIs(self.template_manager[key], tpl)

    def test_variable(self):
        self.assertIs(self.template_manager.variable, self.variables)

    def test_evaluate(self):
        for path, content in self.template_manager.evaluate():
            if path.name == "demo.txt":
                self.assertEqual(content, self.name)

    def test_scan_invalid_path(self):
        with self.assertRaises(ValueError):
            list(self.template_manager.scan(self.templates / "nonexistent"))

    def test_dump(self):
        with patch("builtins.open", mock_open()):
            self.template_manager.dump(self.templates, allow_update=True)


if __name__ == "__main__":
    main()
