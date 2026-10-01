# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The settings of this workstation, in a window.

Four groups: the label, the interface, the printer, the transport. A
setting with a closed set of values is a read-only combo box, so a value
the printer would not understand cannot be typed. The window writes
pittacium.ini line by line, and its comments survive.

The section and the printer take effect at once. The language does at the
next start: every window has already been built in the language it had.

The test label is the one honest way to know the settings work: it is
printed with what is in the boxes, saved first.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from i18n import LANGUAGES
from i18n import _
from spooler import Spooler
from ui.window import Window

#: (group, [(section, key, label, values or None for free text)])
GROUPS = (
    ("Label", (("label", "section", "Section", None),)),
    ("Interface", (("interface", "language", "Language",
                    tuple(sorted(LANGUAGES))),)),
    ("Printer", (("printer", "dpi", "Resolution (dpi)", ("203", "300")),
                 ("printer", "media", "Media", ("T", "D")),
                 ("printer", "tracking", "Sensor", ("Y", "N", "M")),
                 ("printer", "darkness", "Darkness (-30 to 30)", None),
                 ("printer", "speed", "Speed (inches/s)", None))),
    ("Transport", (("transport", "kind", "Transport",
                    ("file", "raw", "tcp")),
                   ("transport", "queue", "Print queue (raw)", None),
                   ("transport", "host", "Address (tcp)", None),
                   ("transport", "port", "Port (tcp)", None))),
)

#: What the closed values mean, shown beside the boxes.
NOTE = ("Media: T thermal transfer, D direct thermal. "
        "Sensor: Y gap, N continuous, M black mark.\n"
        "Transport: file does NOT print, raw uses the print queue, "
        "tcp goes to the printer on port 9100.\n"
        "The language changes at the next start.")


class UI(tk.Toplevel, Window):
    """The settings window."""

    def __init__(self, parent):
        super().__init__(parent, name="settings")
        self.parent = parent
        self.engine.tools.hide_me(self)
        self.transient(parent)
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        #: (section, key) -> the variable of its box
        self.fields = {}
        self.init_ui()

    def init_ui(self):
        frm_body = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_body.pack(fill=tk.BOTH, expand=1)

        # Two groups per row, so the window fits a laptop screen.
        for index, (title, settings) in enumerate(GROUPS):
            frm_group = ttk.LabelFrame(frm_body, text=_(title), padding=8)
            frm_group.grid(row=index // 2, column=index % 2,
                           sticky=tk.NSEW, padx=4, pady=4)
            for line, (section, key, label, values) in enumerate(settings):
                self.add_field(frm_group, line, section, key, label, values)

        ttk.Label(frm_body, text=_(NOTE), style="App.TLabel",
                  justify=tk.LEFT, wraplength=560).grid(
                      row=2, column=0, columnspan=2, sticky=tk.W,
                      pady=(8, 0))

        buttons = ((_("Save"), self.on_save),
                   (_("Test label"), self.on_test),
                   (_("Print queues"), self.on_queues),
                   (_("Close"), self.on_cancel))
        frm_buttons = self.engine.tools.get_button_column(frm_body, buttons,
                                                          self)
        frm_buttons.grid(row=0, column=2, rowspan=3, sticky=tk.N)

        self.bind("<Escape>", self.on_cancel)

    def add_field(self, container, line, section, key, label, values):
        """One setting: its label and its box, a combo when closed."""
        ttk.Label(container, text=_(label),
                  style="App.TLabel").grid(row=line, column=0,
                                           sticky=tk.W, pady=2)
        variable = tk.StringVar()
        if values is None:
            widget = ttk.Entry(container, textvariable=variable,
                               width=self.engine.tools.FIELD_CODE)
        else:
            widget = ttk.Combobox(container, textvariable=variable,
                                  values=list(values), state="readonly",
                                  width=self.engine.tools.FIELD_CODE - 2)
        widget.grid(row=line, column=1, sticky=tk.EW, padx=(8, 0), pady=2)
        self.fields[(section, key)] = variable

    def on_open(self):
        self.title(_("Settings"))
        for section, key in self.fields:
            self.fields[(section, key)].set(
                self.engine.config.get(section, key))
        self.engine.tools.center_me(self, self.parent)

    def get_values(self):
        values = {}
        for section, key in self.fields:
            values[(section, key)] = self.fields[(section, key)].get().strip()
        return values

    def on_save(self, evt=None):
        """Save and close. A refused value leaves the file as it was."""
        self.engine.set_settings(self.get_values())
        self.on_cancel()

    def on_test(self, evt=None):
        """Save, then print a test label with these settings."""
        self.engine.set_settings(self.get_values())
        where = self.engine.print_test()
        message = _("Test label sent to {0}").format(where)
        if not self.engine.printer.is_printing():
            message = _("NOT PRINTED, written to {0}").format(where)
        messagebox.showinfo(_("Test label"), message, parent=self)

    def on_queues(self, evt=None):
        """The print queues the system knows, to copy the right name."""
        queues = Spooler.get_queues()
        text = "\n".join(queues)
        if not queues:
            text = _("No print queue on this machine.")
        messagebox.showinfo(_("Print queues"), text, parent=self)

    def on_cancel(self, evt=None):
        self.destroy()
