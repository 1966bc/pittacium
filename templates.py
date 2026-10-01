# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The templates: labels saved on purpose, the same for the whole section.

A template is a row in templates and its lines in template_elements, saved
together or not at all. Nothing is deleted: a template taken away is
disabled, and a template saved again over an old one disables the old
lines and writes the new ones, so what was there can still be read.

The lines come out as the elements Layout reads, and go in the same way.
"""


class Templates:
    """Reading and writing templates, with their lines."""

    def __init__(self, db, log):
        self.db = db
        self.log = log

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    def get_all(self):
        """The templates in use, by description."""
        sql = """SELECT template_id, format_id, description
                   FROM templates
                  WHERE enable = 1
                  ORDER BY description"""
        return self.db.read_all(sql)

    def get_id(self, description):
        """The template in use with this description, or None."""
        sql = """SELECT template_id
                   FROM templates
                  WHERE description = ? AND enable = 1"""
        row = self.db.read_one(sql, (description,))
        template_id = None
        if row is not None:
            template_id = row["template_id"]
        return template_id

    def get_elements(self, template_id):
        """The lines of a template, from the top, as Layout reads them."""
        sql = """SELECT e.kind, e.content, e.height_mm, e.align,
                        e.human_readable, s.code AS symbology
                   FROM template_elements AS e
                   LEFT JOIN symbologies AS s
                          ON s.symbology_id = e.symbology_id
                  WHERE e.template_id = ? AND e.enable = 1
                  ORDER BY e.position"""
        elements = []
        for row in self.db.read_all(sql, (template_id,)):
            element = {"kind": row["kind"], "content": row["content"],
                       "height_mm": row["height_mm"], "align": row["align"]}
            if row["kind"] == "barcode":
                element["symbology"] = row["symbology"]
                element["human_readable"] = bool(row["human_readable"])
            elements.append(element)
        return elements

    def get_symbology_id(self, code):
        """The row of a symbology, refusing one the database does not have."""
        sql = "SELECT symbology_id FROM symbologies WHERE code = ?"
        row = self.db.read_one(sql, (code,))
        if row is None:
            raise ValueError("no symbology {0}".format(code))
        return row["symbology_id"]

    def get_element_values(self, template_id, position, element):
        """One line as the row template_elements stores."""
        symbology_id = None
        human_readable = 1
        if element["kind"] == "barcode":
            symbology_id = self.get_symbology_id(element["symbology"])
            human_readable = int(element["human_readable"])
        return {"template_id": template_id, "symbology_id": symbology_id,
                "position": position, "kind": element["kind"],
                "content": element["content"],
                "height_mm": element["height_mm"],
                "align": element["align"], "human_readable": human_readable,
                "enable": 1}

    def save(self, description, format_id, elements):
        """Save the lines under a description, new or already there.

        One transaction: the template - inserted, or its old lines
        disabled - and every line, or nothing at all. Empty lines are not
        saved: a template is what is printed.
        """
        description = description.strip()
        if description == "":
            raise ValueError("a template needs a description")
        lines = [element for element in elements
                 if element["content"].strip() != ""]
        if not lines:
            raise ValueError("a template needs at least one line")

        template_id = self.get_id(description)
        cursor = self.db.get_cursor()
        try:
            if template_id is None:
                sql, args = self.db.get_insert(
                    "templates", {"format_id": format_id,
                                  "description": description, "enable": 1})
                cursor.execute(sql, args)
                template_id = cursor.lastrowid
            else:
                cursor.execute("""UPDATE template_elements
                                     SET enable = 0
                                   WHERE template_id = ?""", (template_id,))
            for position, element in enumerate(lines, start=1):
                values = self.get_element_values(template_id, position,
                                                 element)
                sql, args = self.db.get_insert("template_elements", values)
                cursor.execute(sql, args)
            self.db.commit()
        except Exception:
            # Any failure halfway, not only the database's: a line refused
            # by get_element_values must not leave the template behind it.
            self.db.rollback()
            self.log.exception("template not saved")
            raise
        finally:
            cursor.close()

        self.log.info("template saved: id {0}, {1} lines".format(
            template_id, len(lines)))
        return template_id

    def disable(self, template_id):
        """Take a template out of use; its rows stay."""
        self.db.write("UPDATE templates SET enable = 0 WHERE template_id = ?",
                      (template_id,))
        self.log.info("template disabled: id {0}".format(template_id))
