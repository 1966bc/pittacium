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

#: What a line can be: text, or a barcode by its symbology code.
KINDS = (("TEXT", "Text"), ("I2OF5", "Interleaved 2 of 5"),
         ("CODE128", "Code 128"))

#: The height a line takes when it becomes a barcode: bars a scanner
#: reads without aiming.
BARCODE_HEIGHT_MM = 8.0

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
        #: The line the cursor was last in.
        self.current = None
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
        self.frm_lines.columnconfigure(1, weight=1)
        headings = (_("Type"), _("Text"), _("Height mm"), _("Align"))
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

        # Close goes last, under the copies, the furthest from Print.
        frm_close = self.engine.tools.get_button_column(
            frm_actions, ((_("Close"), self.parent.on_exit),))
        frm_close.pack(fill=tk.X, pady=(8, 0))

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
        """A new line at the bottom: type, text, height, alignment."""
        kind = tk.StringVar(value=_(KINDS[0][1]))
        text = tk.StringVar()
        height = tk.StringVar(value=str(height_mm))
        align = tk.StringVar(value=_(ALIGNS[1][1]))

        cb_kind = ttk.Combobox(self.frm_lines, textvariable=kind,
                               state="readonly", width=16,
                               values=[_(word) for code, word in KINDS])
        ent_text = ttk.Entry(self.frm_lines, textvariable=text,
                             width=self.engine.tools.FIELD_CODE + 8)
        spn_height = ttk.Spinbox(self.frm_lines, textvariable=height,
                                 from_=HEIGHT_MIN_MM, to=HEIGHT_MAX_MM,
                                 increment=HEIGHT_STEP_MM, width=6)
        cb_align = ttk.Combobox(self.frm_lines, textvariable=align,
                                state="readonly", width=8,
                                values=[_(word) for code, word in ALIGNS])
        row = {"kind": kind, "text": text, "height": height, "align": align,
               "widgets": (cb_kind, ent_text, spn_height, cb_align),
               "ent_text": ent_text}
        self.rows.append(row)
        self.set_grid()

        for variable in (text, height, align):
            variable.trace_add("write", self.on_change)
        kind.trace_add("write", lambda *args: self.on_kind(row))

        # The line somebody is on is the one Remove line takes away.
        for widget in row["widgets"]:
            widget.bind("<FocusIn>", lambda evt: self.set_current(row),
                        add="+")

        # The keys of a text editor: Return goes to the next line, making
        # it when there is none; the arrows move between lines; BackSpace
        # on an empty line takes it away. A line can be removed from the
        # middle, so the bindings carry the line itself and ask where it
        # is now, rather than remembering where it was.
        ent_text.bind("<Return>", lambda evt: self.on_next(row))
        ent_text.bind("<KP_Enter>", lambda evt: self.on_next(row))
        ent_text.bind("<Down>", lambda evt: self.on_step(row, 1))
        ent_text.bind("<Up>", lambda evt: self.on_step(row, -1))
        ent_text.bind("<BackSpace>", lambda evt: self.on_backspace(row))

        self.set_current(row)
        self.set_preview()

    def set_grid(self):
        """Every line in its place, from the top: after a removal too."""
        for index, row in enumerate(self.rows):
            for column, widget in enumerate(row["widgets"]):
                sticky = ""
                if column == 1:
                    sticky = tk.EW
                widget.grid(row=index + 1, column=column, sticky=sticky,
                            padx=2, pady=2)

    def set_current(self, row):
        self.current = row

    def on_kind(self, row):
        """A line changed type: a barcode wants taller bars than text.

        The height changes only when it is still the default of the other
        type, so a height somebody chose is not thrown away.
        """
        code = self.get_kind(row["kind"].get())
        if code == "TEXT" and row["height"].get() == str(BARCODE_HEIGHT_MM):
            row["height"].set(str(NEXT_HEIGHT_MM))
        elif code != "TEXT" and row["height"].get() in (
                str(NEXT_HEIGHT_MM), str(FIRST_HEIGHT_MM)):
            row["height"].set(str(BARCODE_HEIGHT_MM))
        self.set_preview()

    def on_next(self, row):
        """Return: the line below, a new one if this is the last."""
        index = self.rows.index(row)
        if index + 1 < len(self.rows):
            self.set_cursor(index + 1)
        else:
            self.on_add()
        return "break"

    def on_step(self, row, step):
        """An arrow: the line above or below, if there is one."""
        self.set_cursor(self.rows.index(row) + step)
        return "break"

    def set_cursor(self, index):
        """The cursor to the end of a line's text, if the line exists."""
        if 0 <= index < len(self.rows):
            entry = self.rows[index]["ent_text"]
            entry.focus_set()
            entry.icursor(tk.END)

    def on_backspace(self, row):
        """BackSpace on an empty line removes it, like a line break.

        Anywhere else BackSpace deletes a character as always: returning
        None lets the entry do it. The first line stays.
        """
        handled = None
        if row["text"].get() == "" and len(self.rows) > 1:
            self.remove_row(row)
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
        """Take away the line the cursor is on; one line always stays.

        A line with text is asked about first, with No as the default:
        removing one is rare, so the question does not become a reflex,
        and what it would throw away is something somebody typed. An empty
        line goes without a word - there is nothing to lose.
        """
        if len(self.rows) > 1:
            row = self.rows[-1]
            if self.current in self.rows:
                row = self.current
            text = row["text"].get().strip()
            agreed = True
            if text != "":
                agreed = messagebox.askyesno(
                    self.engine.app_title,
                    _("Remove the line \"{0}\"?").format(text),
                    default=messagebox.NO, parent=self.parent)
            if agreed:
                self.remove_row(row)

    def remove_row(self, row):
        """A line out, the others closed up, the cursor on the one above."""
        index = self.rows.index(row)
        self.rows.remove(row)
        for widget in row["widgets"]:
            widget.destroy()
        self.set_grid()
        self.set_cursor(max(0, index - 1))
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

    def get_kind(self, word):
        """The stored code of a line type, from the word on screen."""
        code = "TEXT"
        for stored, english in KINDS:
            if _(english) == word:
                code = stored
        return code

    def get_elements(self):
        """The lines as Layout reads them."""
        elements = []
        for row in self.rows:
            height = float(row["height"].get().replace(",", "."))
            element = {"kind": "text", "content": row["text"].get(),
                       "height_mm": height,
                       "align": self.get_align(row["align"].get())}
            code = self.get_kind(row["kind"].get())
            if code != "TEXT":
                element["kind"] = "barcode"
                element["symbology"] = code
                element["human_readable"] = True
            elements.append(element)
        return elements

    def get_problem(self):
        """The first line that cannot be printed as it is, translated."""
        problems = self.layout.get_problems(self.get_elements())
        problem = ""
        if problems:
            problem = _(problems[0])
        return problem

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
            problem = self.get_problem()
            if problem:
                self.fit.set(problem)
            elif fitting:
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
        elif self.get_problem():
            refusal = self.get_problem()
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
