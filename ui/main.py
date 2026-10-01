# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The main window: the lines of a label on the left, the label on the right.

Every keystroke redraws the preview, so a line too long or a label too full
is seen while it is typed. The lines are as many as are wanted: Add line
and Remove line, and the preview says when they no longer fit.
"""

import tkinter as tk
from tkinter import ttk

from i18n import _
from ui.preview import Preview
from ui.window import Window

#: The alignments, as stored and as read.
ALIGNS = (("L", "Left"), ("C", "Centre"), ("R", "Right"))

#: The heights a line can be given, in millimetres.
HEIGHT_MIN_MM = 2.0
HEIGHT_MAX_MM = 20.0
HEIGHT_STEP_MM = 0.5

#: A new line: the first is the title, the others are smaller.
FIRST_HEIGHT_MM = 5.0
NEXT_HEIGHT_MM = 3.5


class Main(ttk.Frame, Window):
    """The frame inside the root window."""

    def __init__(self, parent):
        super().__init__(parent, style="App.TFrame", padding=8)
        self.parent = parent
        self.status = tk.StringVar()
        self.fit = tk.StringVar()
        #: One dictionary per line: its variables and its widgets.
        self.rows = []
        label_format = self.engine.get_formats()[0]
        self.layout = self.engine.get_layout(label_format)
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
        frm_body = ttk.Frame(self, style="App.TFrame")
        frm_body.pack(fill=tk.BOTH, expand=1)

        frm_left = ttk.Frame(frm_body, style="App.TFrame")
        frm_left.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)

        self.frm_lines = ttk.LabelFrame(frm_left, text=_("Lines"),
                                        padding=8)
        self.frm_lines.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)
        headings = (_("Text"), _("Height mm"), _("Align"))
        for column, heading in enumerate(headings):
            ttk.Label(self.frm_lines, text=heading,
                      style="App.TLabel").grid(row=0, column=column,
                                               sticky=tk.W, padx=2)

        buttons = ((_("Add line"), self.on_add),
                   (_("Remove line"), self.on_remove))
        frm_buttons = self.engine.tools.get_button_column(frm_left, buttons)
        frm_buttons.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)

        self.preview = Preview(frm_body, self.layout)
        self.preview.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 0))

        frm_status = ttk.Frame(self, style="App.TFrame")
        frm_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ttk.Label(frm_status, textvariable=self.status,
                  style="App.TLabel").pack(side=tk.LEFT)
        ttk.Label(frm_status, textvariable=self.fit,
                  style="App.TLabel").pack(side=tk.RIGHT)

    def on_open(self):
        self.status.set(_("Section: {0}").format(self.engine.get_section()))
        self.add_row(FIRST_HEIGHT_MM)
        self.rows[0]["ent_text"].focus_set()

    # --- the lines ----------------------------------------------------------

    def add_row(self, height_mm):
        """A new line at the bottom: text, height, alignment."""
        line = len(self.rows) + 1
        text = tk.StringVar()
        height = tk.StringVar(value=str(height_mm))
        align = tk.StringVar(value=_(ALIGNS[1][1]))

        ent_text = ttk.Entry(self.frm_lines, textvariable=text,
                             width=self.engine.tools.FIELD_NAME)
        spn_height = ttk.Spinbox(self.frm_lines, textvariable=height,
                                 from_=HEIGHT_MIN_MM, to=HEIGHT_MAX_MM,
                                 increment=HEIGHT_STEP_MM, width=6)
        cb_align = ttk.Combobox(self.frm_lines, textvariable=align,
                                state="readonly", width=8,
                                values=[_(word) for code, word in ALIGNS])
        ent_text.grid(row=line, column=0, sticky=tk.EW, padx=2, pady=2)
        spn_height.grid(row=line, column=1, padx=2, pady=2)
        cb_align.grid(row=line, column=2, padx=2, pady=2)

        for variable in (text, height, align):
            variable.trace_add("write", self.on_change)

        self.rows.append({"text": text, "height": height, "align": align,
                          "widgets": (ent_text, spn_height, cb_align),
                          "ent_text": ent_text})
        self.set_preview()

    def on_add(self, evt=None):
        self.add_row(NEXT_HEIGHT_MM)
        self.rows[-1]["ent_text"].focus_set()

    def on_remove(self, evt=None):
        """Take away the last line; the first one always stays."""
        if len(self.rows) > 1:
            row = self.rows.pop()
            for widget in row["widgets"]:
                widget.destroy()
            self.set_preview()

    def on_change(self, *args):
        self.set_preview()

    # --- the preview --------------------------------------------------------

    def is_height(self, text):
        """True when the height typed is a number in the allowed range."""
        valid = False
        try:
            value = float(text.replace(",", "."))
            valid = HEIGHT_MIN_MM <= value <= HEIGHT_MAX_MM
        except ValueError:
            valid = False
        return valid

    def get_align(self, word):
        """The stored code of an alignment, from the word on screen."""
        code = "C"
        for stored, english in ALIGNS:
            if _(english) == word:
                code = stored
        return code

    def get_elements(self):
        """The lines as Layout reads them."""
        elements = []
        for row in self.rows:
            height = float(row["height"].get().replace(",", "."))
            elements.append({"kind": "text",
                             "content": row["text"].get(),
                             "height_mm": height,
                             "align": self.get_align(row["align"].get())})
        return elements

    def set_preview(self):
        """Draw the label again, unless a height is being typed.

        Half a number - '3.' or an empty box - is not an error while the
        field still has the cursor in it: the preview waits, and says why.
        """
        heights = [row["height"].get() for row in self.rows]
        wrong = [text for text in heights if not self.is_height(text)]

        if wrong:
            self.fit.set(_("Height from {0} to {1} mm").format(
                HEIGHT_MIN_MM, HEIGHT_MAX_MM))
        else:
            elements = self.get_elements()
            fitting = self.layout.is_fitting(elements)
            items = self.layout.get_items(elements,
                                          self.engine.get_section())
            self.preview.set_items(items, fitting)
            if fitting:
                self.fit.set(_("The lines fit."))
            else:
                self.fit.set(_("Too tall by {0:.1f} mm").format(
                    self.layout.get_overflow_mm(elements)))
