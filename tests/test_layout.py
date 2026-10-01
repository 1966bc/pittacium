# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Layout: millimetres to dots, lines stacked, overflow told."""

import unittest

from layout import Layout


def get_line(content, height_mm=4.0, align="C"):
    return {"kind": "text", "content": content, "height_mm": height_mm,
            "align": align}


class TestLayout(unittest.TestCase):

    def setUp(self):
        self.layout = Layout(50, 30, 1.5, 4.0, 300)

    def test_50_by_30_mm_at_300_dpi_is_591_by_354_dots(self):
        self.assertEqual(self.layout.get_size(), (591, 354))

    def test_the_same_format_at_203_dpi_is_smaller_in_dots(self):
        layout = Layout(50, 30, 1.5, 4.0, 203)
        self.assertEqual(layout.get_size(), (400, 240))

    def test_empty_lines_are_not_printed(self):
        items = self.layout.get_items([get_line(""), get_line("PBS 1X")],
                                      "Lab")
        texts = [item["text"] for item in items if item["kind"] == "text"]
        self.assertEqual(texts, ["PBS 1X", "Lab"])

    def test_lines_are_stacked_from_the_top(self):
        items = self.layout.get_items([get_line("one"), get_line("two")],
                                      "Lab")
        self.assertLess(items[0]["y"], items[1]["y"])

    def test_the_section_is_the_last_item_and_centred(self):
        items = self.layout.get_items([get_line("PBS 1X")], "Corelab")
        self.assertEqual((items[-1]["text"], items[-1]["align"]),
                         ("Corelab", "C"))

    def test_the_lines_stay_above_the_section_band(self):
        items = self.layout.get_items([get_line("a"), get_line("b")], "Lab")
        bottom = items[1]["y"] + items[1]["height"]
        self.assertLessEqual(bottom, self.layout.get_band_top())

    def test_three_lines_of_4_mm_fit(self):
        lines = [get_line("a"), get_line("b"), get_line("c")]
        self.assertTrue(self.layout.is_fitting(lines))
        self.assertEqual(self.layout.get_overflow_mm(lines), 0.0)

    def test_too_many_lines_are_told_with_the_overflow(self):
        lines = [get_line(str(n), 6.0) for n in range(5)]
        self.assertFalse(self.layout.is_fitting(lines))
        self.assertGreater(self.layout.get_overflow_mm(lines), 0.0)

    def test_every_line_box_is_inside_the_margins(self):
        items = self.layout.get_items([get_line("PBS 1X", align="R")],
                                      "Lab")
        width = self.layout.get_size()[0]
        margin = self.layout.get_dots(1.5)
        self.assertEqual(items[0]["x"], margin)
        self.assertEqual(items[0]["x"] + items[0]["width"], width - margin)


if __name__ == "__main__":
    unittest.main()
