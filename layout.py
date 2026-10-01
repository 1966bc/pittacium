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

A line of text is a box as wide as the label inside its margins, and the
text is aligned inside the box by whoever draws it: the printer knows the
width of its own letters, this class does not.

A barcode is different: its width is known exactly, module by module, so
it is placed here, with the widest bars that fit and its quiet zone, and
its human-readable line under it.

The lines are stacked from the top with a gap between them and the stack
is centred in the space above the section band. The band is the last
strip of the label: a thin rule, and the section's name centred under it.
"""

from code128 import Code128
from i2of5 import Interleaved2of5

#: The barcodes a line can be, by the code stored in symbologies.
SYMBOLOGIES = {"I2OF5": Interleaved2of5(), "CODE128": Code128()}


class Layout:
    """A label format at a printer resolution, and the items placed on it."""

    #: Space between two lines, in millimetres.
    GAP_MM = 1.0

    #: Height of the section's name, as a share of the band it sits in.
    SECTION_TEXT_RATIO = 0.7

    #: Thickness of the rule above the band, in millimetres.
    RULE_MM = 0.25

    #: The human-readable line under a barcode, and the space above it.
    HUMAN_MM = 2.5
    HUMAN_GAP_MM = 0.5

    #: The narrowest bar a scanner reads reliably, and the widest wanted.
    MODULE_MIN_MM = 0.17
    MODULE_MAX_MM = 0.5

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

    # --- barcodes -----------------------------------------------------------

    def get_module(self, element):
        """The widest bar, in dots, at which the symbol fits; 0 if none.

        The symbol and its quiet zone on both sides have to fit across the
        label. Wider bars scan more easily, so the widest that fits wins.
        """
        symbology = SYMBOLOGIES[element["symbology"]]
        count = len(symbology.get_modules(element["content"]))
        needed = count + 2 * symbology.QUIET
        smallest = max(2, self.get_dots(self.MODULE_MIN_MM))
        module = 0
        for dots in range(smallest, self.get_dots(self.MODULE_MAX_MM) + 1):
            if needed * dots <= self.get_size()[0]:
                module = dots
        return module

    def get_problem(self, element):
        """Why a line cannot be printed as it is, or an empty string."""
        problem = ""
        content = element["content"].strip()
        if element["kind"] == "barcode" and content != "":
            symbology = SYMBOLOGIES[element["symbology"]]
            problem = symbology.get_problem(content)
            if problem == "" and self.get_module(element) == 0:
                problem = "The barcode is too long for the label."
        return problem

    def get_problems(self, elements):
        """The problems of every line that has one, from the top."""
        problems = []
        for element in elements:
            problem = self.get_problem(element)
            if problem:
                problems.append(problem)
        return problems

    # --- the lines ----------------------------------------------------------

    def get_height(self, element):
        """The height of a line, in dots: a barcode carries its text."""
        height = self.get_dots(element["height_mm"])
        if element["kind"] == "barcode" and element["human_readable"]:
            height += (self.get_dots(self.HUMAN_GAP_MM)
                       + self.get_dots(self.HUMAN_MM))
        return height

    def get_lines(self, elements):
        """The elements that print, with their heights in dots.

        An empty line is not printed: on a label written by hand nobody
        leaves a blank line, and a template line left empty is one that was
        not needed this time.
        """
        lines = []
        for element in elements:
            if element["content"].strip() != "":
                lines.append((element, self.get_height(element)))
        return lines

    def get_free(self, lines):
        """Dots left over above the band; negative when the lines overflow."""
        used = 0
        for element, height in lines:
            used += height
        if len(lines) > 1:
            used += self.get_dots(self.GAP_MM) * (len(lines) - 1)
        return self.get_body() - used

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

    # --- the items ----------------------------------------------------------

    def get_text_item(self, x, y, width, height, text, align):
        return {"kind": "text", "x": x, "y": y, "width": width,
                "height": height, "text": text, "align": align}

    def get_barcode_items(self, element, y, height):
        """The bars, placed by their alignment, and the text under them.

        A barcode with a problem is an empty box of the same place and
        height, which the preview shows in red and the printer never gets.
        """
        width = self.get_size()[0]
        margin = self.get_dots(self.margin_mm)
        bars = self.get_dots(element["height_mm"])
        data = element["content"].strip()
        items = []

        if self.get_problem(element):
            items.append({"kind": "invalid", "x": margin, "y": y,
                          "width": width - 2 * margin, "height": height})
        else:
            symbology = SYMBOLOGIES[element["symbology"]]
            modules = symbology.get_modules(data)
            module = self.get_module(element)
            symbol = len(modules) * module
            x = margin
            if element["align"] == "C":
                x = (width - symbol) // 2
            elif element["align"] == "R":
                x = width - margin - symbol
            barcode = {"kind": "barcode", "x": x, "y": y, "width": symbol,
                       "height": bars, "symbology": element["symbology"],
                       "data": data, "module": module, "modules": modules}
            # What the printer must be told to draw the very same symbol:
            # the wide-to-narrow ratio, or the Code 128 subset.
            if element["symbology"] == "I2OF5":
                barcode["ratio"] = symbology.RATIO
            elif element["symbology"] == "CODE128":
                barcode["subset"] = symbology.get_subset(data)
            items.append(barcode)
            if element["human_readable"]:
                items.append(self.get_text_item(
                    x, y + bars + self.get_dots(self.HUMAN_GAP_MM), symbol,
                    self.get_dots(self.HUMAN_MM), data, "C"))
        return items

    def get_items(self, elements, section):
        """Everything to draw, in dots, from the top.

        Each item is a dictionary with its kind - 'text', 'rule',
        'barcode', or 'invalid' for a barcode that cannot be printed - and
        x, y, width, height. Lines that do not fit are placed anyway,
        running into the band: the preview shows the overflow, it does
        not hide it.
        """
        width = self.get_size()[0]
        margin = self.get_dots(self.margin_mm)
        gap = self.get_dots(self.GAP_MM)
        box = width - 2 * margin
        lines = self.get_lines(elements)

        y = margin + max(0, self.get_free(lines)) // 2
        items = []
        for element, height in lines:
            if element["kind"] == "barcode":
                items.extend(self.get_barcode_items(element, y, height))
            else:
                items.append(self.get_text_item(
                    margin, y, box, height, element["content"].strip(),
                    element["align"]))
            y += height + gap

        band_top = self.get_band_top()
        band = self.get_dots(self.section_band_mm)
        rule = max(2, self.get_dots(self.RULE_MM))
        text_height = int(band * self.SECTION_TEXT_RATIO)
        items.append({"kind": "rule", "x": margin, "y": band_top,
                      "width": box, "height": rule})
        items.append(self.get_text_item(
            margin, band_top + rule + (band - rule - text_height) // 2, box,
            text_height, section, "C"))
        return items
