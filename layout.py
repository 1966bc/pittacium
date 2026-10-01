# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Where everything goes on a label, decided once.

The format is in millimetres; the printer has a resolution; the items that
come out are in printer dots. Whoever draws a label - the ZPL for the
printer, the preview on screen - reads these items and adds no position,
size or proportion of its own (CONVENTIONS.md). A number that places
something and lives in a renderer is a second copy, and the second copy is
the one that drifts.

    layout = Layout(50, 30, 1.5, 4.0, 300)
    items = layout.get_items(elements, "Corelab")

Every line is a box as wide as the label inside its margins, and the text
is aligned inside the box by whoever draws it: the printer knows the width
of its own letters, this class does not. What this class does know is the
height, so it says whether the lines fit, and by how much they do not.

The lines are stacked from the top with a gap between them and the stack
is centred in the space above the section band. The band is the last
strip of the label: a thin rule, and the section's name centred under it.
"""


class Layout:
    """A label format at a printer resolution, and the items placed on it."""

    #: Space between two lines, in millimetres.
    GAP_MM = 1.0

    #: Height of the section's name, as a share of the band it sits in.
    SECTION_TEXT_RATIO = 0.7

    #: Thickness of the rule above the band, in millimetres.
    RULE_MM = 0.25

    def __init__(self, width_mm, height_mm, margin_mm, section_band_mm, dpi):
        self.width_mm = float(width_mm)
        self.height_mm = float(height_mm)
        self.margin_mm = float(margin_mm)
        self.section_band_mm = float(section_band_mm)
        self.dpi = int(dpi)

    def __str__(self):
        return "class: {0}\n{1} x {2} mm at {3} dpi".format(
            self.__class__.__name__, self.width_mm, self.height_mm, self.dpi)

    def get_dots(self, mm):
        """Millimetres in printer dots, at this resolution."""
        return int(round(mm * self.dpi / 25.4))

    def get_size(self):
        """Width and height of the label, in dots."""
        return (self.get_dots(self.width_mm), self.get_dots(self.height_mm))

    def get_band_top(self):
        """Where the section band begins, in dots from the top."""
        height = self.get_size()[1]
        return (height - self.get_dots(self.margin_mm)
                - self.get_dots(self.section_band_mm))

    def get_lines(self, elements):
        """The elements that print, with their heights in dots.

        An empty line is not printed: on a label written by hand nobody
        leaves a blank line, and a template line left empty is one that was
        not needed this time.
        """
        lines = []
        for element in elements:
            if element["content"].strip() != "":
                lines.append((element, self.get_dots(element["height_mm"])))
        return lines

    def get_body(self):
        """Dots available to the lines, between the top margin and the band."""
        return (self.get_band_top() - self.get_dots(self.margin_mm)
                - self.get_dots(self.GAP_MM))

    def get_max_lines(self, height_mm):
        """How many lines of this height fit above the band.

        n lines take n heights and n - 1 gaps, so n is the largest whole
        number with n * (height + gap) <= body + gap.
        """
        step = self.get_dots(height_mm) + self.get_dots(self.GAP_MM)
        return (self.get_body() + self.get_dots(self.GAP_MM)) // step

    def get_free(self, lines):
        """Dots left over above the band; negative when the lines overflow."""
        body = self.get_body()
        used = 0
        for element, height in lines:
            used += height
        if len(lines) > 1:
            used += self.get_dots(self.GAP_MM) * (len(lines) - 1)
        return body - used

    def get_overflow_mm(self, elements):
        """How much too tall the lines are, in millimetres; 0 if they fit."""
        free = self.get_free(self.get_lines(elements))
        overflow = 0.0
        if free < 0:
            overflow = -free * 25.4 / self.dpi
        return overflow

    def is_fitting(self, elements):
        """True when every line fits above the section band."""
        return self.get_free(self.get_lines(elements)) >= 0

    def get_items(self, elements, section):
        """Everything to draw, in dots, from the top.

        Each item is a dictionary: kind ('text' or 'rule'), x, y, width,
        height, and for text the text and its alignment (L, C, R) inside
        the box. Lines that do not fit are placed anyway, running into the
        band: the preview shows the overflow, it does not hide it.
        """
        width = self.get_size()[0]
        margin = self.get_dots(self.margin_mm)
        gap = self.get_dots(self.GAP_MM)
        box = width - 2 * margin
        lines = self.get_lines(elements)

        y = margin + max(0, self.get_free(lines)) // 2
        items = []
        for element, height in lines:
            items.append({"kind": "text", "x": margin, "y": y,
                          "width": box, "height": height,
                          "text": element["content"].strip(),
                          "align": element["align"]})
            y += height + gap

        band_top = self.get_band_top()
        band = self.get_dots(self.section_band_mm)
        rule = max(2, self.get_dots(self.RULE_MM))
        text_height = int(band * self.SECTION_TEXT_RATIO)
        items.append({"kind": "rule", "x": margin, "y": band_top,
                      "width": box, "height": rule})
        items.append({"kind": "text", "x": margin,
                      "y": band_top + rule + (band - rule - text_height) // 2,
                      "width": box, "height": text_height,
                      "text": section, "align": "C"})
        return items
