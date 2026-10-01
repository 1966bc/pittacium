# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""A Log that keeps its entries in a list, for the tests."""


class MemoryLog:
    """Log's methods, writing to self.entries instead of a file."""

    def __init__(self):
        self.path = ":memory:"
        self.entries = []

    def trace(self, message):
        pass

    def info(self, message):
        self.entries.append(("INFO", message))

    def warning(self, message):
        self.entries.append(("WARNING", message))

    def error(self, message):
        self.entries.append(("ERROR", message))

    def exception(self, message):
        self.entries.append(("ERROR", message))
