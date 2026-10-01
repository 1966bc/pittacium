# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The licence, shown and not editable."""

import tkinter as tk
from tkinter import ttk

from i18n import _
from ui.window import Window


class UI(tk.Toplevel, Window):
    """The text of LICENSE, read-only."""

    def __init__(self, parent):
        super().__init__(parent, name="licence")
        self.parent = parent
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()

    def init_ui(self):
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, expand=1)

        # Fixed width: the GPL is laid out in columns of plain text, it has
        # its own typography and it is not ours to reflow.
        self.txt_licence = tk.Text(frm_main, wrap=tk.NONE, font="TkFixedFont",
                                   width=80, height=30,
                                   background=self.engine.tools.get_rgb(
                                       *self.engine.tools.WHITE))
        scrollbar = ttk.Scrollbar(frm_main, orient=tk.VERTICAL,
                                  command=self.txt_licence.yview)
        self.txt_licence.configure(yscrollcommand=scrollbar.set)
        self.txt_licence.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind("<Escape>", self.on_cancel)

    def on_open(self):
        """Fill the text and leave it shown, selectable, not editable."""
        self.title(_("Licence"))
        self.txt_licence.insert("1.0", self.engine.get_license())
        self.txt_licence.configure(state=tk.DISABLED)
        self.engine.tools.center_me(self, self.parent)

    def on_cancel(self, evt=None):
        self.destroy()
