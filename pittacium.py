#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Start pittacium.

    python3 pittacium.py            start it
    python3 pittacium.py --trace    start it, and print on the terminal what
                                    it does and what its variables hold
"""

import os
import sys
from tkinter import messagebox

from log import Log
from ui.app import App
from version import APP_NAME

#: The folder of the program: the log lives here, beside it, so it can be
#: started from any folder. Built with PyInstaller, the program is the
#: executable.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    PROJECT_DIR = os.path.dirname(sys.executable)

#: The options the program knows. Anything else is refused, not ignored.
OPTIONS = ("--trace",)


def main():

    # sys.argv[0] is the program, the rest is ours.
    options = sys.argv[1:]
    unknown = [option for option in options if option not in OPTIONS]
    if unknown:
        raise SystemExit(
            "unknown option: {0}\nusage: python3 pittacium.py "
            "[--trace]".format(" ".join(unknown)))

    # The log comes first, so that even a failure to start is written down.
    log = Log(os.path.join(PROJECT_DIR, "pittacium.log"),
              "--trace" in options)

    # Before the main loop there is no report_callback_exception yet: a
    # failure here is written to the log, shown, and raised again.
    try:
        app = App(log)
    except Exception as exc:
        log.exception("start failed: {0}".format(exc))
        messagebox.showerror(APP_NAME, "{0}\n\n{1}".format(exc, log.path))
        raise

    app.mainloop()


if __name__ == "__main__":
    main()
