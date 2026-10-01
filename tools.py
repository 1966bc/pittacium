# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Widget helpers: theme, factories, validation, cursor.

One job: helping to build widgets. No database access, no file handling, no
knowledge of labels or printers.
"""

import tkinter as tk
from tkinter import font
from tkinter import messagebox
from tkinter import ttk

from i18n import _


class Tools:
    """Appearance and behaviour shared by every window."""

    # --- palette ------------------------------------------------------------
    # Meaning first, hue second: the names say what a colour is for, so a
    # future change of taste does not turn into a search for '255, 160, 122'.
    BACKGROUND = (240, 240, 237)
    FOREGROUND = (0, 0, 0)
    WHITE = (255, 255, 255)
    MANDATORY = (0, 0, 255)
    # A row withdrawn from use, and whose installation this is.
    DISCARDED = (140, 140, 140)     # row withdrawn (enable 0)
    IDENTITY = (70, 70, 70)         # whose installation, on the status bar

    # The chrome, which is not the same thing as the palette above. Those
    # colours carry meaning and an operator reads them; these are the edges,
    # the troughs and the hovers - the widget saying what it is and whether it
    # is under the pointer. They are the ones 'clam' would otherwise pick for
    # itself, and picking them is most of the difference between a window that
    # looks configured and one that looks default.
    BORDER = (169, 169, 165)            # the outline of anything with an edge
    TROUGH = (222, 222, 218)            # scrollbar channel, progress bar
    HOVER = (228, 231, 235)             # under the pointer
    PRESSED = (205, 209, 214)           # while the mouse is down
    FOCUS = (58, 110, 165)              # where the keyboard is
    SELECTED = (51, 103, 158)           # the chosen row, the selected text
    UNAVAILABLE = (150, 150, 150)       # a control that is disabled

    # --- field widths -------------------------------------------------------
    # Three, and named for what the field holds rather than for how wide it
    # is - the same rule the palette follows. A width written once per form is
    # a width decided once per form, and no two forms agree on how wide a
    # name is.
    #
    # In characters, because that is what ttk asks for and what the question
    # actually is: how much of the value has to be readable without scrolling.
    #
    # A field wider than its content is not generous, it is a promise that
    # more was expected - an operator who sees room for sixty characters of
    # note writes sixty characters of note, and the listing that shows it is
    # ten pixels wide per column.
    FIELD_CODE = 16      # a thing with a shape: a level, a lot, a date
    FIELD_NAME = 32      # a thing with a name: a person, a supplier, a part
    FIELD_PATH = 48      # a line of prose or a folder: where truncating hurts

    #: Every button in a button column, in every window, is this wide. Not
    #: the widest label of its own column, which is what stacking already
    #: gave and which made each window a different shape - a Close two
    #: characters wide beside a list and eleven beside another.
    #:
    #: Negative, and that is the whole of it: ttk reads a negative width as a
    #: minimum rather than a measurement. A button is never narrower than
    #: eight characters and never wider than its own words.
    #:
    #: A fixed width would have to fit the longest label in the longer of
    #: the two languages, and every button would be that wide just to say
    #: Save. A minimum keeps them one shape - inside a button column the
    #: fill does the levelling - decided by the longest label in that
    #: window rather than in the whole program, and it needs no keeping in
    #: step with the translations.
    BUTTON_WIDTH = -8

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    # --- theme --------------------------------------------------------------

    def get_rgb(self, red, green, blue):
        """An (r, g, b) triple as the hex string tkinter expects."""
        return "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)

    def set_style(self, theme):
        """Configure every style the application uses.

        'clam' is the sensible default: it exists on Windows and on Linux and
        looks the same on both, while 'vista' and 'xpnative' exist only here.

        Everything below is stock ttk: configure, map, layout. No theme file,
        nothing to import, nothing to add to the spec. 'clam' is the only one
        of the built-in themes whose colours are settable at all - 'default'
        and 'alt' draw most of their edges themselves - so the choice of clam
        was already the choice that makes this possible.
        """
        self.style = ttk.Style()

        if theme in self.style.theme_names():
            self.style.theme_use(theme)
        else:
            raise ValueError("unknown ttk theme: {0}".format(theme))

        background = self.get_rgb(*self.BACKGROUND)
        foreground = self.get_rgb(*self.FOREGROUND)
        white = self.get_rgb(*self.WHITE)
        border = self.get_rgb(*self.BORDER)
        trough = self.get_rgb(*self.TROUGH)
        hover = self.get_rgb(*self.HOVER)
        pressed = self.get_rgb(*self.PRESSED)
        focus = self.get_rgb(*self.FOCUS)
        selected = self.get_rgb(*self.SELECTED)
        unavailable = self.get_rgb(*self.UNAVAILABLE)

        # The row height comes from the font rather than from a number, so a
        # machine set to large text gets taller rows instead of clipped ones.
        base = font.nametofont("TkDefaultFont")
        row_height = base.metrics("linespace") + 8

        # The root style. Everything inherits from it, so a colour set here is
        # set for widgets nobody thought to name - which is the case that has
        # always leaked the theme's own grey into a window.
        #
        # lightcolor and darkcolor are clam's bevel: the two highlights it
        # paints inside every border to fake relief. Set to the background
        # they disappear, and what is left is the one line of bordercolor.
        # That single line, and not a colour, is the whole difference between
        # this and a window from 1998.
        self.style.configure(".",
                             background=background,
                             foreground=foreground,
                             fieldbackground=white,
                             bordercolor=border,
                             lightcolor=background,
                             darkcolor=background,
                             troughcolor=trough,
                             selectbackground=selected,
                             selectforeground=white,
                             font="TkDefaultFont")

        self.style.map(".", foreground=[("disabled", unavailable)])

        self.set_classic(self.style.master)

        self.style.configure("App.TFrame", background=background)
        self.style.configure("App.TLabel", padding=2, anchor=tk.W)

        # A button is a rectangle with one line around it, and it answers the
        # pointer. The second half is the part that was missing: without a map
        # nothing on the screen ever acknowledges the mouse, and an interface
        # that does not respond to being pointed at reads as a picture of an
        # interface.
        self.style.configure("App.TButton",
                             padding=(6, 5), anchor=tk.CENTER,
                             borderwidth=1, relief=tk.SOLID)
        self.style.map("App.TButton",
                       background=[("pressed", pressed),
                                   ("active", hover),
                                   ("disabled", background)],
                       bordercolor=[("pressed", focus),
                                    ("active", focus),
                                    ("focus", focus),
                                    ("disabled", border)],
                       lightcolor=[("pressed", pressed), ("active", hover)],
                       darkcolor=[("pressed", pressed), ("active", hover)])

        # The dotted rectangle clam draws inside a focused button. It says
        # what the border already says now that the border changes colour,
        # and it is the single most dated thing on the screen.
        self.style.layout("App.TButton",
                          self.get_layout_without("App.TButton", "focus"))

        self.style.configure("App.TLabelframe",
                             relief=tk.SOLID, borderwidth=1, padding=8,
                             bordercolor=border,
                             lightcolor=background, darkcolor=background)
        self.style.configure("App.TLabelframe.Label",
                             background=background, padding=(2, 0))

        # On the base names and not on App.TEntry, which is what they were
        # on and what nobody used: of the sixteen fields in this application
        # exactly one asked for the application's own style, and the other
        # fifteen took ttk's. A style that has to be asked for is a style
        # that will be forgotten, and the forgetting is silent - the field
        # looks like a field, just not like the one beside it.
        #
        # Named styles still work and still inherit from these: ttk resolves
        # App.TEntry by walking to TEntry, so what is set here reaches
        # everything and a named style adds only what it means to change.
        self.style.configure("TEntry",
                             padding=(6, 4),
                             fieldbackground=white,
                             lightcolor=white, darkcolor=white,
                             insertcolor=foreground)
        self.style.map("TEntry",
                       bordercolor=[("focus", focus)],
                       lightcolor=[("focus", focus)],
                       darkcolor=[("focus", focus)],
                       fieldbackground=[("disabled", background),
                                        ("readonly", background)])

        self.style.configure("TCombobox",
                             padding=(6, 4),
                             arrowsize=13, arrowcolor=foreground,
                             lightcolor=white, darkcolor=white)
        # foreground is mapped here because clam maps it for this class and
        # its map replaces the root's. Clam draws a focused readonly box as
        # white text on its blue selection; fieldbackground below takes the
        # blue away, and a readonly combo reached with Tab went white on
        # white and looked empty. The same map had also dropped the root's
        # grey, so a disabled combo was the one field drawn black.
        self.style.map("TCombobox",
                       bordercolor=[("focus", focus)],
                       lightcolor=[("focus", focus)],
                       darkcolor=[("focus", focus)],
                       foreground=[("readonly", "focus", foreground),
                                   ("disabled", unavailable)],
                       fieldbackground=[("readonly", white),
                                        ("disabled", background)],
                       arrowcolor=[("disabled", unavailable)])

        # The date field is three of these, and the only ones in the
        # application. They were the last widget still drawn by the theme.
        self.style.configure("TSpinbox",
                             padding=(4, 4),
                             fieldbackground=white,
                             lightcolor=white, darkcolor=white,
                             arrowsize=10, arrowcolor=foreground,
                             insertcolor=foreground)
        self.style.map("TSpinbox",
                       bordercolor=[("focus", focus)],
                       lightcolor=[("focus", focus)],
                       darkcolor=[("focus", focus)],
                       fieldbackground=[("disabled", background)],
                       arrowcolor=[("disabled", unavailable)])

        self.style.configure("TSeparator", background=border)

        self.style.configure("App.TRadiobutton", padding=4)
        self.style.configure("App.TCheckbutton", padding=4)
        for name in ("App.TRadiobutton", "App.TCheckbutton"):
            self.style.configure(name,
                                 indicatorbackground=white,
                                 indicatorforeground=foreground,
                                 focuscolor=background)
            self.style.map(name,
                           background=[("active", background)],
                           indicatorbackground=[("pressed", hover),
                                                ("disabled", background)],
                           bordercolor=[("focus", focus)])

        self.style.configure("Mandatory.TEntry",
                             padding=(6, 4),
                             foreground=self.get_rgb(*self.MANDATORY),
                             fieldbackground=self.get_rgb(*self.WHITE),
                             lightcolor=white, darkcolor=white,
                             insertcolor=foreground)
        self.style.map("Mandatory.TEntry",
                       bordercolor=[("focus", focus)],
                       lightcolor=[("focus", focus)],
                       darkcolor=[("focus", focus)])

        self.style.configure("TScrollbar",
                             troughcolor=trough, background=border,
                             bordercolor=trough, arrowcolor=foreground,
                             borderwidth=0, relief=tk.FLAT,
                             arrowsize=13, width=13)
        self.style.map("TScrollbar",
                       background=[("pressed", focus), ("active", pressed)])

        self.style.configure("TProgressbar",
                             troughcolor=trough, background=focus,
                             bordercolor=border, lightcolor=focus,
                             darkcolor=focus, borderwidth=1, thickness=14)

        # The status bar, in two weights because it says two kinds of thing.
        #
        # On the left is what just happened, and it changes: plain, and given
        # enough room around it to be read at a glance rather than squinted
        # at. On the right is what does not change while the program is open,
        # in a quieter grey: standing information that shouts competes with
        # the message that has just arrived.
        #
        # The frame carries the border and the labels inside it carry none.
        # A label with a border of its own is a panel as wide as whatever it
        # happens to hold, so three of them are three seams at three widths -
        # and the middle one moved every time the operator changed, which is
        # a line the eye follows for nothing. One strip, and separators at
        # fixed places inside it.
        #
        # Weight is not what tells the two halves apart, for the same reason.
        # The grey already says which side is standing information; bold on
        # top of it was a second axis of difference doing the first one's job
        # again. Weight does one job only, and inside the left half: the row
        # the message is about is bold, what is said about it is not. There
        # the two are one sentence in one place and nothing else separates
        # them - the name and the warning used to run together with a dash
        # between, and the eye had to find the dash to know where the name
        # ended.
        #
        # The bevel and nothing else. darkcolor is the shaded side, which for
        # a sunken relief is the top and the left; lightcolor is the lit side
        # and is set to the ground so that it disappears - so the bar shows one
        # line along its top rather than a groove all the way round. With every
        # other edge in the window down to a single line, a bevelled strip
        # along the bottom was the last thing left casting a shadow.
        #
        # borderwidth and relief are NOT set here, and that is deliberate: a
        # window that draws a sunken strip should say so where it draws it.
        # What a thing looks like is written where it is built, and a shared
        # style carries only what every window has in common, which is these
        # three colours.
        #
        # A status bar is flat until its window adds
        # `borderwidth=1, relief=tk.SUNKEN` where it builds the strip - the
        # full option name, because ttk::frame has no `bd` abbreviation.
        self.style.configure("StatusBar.TFrame",
                             bordercolor=background,
                             darkcolor=border, lightcolor=background)
        # The named font and not a size. Every label that pinned nine points
        # stayed at nine while the rest of the interface grew, which is the
        # one way a font setting fails that nobody sees until they need it.
        self.style.configure("StatusBar.TLabel",
                             padding=(6, 4), border=0, relief=tk.FLAT,
                             font="TkDefaultFont")
        # No padding on the right: what follows brings its own 6, and two
        # paddings between a name and the sentence about it read as a column
        # break rather than a space.
        self.style.configure("StatusKey.TLabel",
                             padding=(6, 4, 0, 4), border=0, relief=tk.FLAT,
                             font=(base.cget("family"), base.cget("size"),
                                   "bold"))
        self.style.configure("Identity.TLabel",
                             padding=(6, 4), border=0, relief=tk.FLAT,
                             foreground=self.get_rgb(*self.IDENTITY),
                             font="TkDefaultFont")

        # Tk 8.6.8 ships the bug that makes tag colours in a Treeview be
        # ignored (bugs.python.org/issue36468, fixed in Tk 8.6.10). The map has
        # to be filtered, otherwise every row is drawn in the default colour
        # and the whole point of colouring them is lost. Check the patchlevel
        # before deciding this can be removed.
        self.style.map("Treeview",
                       foreground=self.get_fixed_map("foreground"),
                       background=self.get_fixed_map("background"))

        # Room around a row. Sixty rows at the font's own height is a block of
        # text; the same sixty with a few pixels of air are a list, and the
        # colours on them stop touching each other.
        self.style.configure("Treeview",
                             rowheight=row_height,
                             background=white, fieldbackground=white,
                             borderwidth=1, relief=tk.SOLID)

        # Not TkHeadingFont, which Tk defines as bold and which DejaVu Sans
        # draws very heavy indeed. A heading here is already told apart three
        # ways - it sits on the window's grey rather than on the white of the
        # rows, it has its own border, and it does not scroll away - and a
        # fourth in bold is the one that shouts. At eleven points it was the
        # heaviest thing on the screen and the rows underneath, which are
        # what the operator is reading, looked like a caption to it.
        self.style.configure("Treeview.Heading",
                             background=background,
                             padding=(6, 5),
                             borderwidth=1, relief=tk.SOLID,
                             bordercolor=border,
                             font=(base.cget("family"), base.cget("size")))
        self.style.map("Treeview.Heading",
                       background=[("active", hover)],
                       relief=[("pressed", tk.SUNKEN)])

        # The dotted rectangle again, this time around the focused row, where
        # it lands on top of the tag colour that is carrying the meaning.
        self.style.layout("Item", self.get_layout_without("Item", "focus"))

    def set_classic(self, root):
        """Colour the widgets ttk cannot reach.

        Four kinds are left, and they are left for a reason rather than by
        oversight: a menu, a text, a listbox and the listbox a combobox drops
        are classic Tk widgets with no style engine behind them. ttk has no
        menu at all, and its text and listbox do not exist - so these are not
        a fallback anybody chose, they are the only widget there is.

        They are set through the option database, which is Tk's own way of
        saying 'unless told otherwise'. That matters twice: a widget built
        with an explicit colour still keeps it, and an option set here
        reaches widgets this class has never heard of - which is the whole
        point, since the menus are built in ui/main.py and the text in three
        other modules.

        Only widgets created after this runs are affected, and set_style is
        the third statement of App.__init__, before any window exists.
        """
        if root is not None:
            background = self.get_rgb(*self.BACKGROUND)
            foreground = self.get_rgb(*self.FOREGROUND)
            white = self.get_rgb(*self.WHITE)
            selected = self.get_rgb(*self.SELECTED)
            border = self.get_rgb(*self.BORDER)
            unavailable = self.get_rgb(*self.UNAVAILABLE)

            for pattern, value in (
                    # The menu bar and every menu under it. activeBorderWidth
                    # is the raised box Tk draws around the highlighted item,
                    # and it is the one thing on the screen still drawn the
                    # way a menu was drawn in 1995.
                    ("*Menu.background", background),
                    ("*Menu.foreground", foreground),
                    ("*Menu.activeBackground", selected),
                    ("*Menu.activeForeground", white),
                    ("*Menu.disabledForeground", unavailable),
                    ("*Menu.selectColor", foreground),
                    ("*Menu.activeBorderWidth", "0"),
                    ("*Menu.relief", "flat"),
                    ("*Menu.borderWidth", "1"),
                    # The method, the licence and the note on a case: three
                    # texts, all of them read rather than typed into, and all
                    # of them a page.
                    ("*Text.background", white),
                    ("*Text.foreground", foreground),
                    ("*Text.selectBackground", selected),
                    ("*Text.selectForeground", white),
                    ("*Text.insertBackground", foreground),
                    ("*Text.highlightThickness", "0"),
                    ("*Text.borderWidth", "1"),
                    ("*Text.relief", "solid"),
                    # The sequence chooser and the column list.
                    ("*Listbox.background", white),
                    ("*Listbox.foreground", foreground),
                    ("*Listbox.selectBackground", selected),
                    ("*Listbox.selectForeground", white),
                    ("*Listbox.activeStyle", "none"),
                    ("*Listbox.highlightThickness", "0"),
                    ("*Listbox.borderWidth", "1"),
                    ("*Listbox.relief", "solid"),
                    # The listbox a combobox drops. More specific than the
                    # line above it, so it wins where the two disagree, and
                    # it disagrees on the border: a popdown draws its own.
                    ("*TCombobox*Listbox.background", white),
                    ("*TCombobox*Listbox.foreground", foreground),
                    ("*TCombobox*Listbox.selectBackground", selected),
                    ("*TCombobox*Listbox.selectForeground", white),
                    ("*TCombobox*Listbox.borderWidth", "0")):
                root.option_add(pattern, value)

            # Not the canvas. The two in this application are matplotlib's
            # figure and the column status card, and both paint every pixel
            # they own - a colour set here would be seen only in the moment
            # between a resize and the redraw, and only if it were wrong.

    def get_layout_without(self, style_name, element):
        """This style's layout with one element taken out of it.

        A ttk layout is a tree of (element, options) pairs, and removing a
        node means putting its children where it was rather than dropping
        them - the focus ring wraps the padding that holds the label, so
        deleting the branch would delete the text as well.

        The layout is read from the theme rather than written out here: what
        clam nests inside what is clam's business, and a layout copied into
        this file is a copy that goes stale the first time Tk changes.
        """
        def prune(layout):
            kept = []
            for name, options in layout:
                options = dict(options)
                children = options.get("children")
                if children:
                    options["children"] = prune(children)
                if name.split(".")[-1] == element:
                    kept.extend(options.get("children", []))
                else:
                    kept.append((name, options))
            return kept

        return prune(self.style.layout(style_name))

    def get_fixed_map(self, option):
        """Style map for `option` without the entries Tk 8.6.8 mishandles."""
        style = ttk.Style()
        return [element for element in style.map("Treeview", query_opt=option)
                if element[:2] != ("!disabled", "!selected")]

    # --- geometry -----------------------------------------------------------

    def hide_me(self, container):
        """Take a window off the screen while it is being built.

        The first statement of every Toplevel in this application, and the
        other half of center_me. Tk maps a Toplevel the moment it is created,
        at whatever corner the window manager picks, and it stays there and
        visible for as long as the window takes to build itself - which for
        the chromatogram means reading a trace out of the database and drawing
        two matplotlib axes. The operator sees the window appear in the top
        left, sit there empty, fill in, and jump to the middle.

        Withdrawn, none of that is on the screen. The window is measured while
        hidden - winfo_reqwidth is the size it asked for and needs no mapping
        - and center_me puts it back when it is finished and in place.
        """
        container.withdraw()

    def center_me(self, container, over=None):
        """Centre a window over the one that opened it, and show it.

        Over the parent by default, because that is where the operator is
        looking: a dialog that appears in the middle of a wide monitor while
        the main window sits on the left makes the eye travel for no reason,
        and on two monitors it can open on the other one.

        The window is kept whole on the screen. A dialog taller than what
        opened it would otherwise be centred with its title bar above the top
        edge, which puts it beyond reach of the mouse.

        It ends by showing the window, which is what pairs it with hide_me:
        every caller is at the point of saying 'it is built, let them see it',
        and splitting that into two calls is splitting a thing nobody wants
        half of.
        """
        container.update_idletasks()
        width = container.winfo_reqwidth()
        height = container.winfo_reqheight()

        parent = over
        if parent is None:
            parent = container.master
        if parent is not None and parent.winfo_exists() \
                and parent.winfo_width() > 1:
            x = parent.winfo_rootx() + (parent.winfo_width() - width) / 2
            y = parent.winfo_rooty() + (parent.winfo_height() - height) / 2
        else:
            x = (container.winfo_screenwidth() - width) / 2
            y = (container.winfo_screenheight() - height) / 2

        x = max(0, min(int(x), container.winfo_screenwidth() - width))
        y = max(0, min(int(y), container.winfo_screenheight() - height))
        container.geometry("+{0:d}+{1:d}".format(x, y))

        # Placed, then shown. On a window that was never hidden this does
        # nothing at all, so it is safe on every caller.
        container.deiconify()

    # --- widget factories ---------------------------------------------------

    def get_tree(self, container, columns, show=None):
        """Build a Treeview with its scrollbar.

        columns is a sequence of six-part specifications:

            (identifier, heading, anchor, stretch, minwidth, width)

        The first one is always '#0', the implicit column, and it carries the
        row identifier rather than data.
        """
        for spec in columns:
            if len(spec) != 6:
                raise ValueError(
                    "column specification needs six parts "
                    "(identifier, heading, anchor, stretch, minwidth, width), "
                    "got {0!r}".format(spec))

        headers = [spec[1] for spec in columns][1:]

        if show is None:
            tree = ttk.Treeview(container)
        else:
            tree = ttk.Treeview(container, show=show)

        tree["columns"] = headers

        for identifier, heading, anchor, stretch, minwidth, width in columns:
            tree.heading(identifier, text=heading, anchor=anchor)
            tree.column(identifier, anchor=anchor, stretch=stretch,
                        minwidth=minwidth, width=width)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL)
        scrollbar.configure(command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.set_tree_tags(tree)
        return tree

    def get_button_column(self, container, buttons, window=None):
        """A column of buttons down the right-hand side, all the same width.

        The layout every list window in this application uses, and it is not
        a preference. Buttons in a row along the bottom are all different
        widths, because a button is as wide as its label - and a translated
        label is a different width again, so a row that lines up in English
        does not in Italian. Stacked and filled to the column they are one
        shape, and the eye reads them as one group of choices about the list
        beside them rather than as a sentence to be read left to right.

        buttons is a sequence of (label, command) in the order they are to
        appear. The destructive or closing one goes last, at the bottom,
        away from the pointer that has just been in the list.

        Each gets a letter underlined and bound to Alt. The first letter
        where it is free, and the first free letter of the label where it is
        not - which is what Windows does, and what stops the last button in a
        list from being the one that silently has no accelerator. Close
        alongside Compare gets Alt-L rather than nothing.

        The letter is taken from the label as the operator reads it, so an
        interface in Italian has Italian accelerators. That also means two
        windows can disagree about what Alt-C does, which is correct: an
        accelerator belongs to the window it is pressed in.

        window is what the binding is made on, because a Toplevel and not the
        frame is what has the focus - it defaults to the container's own
        window.
        """
        column = ttk.Frame(container, style="App.TFrame")
        target = window
        if target is None:
            target = container.winfo_toplevel()
        taken = set()

        for label, command in buttons:
            underline = self.get_underline(label, taken)
            ttk.Button(column, style="App.TButton", text=label,
                       width=self.BUTTON_WIDTH,
                       underline=underline, command=command).pack(
                           fill=tk.X, padx=5, pady=5)
            if underline >= 0:
                letter = label[underline].lower()
                taken.add(letter)
                # The accelerator swallows the event Tk hands a binding. A
                # button's command is called with nothing, and the two have
                # to be the same call or the keyboard reaches handlers the
                # mouse never does - which is how a form that works when it
                # is clicked raises on Alt-S.
                target.bind("<Alt-{0}>".format(letter),
                            lambda evt, run=command: run())

        return column

    def get_underline(self, label, taken):
        """Which letter of this label to underline, or -1 for none.

        The first that nobody in this window has claimed. Letters only: an
        ellipsis or a digit underlined is an accelerator nobody can guess,
        and a label made entirely of them is a button that goes without -
        which is better than one whose accelerator does somebody else's job.
        """
        for index, character in enumerate(label):
            if character.isalpha() and character.lower() not in taken:
                return index
        return -1

    def set_selected(self, tree, iid):
        """Put the focus back on a row, and scroll it into view.

        Called after a list has been read again, which is the moment the
        selection is lost: the rows are deleted and rebuilt, so the one the
        operator was on stops existing between the two. Without this, saving
        an edit drops them at the top of a list they were half way down, and
        the row they just changed is the one thing they cannot see.

        A row that is no longer there - withdrawn, retired out of the
        listing, or renamed into another place in the order - leaves the
        list as it is rather than guessing at a neighbour. Landing on the
        wrong row is worse than landing on none, because the next thing the
        operator presses acts on it.
        """
        if iid and tree.exists(iid):
            tree.selection_set(iid)
            tree.focus(iid)
            tree.see(iid)
            tree.focus_set()

    # --- dates --------------------------------------------------------------

    def get_date_display(self, value):
        """An ISO date or timestamp as it is read on screen.

        Stored ISO and shown dd-mm-yyyy. The two are not in tension: ISO is
        what sorts, what SQLite compares and what a range query is written
        in, so it is what the database holds; dd-mm-yyyy is what somebody
        reads off a screen or a printed form without translating it first.
        The conversion belongs here, in one place, for the same reason the
        colours do - a date written two ways in two windows is the same
        column looking like two.

        A timestamp keeps its time, to the minute: seconds may be recorded,
        and nobody reads them.

        Anything that is not an ISO date comes back unchanged. A listing
        must not fail over a date, and a value that reaches here in another
        shape is better shown as it is than replaced by a blank nobody can
        account for.
        """
        text = ""
        if value is not None:
            text = str(value).strip()
        day, time = text[:10], text[11:16]

        if len(day) != 10 or day[4] != "-" or day[7] != "-":
            return text
        # Whatever follows the day has to be a separator. Without this a
        # value that merely starts like a date - '2026-09-03x' - would come
        # back turned round with its tail quietly cut off.
        if len(text) > 10 and text[10] not in (" ", "T"):
            return text
        if not (day[:4] + day[5:7] + day[8:]).isdecimal():
            return text

        shown = "{0}-{1}-{2}".format(day[8:], day[5:7], day[:4])
        if len(time) == 5:
            shown = "{0} {1}".format(shown, time)
        return shown

    # --- combo boxes --------------------------------------------------------

    def set_combo(self, combo, captions):
        """Fill a readonly combo box, and say nothing about what is chosen.

        The ids that go with the captions are the caller's to keep, in a
        dictionary of position to key: the box holds captions[i] and the
        caller holds ids[i]. Keyed by position and not by caption, because a
        caption is a business rule - suppliers.name is UNIQUE today, and the
        day two makers of that name in two cities have to be told apart, a
        mapping keyed by it starts losing rows and nothing fails. A primary
        key does not change what it means.

        A dictionary and not a list: an empty combo box answers -1, which a
        dictionary simply does not hold and a list reads as the last row.
        """
        combo.configure(values=list(captions))

    def get_index(self, ids, value):
        """The position that stands for `value`, or -1 when it holds none.

        The way back through the mapping, written once because three
        different widgets need it and a reverse lookup open-coded three times
        is a reverse lookup that will be wrong in one of them.
        """
        for index, held in ids.items():
            if held == value:
                return index
        return -1

    def get_combo_id(self, combo, ids):
        """The id behind the chosen caption, or None when none is chosen.

        current() answers -1 for an empty box, and the mapping has no -1 in
        it, so an empty box comes back as None without anything being asked
        about it. That was a guard when these were lists, where -1 is the
        last row: a valid id, belonging to somebody else.
        """
        return ids.get(combo.current())

    def set_combo_id(self, combo, ids, value):
        """Show the caption that stands for `value`, or nothing at all.

        A value the list does not hold - a supplier withdrawn, an operator
        retired out of the listing - empties the box rather than leaving what
        was in it, which is never nothing: these forms preset the single
        choice, or whoever is at the machine. Left standing, that preset is
        read back as the record's own value and written over it.

        The same rule as set_selected, and for the same reason: showing the
        wrong one is worse than showing none.
        """
        index = self.get_index(ids, value)
        if index >= 0:
            combo.current(index)
        else:
            combo.set("")

    def set_list(self, listbox, captions, enabled=None):
        """Fill a listbox, and say nothing about what is selected.

        The combo boxes' arrangement, applied to a list that stays open: the
        box holds captions[i] and the caller holds ids[i], in a list of its
        own in the same order. Keyed by position and never by caption, for
        the reason set_combo gives - a caption is a business rule, a primary
        key is not.

        A Listbox and not a Treeview wherever a row is one thing with one
        name. The tree brings columns, headings that can be clicked, an
        indentation level and a row of its own machinery for selection; a
        list of names needs none of it, and what it costs is a window that
        looks like a report when it is a list of six words.

        `enabled` is the rows' enable flags, in that same order, and the
        disabled ones are drawn in grey. A Listbox has no tags, so what a
        Treeview says with the 'discarded' tag is said here one item at a
        time - the same colour from the same palette, because the operator is
        being told the same thing: this row is no longer part of what is
        current, not that anything about it was wrong.
        """
        listbox.delete(0, tk.END)
        for index, caption in enumerate(captions):
            listbox.insert(tk.END, caption)
            if enabled is not None and not enabled[index]:
                listbox.itemconfigure(
                    index, foreground=self.get_rgb(*self.DISCARDED))

    def get_list_id(self, listbox, ids):
        """The id behind the selected line, or None when none is selected.

        curselection answers an empty tuple, not -1: a listbox with nothing
        chosen is a real state here, because reading the list again clears
        the selection and the operator may act before choosing again.
        """
        selection = listbox.curselection()
        found = None
        if selection:
            found = ids.get(selection[0])
        return found

    def set_list_id(self, listbox, ids, value):
        """Select the line that stands for `value`, or leave none selected.

        The same rule as set_selected and set_combo_id, and for the same
        reason: a value the list no longer holds - a supplier withdrawn while
        the window stood open - leaves nothing selected rather than the
        neighbouring row. Landing on the wrong row is worse than landing on
        none, because the next button pressed acts on it.

        see() as well as selection_set, or the row is selected somewhere off
        the visible part of a list that has grown.
        """
        listbox.selection_clear(0, tk.END)
        index = self.get_index(ids, value)
        if index >= 0:
            listbox.selection_set(index)
            listbox.activate(index)
            listbox.see(index)

    def set_count(self, variable, count):
        """How many rows the list is showing, in words it can be read in.

        Said once here rather than formatted in every window, so the five
        registers cannot start counting in five different phrasings. The
        number is the length of the register, withdrawn rows included: what
        is on the screen, which is what somebody looking at the screen is
        asking about.

        'Items' and not 'suppliers' or 'people', because neither language
        here has a plural this string could carry: one row and six rows would
        need two translations of a sentence that exists to say a number.
        """
        variable.set(_("Items: {0}").format(count))

    def get_enable_tags(self, enable):
        """The tags of a row by whether it is enabled: grey when not.

        Said once, so that every list asks the question in the same words.
        """
        tags = ()
        if not enable:
            tags = ("discarded",)
        return tags

    def set_tree_tags(self, tree):
        """The row colours, defined once for every list in the application.

        Rows with states of their own are coloured by a subclass that
        extends this and calls it first.
        """
        # The foreground and not the background: a withdrawn row is not a
        # state of what it holds, it is a row no longer in use, and greyed
        # text says that without competing with any other colour.
        tree.tag_configure("discarded",
                           foreground=self.get_rgb(*self.DISCARDED))

    # --- input validation ---------------------------------------------------

    def get_widgets(self, container):
        """Every descendant of a container, depth first.

        Recursive rather than two levels deep, so a field does not escape
        validation merely because someone wrapped it in one more frame.
        """
        found = []
        for child in container.winfo_children():
            found.append(child)
            found.extend(self.get_widgets(child))
        return found

    def get_invalid_field(self, container):
        """First field that fails, as (widget, reason), or None if all pass.

        A field that is not on the form at the moment is skipped - see
        is_out_of_the_form.
        """
        invalid = None
        for widget in self.get_widgets(container):
            if invalid is not None:
                continue
            if not isinstance(widget, (ttk.Entry, tk.Entry)):
                continue
            if self.is_out_of_the_form(widget):
                continue
            value = widget.get().strip()
            if not value:
                invalid = (widget, "empty")
            elif (isinstance(widget, ttk.Combobox)
                  and value not in widget.cget("values")):
                invalid = (widget, "not_in_list")
        return invalid

    def is_out_of_the_form(self, widget):
        """Whether a field is not asked of the operator at the moment.

        DISABLED: a field the form has closed because it does not apply is
        not a field left empty. READONLY is not that: it is how a combo box
        says 'choose, do not type', and it still has to be chosen.

        REMOVED FROM ITS GEOMETRY MANAGER, by grid_remove or pack_forget: a
        field taken off the form. Asked of the manager and not of the screen,
        on purpose: winfo_viewable is false for every field of a window that
        is still withdrawn, and a check that skipped them all would pass a
        form nobody filled in.
        """
        if isinstance(widget, ttk.Widget):
            disabled = widget.instate(("disabled",))
        else:
            disabled = str(widget.cget("state")) == tk.DISABLED

        removed = widget.winfo_manager() == ""
        return disabled or removed

    def get_clean_text(self, value):
        """A typed value with the spaces a person does not see taken out.

        Leading and trailing ones, and any run of them inside collapsed to
        one. A name typed with two spaces passes a UNIQUE constraint as a
        different name from the one with one space, and a register exists to
        stop exactly that.
        """
        if not value:
            return ""
        return " ".join(value.split())

    def on_fields_control(self, container, title):
        """True when every field is filled and every choice is a legal one.

        A real boolean, not zero or None: the caller writes `if not ok`, and
        `0 == False` never has to be true by accident.
        """
        messages = {"empty": _("Please fill in every field."),
                    "not_in_list": _("Choose a value from the list.")}
        invalid = self.get_invalid_field(container)
        is_valid = invalid is None

        if not is_valid:
            widget, reason = invalid
            messagebox.showwarning(title, messages[reason], parent=container)
            widget.focus()

        return is_valid

    def get_validate_integer(self, caller):
        return (caller.register(self.validate_integer),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

    def get_validate_float(self, caller):
        return (caller.register(self.validate_float),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

    #: What a number looks like on the way to being one. These are typed
    #: through, not typed by mistake: a field that refuses them refuses the
    #: first keystroke of every negative number, and of every value written
    #: .5 - which is not validation but a field nobody can type in.
    INCOMPLETE_INTEGER = ("", "-", "+")
    INCOMPLETE_FLOAT = ("", "-", "+", ".", "-.", "+.")

    def validate_integer(self, action, index, value_if_allowed, prior_value,
                         text, validation_type, trigger_type, widget_name):
        """Allow the keystroke only when the field stays a valid integer."""
        allowed = True
        if action == "1" and value_if_allowed not in self.INCOMPLETE_INTEGER:
            try:
                int(value_if_allowed)
            except ValueError:
                allowed = False
        return allowed

    def validate_float(self, action, index, value_if_allowed, prior_value,
                       text, validation_type, trigger_type, widget_name):
        """Allow the keystroke only when the field stays a valid number.

        The comma is read as a decimal point rather than refused. It is the
        key the numeric keypad gives on the keyboards this runs on, and the
        forms already translate it before converting - control.py and
        criteria_set.py both do. Refused here, the obvious key would do
        nothing at all and say nothing about why.
        """
        allowed = True
        candidate = value_if_allowed.replace(",", ".")
        if action == "1" and candidate not in self.INCOMPLETE_FLOAT:
            try:
                float(candidate)
            except ValueError:
                allowed = False
        return allowed

    def get_validate_length(self, caller, length):
        """A validatecommand that keeps a field within `length` characters.

        The length travels as a literal argument after the substitutions, so
        one registered method serves every width:

            entry.configure(
                validate="key",
                validatecommand=engine.get_validate_length(self, 16))

        A field has one validatecommand: one that must be a number and short
        as well needs a validator of its own that does both.
        """
        return (caller.register(self.validate_length),
                "%d", "%P", str(length))

    def validate_length(self, action, value_if_allowed, length):
        """Allow the keystroke only when the field stays within length.

        Checked before the character goes in, like the two above, so what
        would not fit is refused rather than what is there being cut: the
        cursor does not jump, a paste too long is refused whole, and a value
        set from code - a row read back from the database - is never touched,
        because 'key' validation runs on typing and deleting only. Deleting
        is always allowed.
        """
        allowed = True
        if action == "1" and len(value_if_allowed) > int(length):
            allowed = False
        return allowed

    # --- cursor -------------------------------------------------------------

    BUSY_CURSOR = "watch"

    def busy(self, caller):
        """Anything slower than an eyeblink is wrapped in busy/not_busy.

        The cursor is set on the root as well as on the caller. Setting it on
        one widget changes it over that widget alone, which is why an hourglass
        set on a dialog is invisible the moment the pointer is over a button
        inside it - and the pointer is always over a button, because the
        operator has just clicked one.
        """
        for widget in self.get_busy_widgets(caller):
            widget.config(cursor=self.BUSY_CURSOR)
        caller.update()

    def not_busy(self, caller):
        for widget in self.get_busy_widgets(caller):
            widget.config(cursor="")
        caller.update()

    def get_busy_widgets(self, caller):
        """The caller, the root, and everything inside the caller."""
        widgets = [caller, caller.nametowidget(".")]
        widgets.extend(self.get_widgets(caller))
        return widgets


def main():
    foo = Tools()
    root = tk.Tk()
    root.title("Tools")
    foo.set_style("clam")
    foo.center_me(root)
    root.mainloop()


if __name__ == "__main__":
    main()
