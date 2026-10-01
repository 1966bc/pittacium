# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The printer of this workstation: its language, its transport, the log.

The printer is data (CONVENTIONS.md): which language it speaks, its
resolution and media, how a job reaches it - all from the settings. This
class reads them once, picks the class that speaks that language, and
prints: build the source, hand it to the spooler, write down what
happened.

What happened is the format, the copies, the transport and where the job
went. What the label said is never written: it is printed and not kept.
"""

import os

from spooler import Spooler
from zpl import Zpl

#: The printer languages pittacium speaks, by the name in the settings.
#: Another one is a class added here, the day there is a printer to test
#: it on.
LANGUAGES = {"zpl": Zpl}


class Printer:
    """The label printer, as the settings describe it."""

    #: Copies in one job. The ceiling is there so that a 100 typed by
    #: mistake does not become a hundred labels.
    COPIES_MIN = 1
    COPIES_MAX = 99

    def __init__(self, config, folder, log):
        self.log = log
        self.language = config.get("printer", "language")
        if self.language not in LANGUAGES:
            raise ValueError("printer language is {0}, one of {1}".format(
                self.language, ", ".join(sorted(LANGUAGES))))
        self.dpi = config.get_int("printer", "dpi")
        self.media = config.get("printer", "media")
        self.tracking = config.get("printer", "tracking")
        self.darkness = config.get_int("printer", "darkness")
        self.speed = config.get_int("printer", "speed")
        self.spooler = Spooler(config.get("transport", "kind"),
                               config.get("transport", "queue"),
                               config.get("transport", "host"),
                               config.get_int("transport", "port"),
                               os.path.join(folder, "zpl"), log)
        # A writer is built once now, with no layout, only so that a
        # setting the printer would not understand is refused here, when
        # the settings are read, and not at the first label.
        self.get_writer(None)

    def __str__(self):
        return "class: {0}\n{1} at {2} dpi, {3}".format(
            self.__class__.__name__, self.language, self.dpi,
            self.spooler.transport)

    def is_printing(self):
        """False when the transport writes files instead of printing."""
        return self.spooler.is_printing()

    def is_copies(self, text):
        """True when the copies typed are a whole number in range."""
        valid = text.isdigit()
        if valid:
            valid = self.COPIES_MIN <= int(text) <= self.COPIES_MAX
        return valid

    def check_copies(self, copies):
        if not self.COPIES_MIN <= copies <= self.COPIES_MAX:
            raise ValueError("copies is {0}, from {1} to {2}".format(
                copies, self.COPIES_MIN, self.COPIES_MAX))

    def get_writer(self, layout):
        """The class that speaks this printer's language, for a layout."""
        return LANGUAGES[self.language](layout, self.media, self.tracking,
                                        self.darkness, self.speed)

    def print_label(self, layout, items, copies, format_name):
        """Print, write down how it went, and say where the job went.

        A failure is written down as a warning - the label did not come
        out - and raised again, so the operator is told.
        """
        self.check_copies(copies)
        source = self.get_writer(layout).get_source(items, copies)
        try:
            where = self.spooler.send(source)
        except Exception as exc:
            self.log.warning("not printed: format {0}, copies {1}, "
                             "transport {2}: {3}".format(
                                 format_name, copies,
                                 self.spooler.transport, exc))
            raise
        done = "printed"
        if not self.is_printing():
            done = "NOT printed, written"
        self.log.info("{0}: format {1}, copies {2}, transport {3}, "
                      "to {4}".format(done, format_name, copies,
                                      self.spooler.transport, where))
        return where
