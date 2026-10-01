# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The application: the root window and the engine."""

import tkinter as tk
from tkinter import messagebox

from engine import Engine
from ui.main import Main


class App(tk.Tk):
    """The root window. It owns the engine; every window finds it here."""

    def __init__(self, log):
        super().__init__()

        self.engine = Engine(log)

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.title(self.engine.app_title)
        self.engine.tools.set_style(
            self.engine.config.get("interface", "theme"))
        self.set_icon()

        main = Main(self)
        main.pack(fill=tk.BOTH, expand=1)
        main.on_open()
        self.engine.tools.center_me(self)
        self.engine.log.trace("ready")

    def set_icon(self):
        """The icon, in every size the window manager may ask for.

        The images are kept on the instance: Tk holds them by name and a
        PhotoImage nobody keeps is collected, leaving an empty icon.
        """
        self.icons = [tk.PhotoImage(data=data)
                      for data in self.engine.get_icons()]
        self.iconphoto(True, *self.icons)

    def report_callback_exception(self, exc, val, tb):
        """Tkinter calls this for an exception raised in a callback.

        Every error coming out of the interface ends up here, the one place
        where it is handled: written to the log with its traceback, and
        shown, so nothing fails in silence. Tkinter calls this from inside
        its own except block, which is what log.exception() needs.
        """
        self.engine.log.exception("{0}: {1}".format(exc.__name__, val))
        messagebox.showerror(self.engine.app_title,
                             "{0}\n\n{1}".format(val, self.engine.log.path),
                             parent=self.get_active_window())

    def get_active_window(self):
        """The window on top, to hang a box on.

        A box whose parent is the root window opens behind any dialog that
        is transient of it; asked of the window with the focus, it opens
        over what the user was doing.
        """
        widget = self.focus_displayof()
        window = self
        if widget is not None:
            window = widget.winfo_toplevel()
        return window

    def on_exit(self, evt=None):
        """Close the database and go.

        No question first: leaving loses nothing - a label is printed or it
        is not, and a template is saved when Save is pressed.
        """
        self.engine.db.close_connection()
        self.destroy()
