# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The encoders, and a barcode on a label from Layout to ZPL."""

import unittest

from code128 import Code128
from i2of5 import Interleaved2of5
from layout import Layout
from zpl import Zpl


def get_barcode(data, symbology, align="C"):
    return {"kind": "barcode", "content": data, "height_mm": 8.0,
            "align": align, "symbology": symbology, "human_readable": True}


class TestInterleaved2of5(unittest.TestCase):

    def setUp(self):
        self.i2of5 = Interleaved2of5()

    def test_42_is_start_one_pair_and_stop(self):
        # start 4 modules, a pair 2 x (3 narrow + 2 wide of 3), stop 5
        self.assertEqual(len(self.i2of5.get_modules("42")), 4 + 18 + 5)

    def test_it_starts_and_ends_with_its_guards(self):
        modules = self.i2of5.get_modules("42")
        self.assertTrue(modules.startswith("1010"))
        self.assertTrue(modules.endswith("11101"))

    def test_an_odd_number_of_digits_is_refused_not_padded(self):
        self.assertIn("even", self.i2of5.get_problem("123"))

    def test_letters_are_refused(self):
        self.assertIn("digits", self.i2of5.get_problem("12AB"))


class TestCode128(unittest.TestCase):

    def setUp(self):
        self.code128 = Code128()

    def test_an_even_number_of_digits_is_subset_c(self):
        self.assertEqual(self.code128.get_subset("1234"), "C")

    def test_anything_else_is_subset_b(self):
        self.assertEqual(self.code128.get_subset("123"), "B")
        self.assertEqual(self.code128.get_subset("PBS"), "B")

    def test_the_checksum_of_1234_in_subset_c(self):
        # 105 + 1 x 12 + 2 x 34 = 185, mod 103 = 82
        self.assertEqual(self.code128.get_values("1234"),
                         [105, 12, 34, 82, 106])

    def test_the_checksum_of_pbs_in_subset_b(self):
        # 104 + 1 x 48 + 2 x 34 + 3 x 51 = 373, mod 103 = 64
        self.assertEqual(self.code128.get_values("PBS"),
                         [104, 48, 34, 51, 64, 106])

    def test_every_character_is_11_modules_and_the_stop_13(self):
        values = self.code128.get_values("PBS")
        self.assertEqual(len(self.code128.get_modules("PBS")),
                         11 * (len(values) - 1) + 13)

    def test_a_caret_is_refused_as_an_invocation_code(self):
        self.assertNotEqual(self.code128.get_problem("A>B"), "")

    def test_accents_are_refused(self):
        self.assertNotEqual(self.code128.get_problem("città"), "")


class TestBarcodeOnALabel(unittest.TestCase):

    def setUp(self):
        self.layout = Layout(50, 30, 1.5, 4.0, 300)

    def get_barcode_item(self, element):
        items = self.layout.get_items([element], "Lab")
        return [item for item in items if item["kind"] == "barcode"][0]

    def test_the_symbol_and_its_quiet_zone_fit_across(self):
        item = self.get_barcode_item(get_barcode("42", "I2OF5"))
        quiet = 2 * Interleaved2of5.QUIET * item["module"]
        self.assertLessEqual(item["width"] + quiet,
                             self.layout.get_size()[0])

    def test_short_data_gets_wider_bars_than_long_data(self):
        short = self.get_barcode_item(get_barcode("42", "I2OF5"))
        long = self.get_barcode_item(get_barcode("1234567890", "I2OF5"))
        self.assertGreater(short["module"], long["module"])

    def test_a_centred_barcode_is_centred(self):
        item = self.get_barcode_item(get_barcode("42", "I2OF5"))
        width = self.layout.get_size()[0]
        self.assertLessEqual(abs(item["x"] * 2 + item["width"] - width), 1)

    def test_the_human_readable_line_is_under_the_bars(self):
        items = self.layout.get_items([get_barcode("42", "I2OF5")], "Lab")
        self.assertEqual(items[1]["text"], "42")
        self.assertGreater(items[1]["y"], items[0]["y"] + items[0]["height"])

    def test_too_long_a_barcode_is_a_problem_and_never_printed(self):
        element = get_barcode("A" * 60, "CODE128")
        self.assertIn("too long", self.layout.get_problem(element))
        items = self.layout.get_items([element], "Lab")
        self.assertEqual(items[0]["kind"], "invalid")
        with self.assertRaises(ValueError):
            Zpl(self.layout, "T", "Y", 0, 2).get_source(items)

    def test_zpl_draws_2_of_5_with_the_same_ratio(self):
        items = self.layout.get_items([get_barcode("42", "I2OF5")], "Lab")
        source = Zpl(self.layout, "T", "Y", 0, 2).get_source(items)
        self.assertIn(",3.0,", source)
        self.assertIn("^B2N,", source)
        self.assertIn("^FD42^FS", source)

    def test_zpl_tells_code_128_its_subset(self):
        items = self.layout.get_items([get_barcode("1234", "CODE128")],
                                      "Lab")
        source = Zpl(self.layout, "T", "Y", 0, 2).get_source(items)
        self.assertIn("^FD>;1234^FS", source)


if __name__ == "__main__":
    unittest.main()
