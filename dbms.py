# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""SQLite access.

No silent failures: a database error is logged and raised again. It never
becomes an empty result, because an empty result reads as "there is no
data", and that is a different statement from "the query failed".

Rows are sqlite3.Row, read by name. Only what pittacium uses today is
here: a migration takes a copy of the file before it runs, and restoring
it is copying it back by hand. Dump comes the day something needs it.
"""

import datetime
import os
import re
import shutil
import sqlite3


class DBMS:
    """Connection and statement helpers for the application database."""

    #: What a UNIQUE or a CHECK refusing a row raises, reachable as
    #: self.engine.db.IntegrityError so that no window imports sqlite3.
    IntegrityError = sqlite3.IntegrityError

    #: What a table or column may be called. A name cannot be a bound
    #: parameter - it is interpolated into the statement - so the only place
    #: it can be checked is before that happens.
    IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, database, log):
        self.database = database
        self.log = log
        self.con = None

    def __str__(self):
        return "class: {0}\ndatabase: {1}".format(self.__class__.__name__,
                                                  self.database)

    # --- the file -----------------------------------------------------------

    def create(self, scripts):
        """Make a new database file from the SQL scripts, in order.

        Refused on a file that exists: creating over a database in service
        would be the one operation in this program that loses templates.
        """
        if os.path.exists(self.database):
            raise IOError("database already exists: {0}".format(
                self.database))

        self.run_scripts(scripts)
        self.log.info("database created: {0}".format(self.database))

    def run_scripts(self, scripts):
        """Run SQL scripts in order, on a connection of their own.

        Each script carries its own BEGIN and COMMIT, and its own PRAGMAs:
        a migration turns foreign keys off while it rebuilds a table, which
        SQLite allows only outside a transaction - so not on self.con. A
        script that fails leaves its transaction open, and closing the
        connection rolls it back.
        """
        con = sqlite3.connect(self.database)
        try:
            for path in scripts:
                with open(path, "r", encoding="utf-8") as f:
                    con.executescript(f.read())
        finally:
            con.close()

    def migrate(self, scripts):
        """Bring the database to a newer schema, after copying the file.

        The copy is taken with the connection closed, beside the database,
        named after the version it holds and the moment it was taken: if a
        migration goes wrong, putting the copy back is the way home.
        """
        found = self.get_schema_version()
        self.close_connection()
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = "{0}.v{1}.{2}.bak".format(self.database, found, stamp)
        shutil.copyfile(self.database, backup)
        self.log.info("database copied to {0}".format(backup))

        self.run_scripts(scripts)
        self.set_connection()
        self.log.info("database migrated from schema version {0} to "
                      "{1}".format(found, self.get_schema_version()))

    def set_connection(self):
        """Open the database and switch on what SQLite leaves off.

        Foreign keys are disabled by default in SQLite: without the pragma
        the references declared in the schema are decoration.
        """
        if not os.path.exists(self.database):
            raise IOError("database not found: {0}".format(self.database))

        self.con = sqlite3.connect(self.database,
                                   isolation_level="IMMEDIATE")
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.log.trace("connected to {0}".format(self.database))

    def close_connection(self):
        if self.con is not None:
            self.con.close()
            self.con = None
            self.log.trace("connection closed")

    def get_schema_version(self):
        """The schema version written in the file, PRAGMA user_version."""
        return self.read_one("PRAGMA user_version")[0]

    def check_schema_version(self, expected):
        """Refuse a database of another version than the program's."""
        found = self.get_schema_version()
        if found != expected:
            raise ValueError(
                "{0} is schema version {1}, this program reads {2}".format(
                    self.database, found, expected))

    def check_integrity(self):
        """Verify the file and the references, and raise on either.

        integrity_check says whether the file itself is sound - the answer
        to a power cut. foreign_key_check says whether the rows still point
        at rows that exist. A database can pass the first and fail the
        second.
        """
        rows = self.read_all("PRAGMA integrity_check")
        answer = "no answer"
        if rows:
            answer = rows[0][0]
        if answer != "ok":
            raise sqlite3.DatabaseError(
                "integrity check failed on {0}: {1}".format(
                    self.database, "; ".join(row[0] for row in rows)))

        orphans = self.read_all("PRAGMA foreign_key_check")
        if orphans:
            raise sqlite3.IntegrityError(
                "{0} rows point at rows that no longer exist, first in "
                "{1}".format(len(orphans), orphans[0][0]))

    # --- reading and writing ------------------------------------------------

    def read_one(self, sql, args=()):
        """A single row, or None when the query selects nothing."""
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
            row = cur.fetchone()
        except sqlite3.Error:
            self.log.exception("read_one failed: {0}".format(sql))
            raise
        finally:
            cur.close()
        return row

    def read_all(self, sql, args=()):
        """Every row. An empty list means the query selected nothing."""
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
            rows = cur.fetchall()
        except sqlite3.Error:
            self.log.exception("read_all failed: {0}".format(sql))
            raise
        finally:
            cur.close()
        return rows

    def check_connection(self):
        """Refuse to write when the connection is not one that can be used.

        A SELECT 1 is the cheapest question a connection can be asked, and
        the only one that proves the answer rather than inferring it from
        an attribute still being set.
        """
        if self.con is None:
            raise IOError("no database connection")

        try:
            self.con.execute("SELECT 1").fetchone()
        except sqlite3.Error as exc:
            raise IOError("the connection to {0} is not usable: {1}".format(
                self.database, exc))

    def check_args(self, sql, args):
        """As many values as placeholders, said with the statement.

        What SQLite says otherwise - 'Incorrect number of bindings
        supplied' - names neither the table nor the window it came from.
        """
        if len(args) != sql.count("?"):
            raise ValueError("{0} values for {1} placeholders: {2}".format(
                len(args), sql.count("?"), sql))

    def write(self, sql, args=()):
        """Run one statement in a transaction and return the new row id."""
        self.check_args(sql, args)
        self.check_connection()
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
            self.con.commit()
            row_id = cur.lastrowid
        except sqlite3.Error:
            self.con.rollback()
            self.log.exception("write failed: {0}".format(sql))
            raise
        finally:
            cur.close()
        return row_id

    def write_many(self, statements):
        """Run several statements as one transaction: all of them, or none.

        statements is a sequence of (sql, args) pairs: a template and its
        elements are saved together or not at all. Every pair is counted
        against its placeholders before any of them runs.
        """
        for sql, args in statements:
            self.check_args(sql, args)

        self.check_connection()
        cur = self.con.cursor()
        try:
            for sql, args in statements:
                cur.execute(sql, args)
            self.con.commit()
            count = len(statements)
        except sqlite3.Error:
            self.con.rollback()
            self.log.exception("write_many rolled back after {0} "
                               "statements".format(len(statements)))
            raise
        finally:
            cur.close()
        return count

    def get_cursor(self):
        """A cursor for a unit of work made of dependent statements.

        write_many covers statements that are independent. A template is
        not that case: its lines need the id the template's insert made.
        The caller drives the cursor and ends the transaction with
        commit() or rollback() - all of it, or none of it.
        """
        self.check_connection()
        return self.con.cursor()

    def commit(self):
        self.con.commit()

    def rollback(self):
        self.con.rollback()

    # --- statements built from the schema -----------------------------------

    def check_identifier(self, name, kind="table"):
        """Refuse a name that cannot be interpolated safely."""
        if not self.IDENTIFIER.match(name or ""):
            raise ValueError("not a {0} name: {1!r}".format(kind, name))

    def get_table_info(self, table):
        """What the table is made of: (name, is primary key) per column."""
        self.check_identifier(table)
        rows = self.read_all("PRAGMA table_info({0})".format(table))

        if not rows:
            raise ValueError("no table {0}".format(table))
        return [(row["name"], bool(row["pk"])) for row in rows]

    def get_primary_key(self, table):
        """The key column, asked of the table rather than of the caller."""
        keys = [name for name, is_key in self.get_table_info(table)
                if is_key]

        if len(keys) != 1:
            raise ValueError(
                "{0} has {1} primary key columns, not one: {2}".format(
                    table, len(keys), ", ".join(keys) or "none"))
        return keys[0]

    def get_fields(self, table):
        """Column names of a table, primary key excluded.

        Excluded by being the key and not by being first: names[1:] is
        true until the day a table is written differently.
        """
        return tuple(name for name, is_key in self.get_table_info(table)
                     if not is_key)

    def get_insert_sql(self, table):
        """An INSERT from the schema, so field order comes from one place."""
        fields = self.get_fields(table)
        return "INSERT INTO {0} ({1}) VALUES ({2})".format(
            table, ", ".join(fields), ", ".join("?" * len(fields)))

    def get_update_sql(self, table, primary_key):
        """An UPDATE from the schema, every column but the key."""
        self.check_identifier(primary_key, "column")
        fields = self.get_fields(table)
        return "UPDATE {0} SET {1} = ? WHERE {2} = ?".format(
            table, " = ?, ".join(fields), primary_key)

    def get_insert(self, table, values):
        """An INSERT and its arguments, with the values given by name.

        The caller hands over a dictionary keyed by column name and the
        ordering is done here, once, against the schema. A missing column
        and an unknown one are both refused, naming the table.
        """
        return (self.get_insert_sql(table), self.get_args(table, values))

    def get_update(self, table, key_value, values):
        """An UPDATE and its arguments, the same way, with the key last."""
        args = self.get_args(table, values)
        args.append(key_value)
        return (self.get_update_sql(table, self.get_primary_key(table)),
                args)

    def get_args(self, table, values):
        """The values of a row as a list, in the order the schema declares."""
        fields = self.get_fields(table)
        self.check_values(table, fields, values)

        args = []
        for name in fields:
            args.append(values[name])
        return args

    def check_values(self, table, fields, values):
        """Every column named once, and nothing named that is not a column."""
        missing = [name for name in fields if name not in values]
        unknown = [name for name in values if name not in fields]

        if missing or unknown:
            parts = []
            if missing:
                parts.append("missing {0}".format(", ".join(missing)))
            if unknown:
                parts.append("not a column: {0}".format(", ".join(unknown)))
            raise ValueError("{0}: {1}".format(table, "; ".join(parts)))

    def get_selected(self, table, field, value):
        """One row as a dictionary keyed by column name, or None."""
        self.check_identifier(table)
        self.check_identifier(field, "column")
        sql = "SELECT * FROM {0} WHERE {1} = ?".format(table, field)
        row = self.read_one(sql, (value,))

        selected = None
        if row is not None:
            selected = dict(row)
        return selected
