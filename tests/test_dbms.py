# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The database: made from sql/, checked, and refusing what it should."""

import glob
import os
import shutil
import sqlite3
import tempfile
import unittest

from dbms import DBMS
from memory_log import MemoryLog
from version import SCHEMA_VERSION

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_scripts(folders=("ddl", "dml", "migrations")):
    scripts = []
    for folder in folders:
        pattern = os.path.join(PROJECT_DIR, "sql", folder, "*.sql")
        scripts.extend(sorted(glob.glob(pattern)))
    return scripts


class TestDBMS(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.log = MemoryLog()
        self.db = DBMS(os.path.join(self.folder, "test.sl3"), self.log)
        self.db.create(get_scripts())
        self.db.set_connection()

    def tearDown(self):
        self.db.close_connection()
        shutil.rmtree(self.folder)

    def add_template(self):
        sql, args = self.db.get_insert(
            "templates", {"format_id": 1, "description": "PBS 1X",
                          "enable": 1})
        return self.db.write(sql, args)

    def get_element(self, template_id, kind, symbology_id):
        return {"template_id": template_id, "symbology_id": symbology_id,
                "position": 1, "kind": kind, "content": "0123456789",
                "height_mm": 8.0, "align": "C", "human_readable": 1,
                "enable": 1}

    def test_new_database_has_the_program_schema_version(self):
        self.db.check_schema_version(SCHEMA_VERSION)
        self.db.check_integrity()

    def test_create_refuses_an_existing_file(self):
        with self.assertRaises(IOError):
            self.db.create(get_scripts())

    def test_another_schema_version_is_refused(self):
        with self.assertRaises(ValueError):
            self.db.check_schema_version(SCHEMA_VERSION + 1)

    def test_seed_has_the_50_by_30_format(self):
        row = self.db.read_one("SELECT width_mm, height_mm FROM formats")
        self.assertEqual((row["width_mm"], row["height_mm"]), (50, 30))

    def test_a_barcode_element_is_stored(self):
        template_id = self.add_template()
        values = self.get_element(template_id, "barcode", 1)
        sql, args = self.db.get_insert("template_elements", values)
        self.assertIsNotNone(self.db.write(sql, args))

    def test_a_barcode_without_symbology_is_refused(self):
        template_id = self.add_template()
        values = self.get_element(template_id, "barcode", None)
        sql, args = self.db.get_insert("template_elements", values)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.write(sql, args)

    def test_a_text_line_with_a_symbology_is_refused(self):
        template_id = self.add_template()
        values = self.get_element(template_id, "text", 1)
        sql, args = self.db.get_insert("template_elements", values)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.write(sql, args)

    def test_a_template_on_a_missing_format_is_refused(self):
        sql, args = self.db.get_insert(
            "templates", {"format_id": 99, "description": "x", "enable": 1})
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.write(sql, args)

    def test_an_unknown_column_is_refused_by_name(self):
        with self.assertRaises(ValueError) as caught:
            self.db.get_insert("templates", {"format_id": 1,
                                             "description": "x",
                                             "enable": 1, "colour": "red"})
        self.assertIn("colour", str(caught.exception))

    def test_a_failed_read_raises_rather_than_returning_no_rows(self):
        with self.assertRaises(sqlite3.Error):
            self.db.read_all("SELECT * FROM no_such_table")
        self.assertEqual(self.log.entries[-1][0], "ERROR")

    def test_a_format_may_have_no_band(self):
        row = self.db.read_one(
            "SELECT section_band_mm FROM formats WHERE description = ?",
            ("40 x 10",))
        self.assertEqual(row["section_band_mm"], 0)

    def test_a_negative_band_is_still_refused(self):
        sql, args = self.db.get_insert(
            "formats", {"description": "x", "width_mm": 40,
                        "height_mm": 10, "margin_mm": 1,
                        "section_band_mm": -1, "enable": 1})
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.write(sql, args)


class TestMigration(unittest.TestCase):
    """A database of schema version 1, in service, brought up to date."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.log = MemoryLog()
        self.db = DBMS(os.path.join(self.folder, "test.sl3"), self.log)
        self.db.create(get_scripts(("ddl", "dml")))
        self.db.set_connection()
        sql, args = self.db.get_insert(
            "templates", {"format_id": 1, "description": "PBS 1X",
                          "enable": 1})
        self.template_id = self.db.write(sql, args)
        self.db.migrate(get_scripts(("migrations",)))

    def tearDown(self):
        self.db.close_connection()
        shutil.rmtree(self.folder)

    def test_it_reaches_the_program_schema_version_and_is_sound(self):
        self.db.check_schema_version(SCHEMA_VERSION)
        self.db.check_integrity()

    def test_the_templates_still_point_at_their_format(self):
        row = self.db.read_one(
            """SELECT f.description
                 FROM templates AS t
                 JOIN formats AS f ON f.format_id = t.format_id
                WHERE t.template_id = ?""", (self.template_id,))
        self.assertEqual(row["description"], "50 x 30")

    def test_foreign_keys_are_enforced_again(self):
        sql, args = self.db.get_insert(
            "templates", {"format_id": 99, "description": "x", "enable": 1})
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.write(sql, args)

    def test_a_copy_of_the_old_file_is_taken_first(self):
        copies = glob.glob(os.path.join(self.folder, "test.sl3.v1.*.bak"))
        self.assertEqual(len(copies), 1)


if __name__ == "__main__":
    unittest.main()
