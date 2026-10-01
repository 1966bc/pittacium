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
from tkinter import font
from tkinter import messagebox
from tkinter import ttk

from i18n import _
from ui.preview import Preview
from ui.settings import UI as SettingsUI
from ui.window import Window

#: The alignments, as stored and as read.
ALIGNS = (("L", "Left"), ("C", "Centre"), ("R", "Right"))

#: The heights a line can be given, in millimetres.
HEIGHT_MIN_MM = 2.0
HEIGHT_MAX_MM = 20.0
HEIGHT_STEP_MM = 0.5

#: The colour of a warning on the status bar.
WARNING_COLOUR = "#c02020"

#: A new line: the first is the title, the others are smaller.
FIRST_HEIGHT_MM = 5.0
NEXT_HEIGHT_MM = 3.5


class Main(ttk.Frame, Window):
    """The frame inside the root window."""

    def __init__(self, parent):
        super().__init__(parent, style="App.TFrame", padding=8)
        self.parent = parent
        self.status = tk.StringVar()
        self.warning = tk.StringVar()
        self.fit = tk.StringVar()
        #: One dictionary per line: its variables and its widgets.
        self.rows = []
        self.label_format = self.engine.get_formats()[0]
        self.layout = self.engine.get_layout(self.label_format)
        self.init_menu()
        self.init_ui()

    def init_menu(self):
        menubar = tk.Menu(self.parent)
        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label=_("Settings..."), underline=0,
                              command=self.on_settings_window)
        menu_file.add_separator()
        menu_file.add_command(label=_("Exit"), underline=0,
                              command=self.parent.on_exit)
        menubar.add_cascade(label=_("File"), menu=menu_file, underline=0)
        self.parent.config(menu=menubar)

    def init_ui(self):
        # The label on top, as on a sheet: it is looked at before it is
        # written. The lines under it, the buttons down the right edge.
        frm_body = ttk.Frame(self, style="App.TFrame")
        frm_body.pack(fill=tk.BOTH, expand=1)
        frm_body.columnconfigure(0, weight=1)

        self.preview = Preview(frm_body, self.layout)
        self.preview.grid(row=0, column=0)

        self.frm_lines = ttk.LabelFrame(frm_body, text=_("Lines"),
                                        padding=8)
        self.frm_lines.grid(row=1, column=0, sticky=tk.NSEW, pady=(8, 0))
        self.frm_lines.columnconfigure(0, weight=1)
        headings = (_("Text"), _("Height mm"), _("Align"))
        for column, heading in enumerate(headings):
            ttk.Label(self.frm_lines, text=heading,
                      style="App.TLabel").grid(row=0, column=column,
                                               sticky=tk.W, padx=2)

        frm_actions = ttk.Frame(frm_body, style="App.TFrame")
        frm_actions.grid(row=0, column=1, rowspan=2, sticky=tk.N,
                         padx=(8, 0))

        buttons = ((_("Print"), self.on_print),
                   (_("Add line"), self.on_add),
                   (_("Remove line"), self.on_remove))
        frm_buttons = self.engine.tools.get_button_column(frm_actions,
                                                          buttons)
        frm_buttons.pack(fill=tk.X)
        self.parent.bind("<Control-p>", self.on_print)

        frm_copies = ttk.Frame(frm_actions, style="App.TFrame")
        frm_copies.pack(fill=tk.X, padx=5, pady=(8, 0))
        ttk.Label(frm_copies, text=_("Copies"),
                  style="App.TLabel").pack(side=tk.LEFT)
        printer = self.engine.printer
        self.copies = tk.StringVar(value=str(printer.COPIES_MIN))
        self.spn_copies = ttk.Spinbox(frm_copies, textvariable=self.copies,
                                      from_=printer.COPIES_MIN,
                                      to=printer.COPIES_MAX, increment=1,
                                      width=4)
        self.spn_copies.pack(side=tk.RIGHT)

        # The status bar has a fixed height and asks for no width: a long
        # message is cut at the edge rather than widening the whole
        # window. The width is the body's to decide.
        line = font.nametofont("TkDefaultFont").metrics("linespace")
        # Two lines, each with the label's own padding above and below.
        frm_status = ttk.Frame(self, style="App.TFrame",
                               height=2 * (line + 8))
        frm_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        frm_status.grid_propagate(False)
        frm_status.columnconfigure(1, weight=1)
        ttk.Label(frm_status, textvariable=self.status,
                  style="App.TLabel").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(frm_status, textvariable=self.fit,
                  style="App.TLabel").grid(row=0, column=1, sticky=tk.E)
        # Red, and in words a colleague at the bench understands: the
        # program looks as if it works and no label comes out.
        ttk.Label(frm_status, textvariable=self.warning,
                  style="App.TLabel",
                  foreground=WARNING_COLOUR).grid(row=1, column=0,
                                                  columnspan=2,
                                                  sticky=tk.W)

    def on_open(self):
        self.engine.events.subscribe("settings", self.on_settings)
        self.set_status()
        self.add_row(FIRST_HEIGHT_MM)
        self.rows[0]["ent_text"].focus_set()

    def set_status(self):
        """Say the section, and say it loudly when nothing will print."""
        self.status.set(_("Section: {0}").format(self.engine.get_section()))
        warning = ""
        if not self.engine.printer.is_printing():
            warning = _("Printer not set up: labels do NOT come out. "
                        "See File > Settings.")
        self.warning.set(warning)

    def on_settings_window(self, evt=None):
        self.engine.windows.show("settings", lambda: SettingsUI(self.parent))

    def on_settings(self, row_id=None):
        """The settings changed: the resolution may have, and the section.

        The layout is rebuilt at the printer's resolution and the label
        drawn again with the section it now carries.
        """
        self.layout = self.engine.get_layout(self.label_format)
        self.preview.set_layout(self.layout)
        self.set_status()
        self.set_preview()

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

        # The keys of a text editor: Return goes to the next line, making
        # it when there is none; the arrows move between lines; BackSpace
        # on an empty last line takes it away. Lines are only ever added
        # and removed at the bottom, so a line's index does not change.
        index = len(self.rows)
        ent_text.bind("<Return>", lambda evt: self.on_next(index))
        ent_text.bind("<KP_Enter>", lambda evt: self.on_next(index))
        ent_text.bind("<Down>", lambda evt: self.on_move(index + 1))
        ent_text.bind("<Up>", lambda evt: self.on_move(index - 1))
        ent_text.bind("<BackSpace>", lambda evt: self.on_backspace(index))

        self.rows.append({"text": text, "height": height, "align": align,
                          "widgets": (ent_text, spn_height, cb_align),
                          "ent_text": ent_text})
        self.set_preview()

    def on_next(self, index):
        """Return: the line below, a new one if this is the last."""
        if index + 1 < len(self.rows):
            self.on_move(index + 1)
        else:
            self.on_add()
        return "break"

    def on_move(self, index):
        """The cursor to the text of another line, if there is one."""
        if 0 <= index < len(self.rows):
            entry = self.rows[index]["ent_text"]
            entry.focus_set()
            entry.icursor(tk.END)
        return "break"

    def on_backspace(self, index):
        """BackSpace on the empty last line removes it, like a line break.

        Anywhere else BackSpace deletes a character as always: returning
        None lets the entry do it.
        """
        handled = None
        last = index == len(self.rows) - 1
        empty = self.rows[index]["text"].get() == ""
        if last and empty and index > 0:
            self.on_remove()
            self.on_move(index - 1)
            handled = "break"
        return handled

    def on_add(self, evt=None):
        """A new line, up to as many as the label can hold at all.

        The limit is the lines of the smallest height that fit: past it, no
        choice of heights could make the label fit.
        """
        limit = self.layout.get_max_lines(HEIGHT_MIN_MM)
        if len(self.rows) < limit:
            self.add_row(NEXT_HEIGHT_MM)
            self.rows[-1]["ent_text"].focus_set()
        else:
            self.fit.set(_("At most {0} lines on this label.").format(limit))

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

    # --- printing -----------------------------------------------------------

    def get_refusal(self):
        """Why this label cannot be printed now, or an empty string."""
        heights = [row["height"].get() for row in self.rows]
        wrong = [text for text in heights if not self.is_height(text)]
        printer = self.engine.printer
        refusal = ""

        if wrong:
            refusal = _("Height from {0} to {1} mm").format(HEIGHT_MIN_MM,
                                                          HEIGHT_MAX_MM)
        elif not self.layout.get_lines(self.get_elements()):
            refusal = _("Nothing to print: every line is empty.")
        elif not self.layout.is_fitting(self.get_elements()):
            refusal = _("Too tall by {0:.1f} mm").format(
                self.layout.get_overflow_mm(self.get_elements()))
        elif not printer.is_copies(self.copies.get()):
            refusal = _("Copies from {0} to {1}").format(
                printer.COPIES_MIN, printer.COPIES_MAX)

        return refusal

    def on_print(self, evt=None):
        """Print now, with no question: the preview is the question.

        After printing the copies go back to one, so that whoever comes
        next does not print twenty by pressing Print.
        """
        refusal = self.get_refusal()

        if refusal:
            messagebox.showwarning(self.engine.app_title, refusal,
                                   parent=self.parent)
        else:
            copies = int(self.copies.get())
            items = self.layout.get_items(self.get_elements(),
                                          self.engine.get_section())
            where = self.engine.printer.print_label(
                self.layout, items, copies,
                self.label_format["description"])
            if self.engine.printer.is_printing():
                self.fit.set(_("Labels printed: {0}").format(copies))
            else:
                self.fit.set(_("Label NOT printed: the printer is not "
                               "set up."))
            self.copies.set(str(self.engine.printer.COPIES_MIN))
