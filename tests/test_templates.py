# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Templates: saved with their lines, read back the same, never deleted."""

import glob
import os
import shutil
import tempfile
import unittest

from dbms import DBMS
from memory_log import MemoryLog
from templates import Templates

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_scripts():
    scripts = []
    for folder in ("ddl", "dml"):
        pattern = os.path.join(PROJECT_DIR, "sql", folder, "*.sql")
        scripts.extend(sorted(glob.glob(pattern)))
    return scripts


LINES = [{"kind": "text", "content": "PBS 1X", "height_mm": 5.0,
          "align": "C"},
         {"kind": "text", "content": "", "height_mm": 3.5, "align": "C"},
         {"kind": "barcode", "content": "0042", "height_mm": 8.0,
          "align": "C", "symbology": "I2OF5", "human_readable": True}]


class TestTemplates(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.log = MemoryLog()
        self.db = DBMS(os.path.join(self.folder, "test.sl3"), self.log)
        self.db.create(get_scripts())
        self.db.set_connection()
        self.templates = Templates(self.db, self.log)

    def tearDown(self):
        self.db.close_connection()
        shutil.rmtree(self.folder)

    def test_a_template_comes_back_as_it_was_saved_without_empty_lines(self):
        template_id = self.templates.save("PBS", 1, LINES)
        self.assertEqual(self.templates.get_elements(template_id),
                         [LINES[0], LINES[2]])

    def test_saving_again_under_the_same_name_replaces_the_lines(self):
        first = self.templates.save("PBS", 1, LINES)
        second = self.templates.save("PBS", 1, LINES[:1])
        self.assertEqual(first, second)
        self.assertEqual(self.templates.get_elements(first), LINES[:1])
        self.assertEqual(len(self.templates.get_all()), 1)

    def test_the_old_lines_are_kept_disabled_not_deleted(self):
        template_id = self.templates.save("PBS", 1, LINES)
        self.templates.save("PBS", 1, LINES[:1])
        count = self.db.read_one(
            "SELECT COUNT(*) FROM template_elements WHERE template_id = ?",
            (template_id,))[0]
        self.assertEqual(count, 3)

    def test_a_disabled_template_is_out_of_the_list_but_in_the_file(self):
        template_id = self.templates.save("PBS", 1, LINES)
        self.templates.disable(template_id)
        self.assertEqual(self.templates.get_all(), [])
        row = self.db.get_selected("templates", "template_id", template_id)
        self.assertEqual(row["enable"], 0)

    def test_a_template_with_no_lines_is_refused(self):
        with self.assertRaises(ValueError):
            self.templates.save("Empty", 1, [LINES[1]])

    def test_a_template_with_no_name_is_refused(self):
        with self.assertRaises(ValueError):
            self.templates.save("  ", 1, LINES)

    def test_a_failure_halfway_leaves_nothing_behind(self):
        wrong = LINES + [{"kind": "barcode", "content": "1",
                          "height_mm": 8.0, "align": "C",
                          "symbology": "NOPE", "human_readable": True}]
        with self.assertRaises(ValueError):
            self.templates.save("Broken", 1, wrong)
        self.assertEqual(self.templates.get_all(), [])

    def test_the_log_has_the_id_and_not_the_text(self):
        self.templates.save("Rossi Mario", 1, LINES)
        self.assertNotIn("Rossi", self.log.entries[-1][1])
        self.assertNotIn("PBS", self.log.entries[-1][1])


if __name__ == "__main__":
    unittest.main()
