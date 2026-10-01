# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Interleaved 2 of 5, encoded by hand.

The printer draws the bars; this class is for knowing how wide they will
be, drawing them in the preview, and refusing what cannot be encoded.

Digits only, and an even number of them: the digits go in pairs, the
first drawn by the bars and the second by the spaces between them. An odd
number is refused rather than padded with a leading zero, because the
zero would then be read by the scanner as part of the code.

Each digit is five elements, two of them wide. The wide ones are RATIO
modules: the printer is told the same ratio, so both draw the same symbol.
"""


class Interleaved2of5:
    """Start, pairs of digits interleaved, stop."""

    #: N narrow, W wide, for the five elements of each digit.
    DIGITS = ("NNWWN", "WNNNW", "NWNNW", "WWNNN", "NNWNW",
              "WNWNN", "NWWNN", "NNNWW", "WNNWN", "NWNWN")

    #: Width of a wide element, in modules.
    RATIO = 3

    #: Modules around the symbol that must stay blank for a scanner.
    QUIET = 10

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    def get_problem(self, data):
        """Why data cannot be encoded, or an empty string."""
        problem = ""
        if data == "":
            problem = "Nothing to encode."
        elif not data.isdigit():
            problem = "Interleaved 2 of 5 takes digits only."
        elif len(data) % 2 != 0:
            problem = "Interleaved 2 of 5 needs an even number of digits."
        return problem

    def get_width(self, element):
        width = 1
        if element == "W":
            width = self.RATIO
        return width

    def get_modules(self, data):
        """Bars and spaces as a string of '1' (bar) and '0' (space)."""
        modules = ["1010"]
        for index in range(0, len(data), 2):
            bars = self.DIGITS[int(data[index])]
            spaces = self.DIGITS[int(data[index + 1])]
            for bar, space in zip(bars, spaces):
                modules.append("1" * self.get_width(bar))
                modules.append("0" * self.get_width(space))
        modules.append("1" * self.RATIO + "0" + "1")
        return "".join(modules)
