# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""ZPL: the items as commands, copies by ^PQ, typed text kept as text."""

import unittest

from layout import Layout
from zpl import Zpl


def get_line(content, align="C"):
    return {"kind": "text", "content": content, "height_mm": 4.0,
            "align": align}


class TestZpl(unittest.TestCase):

    def setUp(self):
        self.layout = Layout(50, 30, 1.5, 4.0, 300)
        self.zpl = Zpl(self.layout, "T", "Y", 0, 2)

    def get_source(self, lines, copies=1):
        items = self.layout.get_items(lines, "Lab")
        return self.zpl.get_source(items, copies)

    def test_a_job_starts_and_ends_once(self):
        source = self.get_source([get_line("PBS 1X")])
        self.assertTrue(source.startswith("^XA"))
        self.assertEqual(source.count("^XA"), 1)
        self.assertEqual(source.count("^XZ"), 1)

    def test_the_label_size_is_in_dots(self):
        source = self.get_source([get_line("PBS 1X")])
        self.assertIn("^PW591", source)
        self.assertIn("^LL354", source)

    def test_utf8_is_declared_so_accents_print(self):
        self.assertIn("^CI28", self.get_source([get_line("città")]))

    def test_the_copies_are_asked_of_the_printer(self):
        self.assertIn("^PQ3", self.get_source([get_line("PBS 1X")], 3))

    def test_one_field_per_line_plus_the_section(self):
        source = self.get_source([get_line("one"), get_line("two")])
        self.assertEqual(source.count("^FD"), 3)

    def test_the_alignment_goes_to_the_field_block(self):
        source = self.get_source([get_line("PBS 1X", "R")])
        self.assertIn(",R^FH^FDPBS 1X^FS", source)

    def test_a_caret_typed_is_text_and_not_a_command(self):
        source = self.get_source([get_line("pH ^ 7 ~ x_y")])
        self.assertIn("^FDpH _5E 7 _7E x_5Fy^FS", source)

    def test_the_rule_above_the_band_is_a_filled_box(self):
        self.assertIn("^GB", self.get_source([get_line("PBS 1X")]))

    def test_an_unknown_media_is_refused(self):
        with self.assertRaises(ValueError):
            Zpl(self.layout, "X", "Y", 0, 2)

    def test_darkness_out_of_range_is_refused(self):
        with self.assertRaises(ValueError):
            Zpl(self.layout, "T", "Y", 31, 2)


if __name__ == "__main__":
    unittest.main()
