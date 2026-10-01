# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Printer and Spooler: what goes out, what is written down, what is not."""

import os
import shutil
import tempfile
import unittest

from config import Config
from layout import Layout
from memory_log import MemoryLog
from printer import Printer
from spooler import Spooler

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET = "Rossi Mario"


class TestPrinter(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.log = MemoryLog()
        example = os.path.join(PROJECT_DIR, "pittacium.ini.example")
        self.printer = Printer(Config(example), self.folder, self.log)
        self.layout = Layout(50, 30, 1.5, 4.0, self.printer.dpi)
        line = {"kind": "text", "content": SECRET, "height_mm": 4.0,
                "align": "C"}
        self.items = self.layout.get_items([line], "Lab")

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_the_example_settings_print_to_a_file(self):
        self.assertFalse(self.printer.is_printing())

    def test_the_file_transport_writes_the_job(self):
        path = self.printer.print_label(self.layout, self.items, 2,
                                        "50 x 30")
        with open(path, "r", encoding="utf-8") as f:
            self.assertIn("^PQ2", f.read())

    def test_the_log_says_it_was_printed_but_not_what_it_said(self):
        self.printer.print_label(self.layout, self.items, 1, "50 x 30")
        level, message = self.log.entries[-1]
        self.assertEqual(level, "INFO")
        self.assertIn("copies 1", message)
        self.assertNotIn(SECRET, message)

    def test_the_file_transport_is_never_logged_as_printed(self):
        self.printer.print_label(self.layout, self.items, 1, "50 x 30")
        self.assertTrue(self.log.entries[-1][1].startswith("NOT printed"))

    def test_copies_out_of_range_are_refused(self):
        with self.assertRaises(ValueError):
            self.printer.print_label(self.layout, self.items, 100,
                                     "50 x 30")

    def test_copies_typed_are_checked(self):
        self.assertTrue(self.printer.is_copies("12"))
        self.assertFalse(self.printer.is_copies("0"))
        self.assertFalse(self.printer.is_copies("1O"))

    def test_a_failed_send_is_a_warning_and_raises(self):
        self.printer.spooler = Spooler("tcp", "", "", 9100, self.folder,
                                       self.log)
        with self.assertRaises(ValueError):
            self.printer.print_label(self.layout, self.items, 1, "50 x 30")
        self.assertEqual(self.log.entries[-1][0], "WARNING")
        self.assertNotIn(SECRET, self.log.entries[-1][1])

    def test_a_setting_the_printer_would_not_understand_is_refused(self):
        path = os.path.join(self.folder, "test.ini")
        shutil.copyfile(os.path.join(PROJECT_DIR, "pittacium.ini.example"),
                        path)
        config = Config(path)
        config.set("printer", "darkness", "99")
        with self.assertRaises(ValueError):
            Printer(config, self.folder, self.log)

    def test_an_unknown_transport_is_refused(self):
        with self.assertRaises(ValueError):
            Spooler("usb", "", "", 9100, self.folder, self.log)


if __name__ == "__main__":
    unittest.main()
