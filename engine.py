# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The one object every window reaches: it owns the parts, it is none of them.

Composition: each part is an attribute and a call says who does the work -
engine.db.read_all(...), engine.tools.center_me(...) - and each part can be
built and tested on its own.

What is here is what belongs to nobody else: where the files are, and the
first start of a new installation, which makes its own settings and its
own database so that a colleague can start the program and print.
"""

import glob
import os
import shutil

import i18n
from config import Config
from dbms import DBMS
from events import Events
from layout import Layout
from printer import Printer
from tools import Tools
from version import APP_NAME
from version import SCHEMA_VERSION
from windows import Windows

#: The settings of this workstation, and the template they start from. The
#: first is not in the repository: it names this laboratory's printer.
SETTINGS = "pittacium.ini"
SETTINGS_EXAMPLE = "pittacium.ini.example"

#: What the band at the bottom of a label reads until the workstation says
#: which section it belongs to.
DEFAULT_SECTION = "Lab"


class Engine:
    """The parts of the application, and what belongs to none of them."""

    def __init__(self, log):
        self.log = log
        # The settings of this workstation, made from the example the
        # first time the program starts.
        self.config = Config(self.get_settings())
        i18n.set_language(self.config.get("interface", "language"))
        # The database: made from sql/ the first time, then checked.
        self.db = DBMS(self.get_database(), log)
        self.set_database()
        # Styles and widget helpers.
        self.tools = Tools()
        # The label printer of this workstation, from the settings.
        self.printer = self.get_printer()
        # Who changed what, told to the windows that show it: the Observer.
        self.events = Events(log)
        # The open windows, one per name: the Singleton pattern, by name.
        self.windows = Windows(log)

        self.app_title = APP_NAME

    def __str__(self):
        return ("class: {0}\nparts: log, config, db, printer, tools, events, "
                "windows").format(self.__class__.__name__)

    # --- the files ----------------------------------------------------------

    def get_file(self, name):
        """The full path of a file beside the program.

        So the settings, the database and the log are found wherever the
        program is started from.
        """
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

    def get_settings(self):
        """The settings file, copied from the example when there is none.

        The example is in the repository and the copy is not: the copy is
        where a laboratory writes its own printer queue and section.
        """
        path = self.get_file(SETTINGS)

        if not os.path.exists(path):
            shutil.copyfile(self.get_file(SETTINGS_EXAMPLE), path)
            self.log.info("settings created from {0}".format(
                SETTINGS_EXAMPLE))

        return path

    def get_database(self):
        """The database file, from the settings.

        A bare name is taken beside the program; an absolute path is taken
        as it is, for a file kept somewhere else - a shared folder, so that
        a whole laboratory prints from the same templates.
        """
        written = self.config.get("database", "file")

        path = written
        if not os.path.isabs(written):
            path = self.get_file(written)

        return path

    def get_scripts(self):
        """The SQL that makes a new database: structure, then data."""
        scripts = []
        for folder in ("ddl", "dml"):
            pattern = os.path.join(self.get_file("sql"), folder, "*.sql")
            scripts.extend(sorted(glob.glob(pattern)))
        return scripts

    def set_database(self):
        """Make the database if there is none, open it, and check it.

        A file of another schema version is refused here, at the start,
        rather than failing on the first query that finds a column missing.
        """
        if not os.path.exists(self.db.database):
            self.db.create(self.get_scripts())

        self.db.set_connection()
        self.db.check_schema_version(SCHEMA_VERSION)
        self.db.check_integrity()

    def get_icons(self):
        """Every size of the application icon: one base64 PNG per line."""
        with open(self.get_file("app"), "r") as f:
            return f.read().split()

    def get_license(self):
        """The licence, as the About window shows it."""
        with open(self.get_file("LICENSE"), "r", encoding="utf-8") as f:
            return f.read()

    # --- the label ----------------------------------------------------------

    def get_printer(self):
        """The printer as the settings describe it now."""
        return Printer(self.config, self.get_file(""), self.log)

    def set_settings(self, values):
        """Write the settings, and take them into use - or none of them.

        values maps (section, key) to text. They are written, then a
        printer is built from them; if it refuses one, every value written
        goes back to what it was, and the refusal is raised. A settings
        file half changed would be a printer nobody configured.
        """
        old = {}
        for section, key in values:
            old[(section, key)] = self.config.get(section, key)
            self.config.set(section, key, values[(section, key)])
        try:
            printer = self.get_printer()
        except Exception:
            for section, key in old:
                self.config.set(section, key, old[(section, key)])
            raise
        self.printer = printer
        self.log.info("settings saved")
        self.events.notify("settings")

    def print_test(self):
        """A test label on the first format, with the printer's settings.

        It says what it was printed with, so the label in the hand can be
        read against the settings window.
        """
        label_format = self.get_formats()[0]
        layout = self.get_layout(label_format)
        printer = self.printer
        lines = ((APP_NAME, 5.0),
                 ("Test", 3.5),
                 ("{0} dpi  {1}  {2}".format(printer.dpi, printer.media,
                                             printer.tracking), 3.0))
        elements = []
        for text, height in lines:
            elements.append({"kind": "text", "content": text,
                             "height_mm": height, "align": "C"})
        items = layout.get_items(elements, self.get_section())
        return printer.print_label(layout, items, 1,
                                   label_format["description"])

    def get_formats(self):
        """The label formats in use, by description."""
        sql = """SELECT *
                   FROM formats
                  WHERE enable = 1
                  ORDER BY description"""
        return self.db.read_all(sql)

    def get_layout(self, label_format):
        """The Layout of a format row at this printer's resolution."""
        return Layout(label_format["width_mm"], label_format["height_mm"],
                      label_format["margin_mm"],
                      label_format["section_band_mm"], self.printer.dpi)

    def get_section(self):
        """The name printed at the bottom of every label.

        Set once per workstation in the settings; "Lab" until it is.
        """
        section = self.config.get("label", "section")

        if section == "":
            section = DEFAULT_SECTION

        return section
