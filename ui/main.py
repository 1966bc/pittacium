# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The main window: for now a menu and a status bar.

The label form comes here next; this is the frame it will sit in.
"""

import tkinter as tk
from tkinter import ttk

from i18n import _
from ui.window import Window


class Main(ttk.Frame, Window):
    """The frame inside the root window."""

    def __init__(self, parent):
        super().__init__(parent, style="App.TFrame")
        self.parent = parent
        self.status = tk.StringVar()
        self.init_menu()
        self.init_ui()

    def init_menu(self):
        menubar = tk.Menu(self.parent)
        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label=_("Exit"), underline=0,
                              command=self.parent.on_exit)
        menubar.add_cascade(label=_("File"), menu=menu_file, underline=0)
        self.parent.config(menu=menubar)

    def init_ui(self):
        frm_body = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_body.pack(fill=tk.BOTH, expand=1)
        ttk.Label(frm_body, text=self.engine.app_title,
                  style="App.TLabel").pack(padx=80, pady=40)

        lbl_status = ttk.Label(self, textvariable=self.status,
                               style="App.TLabel", relief=tk.SUNKEN)
        lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

    def on_open(self):
        self.status.set(_("Section: {0}").format(self.engine.get_section()))
