# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The label on screen, drawn from the same items the printer gets.

Positions and sizes come from Layout and nothing here adds to them: the
preview is scaled, not recomposed. What is approximate is the shape of the
letters. The printer uses its own condensed font; the screen uses the
narrowest similar one it has, and when it has none a regular one, wider
than the printer's - so a line the preview says fits, fits.

A line wider than its box is outlined in red, and so is the label when the
lines are too tall for it: a label is wasted on paper only after it has
been seen to be wrong on screen.
"""

import tkinter as tk
from tkinter import font


class Preview(tk.Canvas):
    """A canvas that draws one label, scaled to its own width."""

    #: Width of the label on screen, in pixels.
    LABEL_PX = 480

    #: Room around the label, in pixels.
    PAD_PX = 16

    #: The fonts tried, narrowest first: the printer's is condensed.
    FAMILIES = ("Arial Narrow", "Liberation Sans Narrow",
                "DejaVu Sans Condensed", "Helvetica")

    PAPER = "#ffffff"
    INK = "#000000"
    TABLE = "#c8c8c4"
    WRONG = "#d03030"

    def __init__(self, parent, layout):
        super().__init__(parent, background=self.TABLE,
                         highlightthickness=0)
        self.set_layout(layout)
        self.family = self.get_family()

    def set_layout(self, layout):
        """Scale to a layout: the label is always LABEL_PX wide on screen."""
        width_dots, height_dots = layout.get_size()
        self.scale = float(self.LABEL_PX) / width_dots
        self.label_width = self.LABEL_PX
        self.label_height = int(height_dots * self.scale)
        self.configure(width=self.label_width + 2 * self.PAD_PX,
                       height=self.label_height + 2 * self.PAD_PX)

    def get_family(self):
        """The first of FAMILIES this machine has."""
        available = font.families(self)
        chosen = self.FAMILIES[-1]
        for family in reversed(self.FAMILIES):
            if family in available:
                chosen = family
        return chosen

    def get_px(self, dots):
        return int(round(dots * self.scale))

    def set_items(self, items, fitting):
        """Draw the label again, from scratch."""
        self.delete("all")
        outline = self.INK
        width = 1
        if not fitting:
            outline = self.WRONG
            width = 3
        self.create_rectangle(self.PAD_PX, self.PAD_PX,
                              self.PAD_PX + self.label_width,
                              self.PAD_PX + self.label_height,
                              fill=self.PAPER, outline=outline, width=width)
        for item in items:
            if item["kind"] == "rule":
                self.set_rule(item)
            else:
                self.set_text(item)

    def set_rule(self, item):
        x = self.PAD_PX + self.get_px(item["x"])
        y = self.PAD_PX + self.get_px(item["y"])
        self.create_rectangle(x, y, x + self.get_px(item["width"]),
                              y + max(1, self.get_px(item["height"])),
                              fill=self.INK, outline="")

    def set_text(self, item):
        """One line of text in its box, aligned as the printer would.

        A negative font size is in pixels: the item's height, scaled.
        """
        x = self.PAD_PX + self.get_px(item["x"])
        y = self.PAD_PX + self.get_px(item["y"])
        box = self.get_px(item["width"])
        size = max(1, self.get_px(item["height"]))
        face = (self.family, -size, "bold")

        anchor = tk.NW
        left = x
        if item["align"] == "C":
            anchor = tk.N
            left = x + box // 2
        elif item["align"] == "R":
            anchor = tk.NE
            left = x + box

        self.create_text(left, y, text=item["text"], anchor=anchor,
                         font=face, fill=self.INK)

        if font.Font(font=face).measure(item["text"]) > box:
            self.create_rectangle(x, y, x + box, y + size,
                                  outline=self.WRONG, width=2)
