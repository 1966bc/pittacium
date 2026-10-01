# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""About pittacium: what it is, who wrote it, what it runs on.

What it runs on is asked of the running program, not written down: the
Python, Tk and SQLite versions are the ones that would be reported with a
bug, and on the laboratory machine they are not the ones at home.
"""

import sqlite3
import sys
import tkinter as tk
import webbrowser
from tkinter import font
from tkinter import ttk

import version
from i18n import _
from ui.window import Window


class UI(tk.Toplevel, Window):
    """A small window with the icon, the name, and a few facts."""

    def __init__(self, parent):
        super().__init__(parent, name="about")
        self.parent = parent
        self.transient(parent)
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()

    def init_ui(self):
        frm_main = ttk.Frame(self, style="App.TFrame", padding=16)
        frm_main.pack(fill=tk.BOTH, expand=1)

        # The largest of the icon's sizes. Kept on self: a PhotoImage only a
        # local variable points to is collected, and the label goes blank.
        self.icon = tk.PhotoImage(data=self.engine.get_icons()[-1])
        ttk.Label(frm_main, image=self.icon).grid(row=0, column=0, rowspan=2,
                                                  sticky=tk.N, padx=(0, 12))

        # The name larger and bold, in the default family, so it grows with
        # the rest of the text on a machine set to large fonts.
        base = font.nametofont("TkDefaultFont")
        title = (base.cget("family"), base.cget("size") + 6, "bold")
        ttk.Label(frm_main, text=version.APP_NAME,
                  font=title).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(frm_main, text=_(version.APP_SUBTITLE),
                  style="App.TLabel").grid(row=1, column=1, sticky=tk.W)

        ttk.Separator(frm_main).grid(row=2, column=0, columnspan=2,
                                     sticky=tk.EW, pady=12)

        facts = ((_("Version:"), "{0}, {1}".format(version.__version__,
                                                   version.__date__)),
                 (_("Author:"), version.__author__),
                 (_("Licence:"), version.__license__),
                 ("Python:", ".".join(map(str, sys.version_info[:3]))),
                 ("Tk:", self.tk.call("info", "patchlevel")),
                 ("SQLite:", sqlite3.sqlite_version),
                 (_("Database:"), self.engine.db.database))

        frm_facts = ttk.Frame(frm_main, style="App.TFrame")
        frm_facts.grid(row=3, column=0, columnspan=2, sticky=tk.W)
        for row, (label, value) in enumerate(facts):
            ttk.Label(frm_facts, text=label,
                      style="App.TLabel").grid(row=row, column=0, sticky=tk.W)
            ttk.Label(frm_facts, text=value,
                      style="App.TLabel").grid(row=row, column=1,
                                               sticky=tk.W, padx=(8, 0))

        # Something that opens when clicked: the colour of the keyboard
        # focus, underlined, the way a link has always looked.
        link_font = (base.cget("family"), base.cget("size"), "underline")
        ttk.Label(frm_facts, text=_("Source:"),
                  style="App.TLabel").grid(row=len(facts), column=0,
                                           sticky=tk.W)
        lbl_link = ttk.Label(frm_facts, text=version.SOURCE, font=link_font,
                             foreground=self.engine.tools.get_rgb(
                                 *self.engine.tools.FOCUS),
                             cursor="hand2")
        lbl_link.grid(row=len(facts), column=1, sticky=tk.W, padx=(8, 0))
        lbl_link.bind("<Button-1>", self.on_source)

        frm_buttons = self.engine.tools.get_button_column(
            frm_main, ((_("Close"), self.on_cancel),), self)
        frm_buttons.grid(row=4, column=0, columnspan=2, sticky=tk.E,
                         pady=(12, 0))
        self.bind("<Escape>", self.on_cancel)

    def on_open(self):
        self.title(_("About {0}").format(version.APP_NAME))
        self.engine.tools.center_me(self, self.parent)

    def on_source(self, evt=None):
        webbrowser.open(version.SOURCE)

    def on_cancel(self, evt=None):
        self.destroy()
