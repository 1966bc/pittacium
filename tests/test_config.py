# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The .ini reader: values, refusals, and comments that survive a change."""

import os
import shutil
import tempfile
import unittest

from config import Config

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "test.ini")

    def tearDown(self):
        shutil.rmtree(self.folder)

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_the_example_settings_are_readable(self):
        example = os.path.join(PROJECT_DIR, "pittacium.ini.example")
        config = Config(example)
        self.assertEqual(config.get("label", "section"), "Lab")

    def test_a_line_that_is_not_a_setting_is_refused_with_its_number(self):
        self.write("[label]\nsection = Lab\nnonsense\n")
        with self.assertRaises(ValueError) as caught:
            Config(self.path)
        self.assertIn("line 3", str(caught.exception))

    def test_a_missing_key_is_refused(self):
        self.write("[label]\nsection = Lab\n")
        with self.assertRaises(ValueError):
            Config(self.path).get("label", "colour")

    def test_set_keeps_the_comments(self):
        self.write("[label]\n; the section\nsection = Lab\n")
        Config(self.path).set("label", "section", "Corelab")
        config = Config(self.path)
        self.assertEqual(config.get("label", "section"), "Corelab")
        self.assertIn("; the section\n", config.lines)


if __name__ == "__main__":
    unittest.main()
