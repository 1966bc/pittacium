# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""A label in ZPL II, the language of Zebra printers and their emulations.

The only module that writes a printer command (CONVENTIONS.md). It builds
the source and does not send it: that is the Spooler's job. Every position
and size comes from Layout's items, already in dots.

The printer draws the text itself with its scalable font 0, at its own
resolution: sharp, and a job of a few hundred bytes. ^CI28 tells it the
text is UTF-8, so accented letters print as typed.

What somebody types goes inside ^FD and must stay text. A caret starts a
ZPL command and a tilde a control command, so both are written in hex
after ^FH, and so is the underscore that ^FH uses to mark hex: a label
that reads "pH ^ 7" prints that, rather than becoming a command.

    zpl = Zpl(layout, "T", "Y", 0, 2)
    source = zpl.get_source(items, copies=3)
"""


class Zpl:
    """The ZPL source of one label, for a given layout and media."""

    #: The settings that take a closed set of values.
    MEDIA = ("T", "D")              # thermal transfer, direct thermal
    TRACKING = ("Y", "N", "M")      # gap, continuous, black mark
    DARKNESS = (-30, 30)
    SPEED = (1, 14)

    #: Characters that cannot appear as they are inside ^FD.
    ESCAPES = (("_", "_5F"), ("^", "_5E"), ("~", "_7E"))

    def __init__(self, layout, media, tracking, darkness, speed):
        self.layout = layout
        self.media = media
        self.tracking = tracking
        self.darkness = int(darkness)
        self.speed = int(speed)
        self.check_settings()

    def __str__(self):
        return "class: {0}\nmedia {1}, tracking {2}".format(
            self.__class__.__name__, self.media, self.tracking)

    def check_settings(self):
        """Refuse a setting the printer would not understand."""
        if self.media not in self.MEDIA:
            raise ValueError("media is {0}, one of {1}".format(
                self.media, ", ".join(self.MEDIA)))
        if self.tracking not in self.TRACKING:
            raise ValueError("tracking is {0}, one of {1}".format(
                self.tracking, ", ".join(self.TRACKING)))
        if not self.DARKNESS[0] <= self.darkness <= self.DARKNESS[1]:
            raise ValueError("darkness is {0}, from {1} to {2}".format(
                self.darkness, self.DARKNESS[0], self.DARKNESS[1]))
        if not self.SPEED[0] <= self.speed <= self.SPEED[1]:
            raise ValueError("speed is {0}, from {1} to {2}".format(
                self.speed, self.SPEED[0], self.SPEED[1]))

    def get_field(self, text):
        """Text as it goes inside ^FD, with ^FH before it."""
        for plain, coded in self.ESCAPES:
            text = text.replace(plain, coded)
        return "^FH^FD{0}^FS".format(text)

    def get_text(self, item):
        """A line of text, aligned inside its box by the printer: ^FB."""
        return "^FO{0},{1}^A0N,{2},{2}^FB{3},1,0,{4}{5}".format(
            item["x"], item["y"], item["height"], item["width"],
            item["align"], self.get_field(item["text"]))

    def get_barcode(self, item):
        """A barcode, drawn by the printer exactly as Layout measured it.

        ^BY gives the narrow bar in dots and, for 2 of 5, the ratio of the
        wide one. Code 128 is told its subset with an invocation code at
        the start of the data - >: for B, >; for C - so the printer does
        not choose another one than the preview drew. No interpretation
        line from the printer: Layout places the human-readable text.
        """
        head = "^FO{0},{1}^BY{2},{3:.1f},{4}".format(
            item["x"], item["y"], item["module"], item.get("ratio", 3),
            item["height"])
        if item["symbology"] == "I2OF5":
            command = "^B2N,{0},N,N,N".format(item["height"])
            data = item["data"]
        elif item["symbology"] == "CODE128":
            command = "^BCN,{0},N,N,N,N".format(item["height"])
            data = {"B": ">:", "C": ">;"}[item["subset"]] + item["data"]
        else:
            raise ValueError("no ZPL for symbology {0}".format(
                item["symbology"]))
        return "{0}{1}{2}".format(head, command, self.get_field(data))

    def get_rule(self, item):
        """A filled box: ^GB with the thickness equal to its height."""
        return "^FO{0},{1}^GB{2},{3},{3}^FS".format(
            item["x"], item["y"], item["width"], item["height"])

    def get_source(self, items, copies=1):
        """The whole job: settings, every item, copies (^PQ), end.

        The printer makes the copies: one job asking for n, not n jobs.
        """
        width, height = self.layout.get_size()

        lines = ["^XA", "^CI28",
                 "^PW{0}".format(width), "^LL{0}".format(height), "^LH0,0",
                 "^MT{0}".format(self.media), "^MN{0}".format(self.tracking),
                 "^MD{0}".format(self.darkness), "^PR{0}".format(self.speed),
                 "^PON"]
        for item in items:
            if item["kind"] == "rule":
                lines.append(self.get_rule(item))
            elif item["kind"] == "barcode":
                lines.append(self.get_barcode(item))
            elif item["kind"] == "text":
                lines.append(self.get_text(item))
            else:
                raise ValueError("cannot print an item of kind {0}".format(
                    item["kind"]))
        lines.append("^PQ{0}".format(copies))
        lines.append("^XZ")

        return "\n".join(lines) + "\n"
