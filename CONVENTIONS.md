# pittacium — Conventions

How the code of pittacium is written, and why. Read it before writing code;
change it here first when a rule turns out to be wrong, and in the code
afterwards - never the other way round.

Every rule serves clarity, safety and maintainability: the simplest
solution that still reads clearly in two years (KISS), nothing written for
an imagined future (YAGNI), every piece of knowledge written once (DRY).
Two copies start identical, one gets fixed and the other does not.

---

## The rules of this program

- **Only `Zpl` writes printer commands.** No other module contains a ZPL
  string, not even one `^XA`. The day the printer changes make, one class
  changes.
- **Only `Layout` decides where things go.** `Zpl` and `Preview` read the
  same items and add no position, size or proportion of their own. A
  number that places something and lives in a renderer is a second copy,
  and the second copy is the one that drifts.
- **Millimetres in the formats, dots in the layout.** A format never holds
  a value in dots; the conversion happens once, with the printer's
  resolution.
- **Printer settings are data.** No resolution, darkness or queue name is
  a constant in the code: they are in `pittacium.ini`.
- **A failed print is never reported as printed.** `Spooler.send` either
  returns having handed the job over, or raises. The `file` transport says
  on screen and in the log that nothing was printed, every time.
- **What is printed is not kept.** A label is the fair copy of a
  handwritten one and may carry anything, a name included. Its text never
  reaches the database or the log: the log records that a label was
  printed, in which format, how many copies and the outcome - never what
  it said. Only a template, saved on purpose, is stored. The `file`
  transport writes the ZPL to disk and is for testing only.
- **Nothing is deleted.** Rows carry `enable` (0/1) and every read filters
  on it. A template taken away is disabled; saved again, its old lines are
  disabled and the new ones written.

## Target environment

**Write for the oldest interpreter the program runs on.** The laboratory
runs Windows 10 LTSC 2019 with **Python 3.7.0** and **SQLite 3.21.0**;
development happens on Debian 12 with Python 3.11 and SQLite 3.40.

- Not available: the walrus `:=`, `match`, positional-only parameters,
  dict merge with `|`, `functools.cached_property`, `zoneinfo`. If it
  would not have been written in 2018, it is not written.
- Nothing removed after 3.7 either: `sqlite3.OptimizedUnicode` is gone in
  3.12.
- Both operating systems: `os.path.join` always, never a separator by
  hand.
- On Debian, `tkinter` needs the `python3-tk` package; its absence looks
  like a bug in the code.

## Batteries included

The standard library and nothing else: `tkinter`, `sqlite3`, `socket`,
`subprocess`, `unittest`. Laboratory machines have no administrator rights
and often no PyPI, and the program must still start in five years.

A dependency that earns its place is **optional**: imported in `try/except
ImportError` with a flag, and the program degrades cleanly without it.
The only one is `pywin32`, for the `raw` transport on Windows; the `tcp`
transport reaches the same printer without it.

Where a library is not really needed, a small class written by hand does
the job and its docstring names the library it stands in for: `Log`
(`logging`), `Config` (`configparser`), `Events`, `Windows`, and the two
barcode encoders.

## Language

- **English in the code**: identifiers, comments, docstrings, log
  messages, exception text. A log in two languages is a log nobody can
  grep.
- **The interface goes through `_()`** from `i18n.py`. The keys are the
  English strings, Italian is the first translation: a string not yet
  translated shows in English, never as a symbol.
- **The database is not translated**: a symbology code means the same
  thing whoever wrote the row.

## Style

- **PEP 8, 79 columns.** Four spaces, `lower_case_with_underscores` for
  functions and variables, `CapWords` for classes, `UPPER_CASE` for module
  constants. Imports in three blocks - standard library, third party, ours
  - and no `import *`. `is None`, never `== None`.
- **`.format()`**, not f-strings and not `%`. And never any of them to
  build SQL.
- **Object-oriented.** The logic lives in classes, one responsibility
  each, one class per module, named after it. No free functions, except a
  trailing `main()`.
- **Composition before inheritance.** A class *has* its collaborators as
  attributes. Inheritance only where *is a* is true - `App(tk.Tk)`,
  `UI(tk.Toplevel)`. The one exception is `ui.window.Window`, which adds a
  single property and decides nothing about what a window is.
- **Böhm–Jacopini.** Sequence, `if`, loops, assignment. One exit per
  function: no `return` in the middle, no `break` or `continue`. A
  function that needs several exits is doing several things and must be
  split. `raise` is allowed, for real errors only.
- **One sentence per line.** A plain `if`/`else`, never `x if c else y`.
  `self.engine` on every line, never an `engine = self.engine` alias. A
  value that needs working out is worked out on its own line and named
  before the call that uses it.
- **A name is a contract**, readable where it is called:

| prefix | contract |
|---|---|
| `init_*` | builds widgets, called once from the constructor |
| `set_*` | changes state or fills widgets, returns nothing useful |
| `get_*` | returns a value and changes nothing |
| `is_*`, `has_*` | returns a bool, no side effects |
| `check_*` | verifies and **raises** when something is wrong |
| `on_*` | event handler, `def on_x(self, evt=None)` |

- **A constant lives where it is read**, at the top of that module, with
  the comment that says why it is that number.
- **Comments say why**, not what. A docstring says what the thing does
  now; how it came to be belongs in the commit message.
- **Plain text in the source.** No decorative glyphs: `+/-`, `<=`, `->`.
- **Module header**, the same in every file:

```python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
```

  A shebang only on `pittacium.py`, the file that is started.

## The shape of the program

```
pittacium.py     launcher, and nothing else
engine.py        Engine: owns the parts, knows no printer language
dbms.py          DBMS: the connection, the statements
config.py        Config: pittacium.ini, read by hand
log.py           Log: the log, written by hand
events.py        Events: subscribe / unsubscribe / notify
windows.py       Windows: the open windows, one per name
tools.py         Tools: widget factories, styles, validation
layout.py        Layout: where everything goes on a label, in dots
zpl.py           Zpl: the label in ZPL II
spooler.py       Spooler: the job to the printer, raw / tcp / file
printer.py       Printer: language, transport, log
templates.py     Templates: saved labels and their lines
i2of5.py         Interleaved 2 of 5, encoded by hand
code128.py       Code 128, encoded by hand
version.py       the facts about the program, written once
ui/              the windows: they calculate nothing
sql/ddl dml      the schema and the starting data
tests/
```

- **The Engine is composition.** `App(tk.Tk)` creates the one `Engine`,
  which owns its parts as attributes - `log`, `config`, `db`, `printer`,
  `templates`, `tools`, `events`, `windows` - so a call says who does the
  work: `self.engine.templates.save(...)`.
- **A window reaches the engine** through `ui.window.Window`, a property
  returning `self.nametowidget(".").engine`. Never a constructor argument.
- **`tools.py` is shared.** It travels unchanged from one project to the
  next, so it carries helpers this program does not call and comments
  about the projects it came from. It is not trimmed here: a copy
  pruned for one program is a copy that stops being the same. What
  pittacium needs from it is added in a form the others could use.
- **Dependencies point one way.** `layout.py`, `zpl.py` and the encoders
  import no `tkinter`: they can be tested without a window. `ui/` decides
  no position and does not import `sqlite3`.
- **Files written and files read.** What the program writes - the
  settings, the database, the log, the `zpl` folder - lives beside it
  (`Engine.get_file`); what it only reads travels with it
  (`Engine.get_resource`). Built with PyInstaller, the first is beside the
  executable and the second wherever the build unpacked it.

## Errors and the log

- **Errors rise to one net.** `DBMS` catches only `sqlite3.Error`: logs
  the statement, rolls back, raises. `App.report_callback_exception` is
  the net for callbacks - the traceback to the log, the message on
  screen. `main()` wraps the start the same way.
- **No bare `except:`.** No `None` returned in place of data: a failed
  read must not look like "no rows".
- **A transaction is all or nothing.** A template and its lines are saved
  together; a failure halfway - any failure, not only the database's -
  rolls back the whole of it.
- **The log is `Log`**, beside the program: one event per line, rotated by
  size. It is not a record of what was printed, only of what happened.

## Tkinter

- **Widget prefixes**: `lst_`, `cb_`, `txt_`, `lbl_`, `frm_`, `btn_`,
  `ent_`, `chk_`, `spn_`.
- **Buttons come from `Tools.get_button_column`**, which underlines the
  first free letter and binds it to Alt. The closing button goes last.
- **One module per window**, a `UI` class whose Tk name is the module's,
  opened through `engine.windows`.
- **Observer, not reach-through.** Whoever changes something calls
  `events.notify(name, row_id)`; whoever shows it subscribed and reloads.
  Events are declared in `Events.NAMES`; an unknown name raises, so a
  misspelt event fails at once instead of notifying nobody.
- **Built hidden, shown in place**: `tools.hide_me`, then
  `tools.center_me`, or the window appears empty in a corner and jumps.
- **No `__str__` on a widget class.** Tk uses `str(widget)` as its path
  name.
- **The status bar decides no width.** A long message is cut, it does not
  widen the window.
- **A confirmation is for what cannot be taken back, or costs work**, and
  its default is No: deleting a template, replacing one, removing a line
  that has text. Not for Print: the preview is the question. Nobody is
  told about a decision they just made.
- **Words a colleague at the bench understands.** "The printer is not set
  up", not "transport file".

## SQLite

- **`sqlite3.Row`**, columns by name: `row["code"]` survives a new
  column, `row[2]` does not.
- **`?`, always.** The one exception is `PRAGMA user_version`, which takes
  no placeholder.
- **INSERT and UPDATE are built from the schema** by `get_insert` and
  `get_update`, from values keyed by column name; a missing or unknown
  column is refused, naming the table.
- **`PRAGMA foreign_keys = ON`** on every connection.
- **Names**: tables plural, primary key `<singular>_id`, keywords upper
  case, everything else lower case, units in the column name: `height_mm`.
- **Design for SQLite 3.21**: no `ON CONFLICT DO UPDATE`, no `RENAME
  COLUMN`, no `DROP COLUMN`, no window functions, no `RETURNING`.
- **The schema version is `PRAGMA user_version`**, checked at every start.
  Once a database is in service its schema is changed only by a numbered
  migration, with a copy of the file taken first.
- The repository carries the schema and the starting data as `.sql`,
  never a populated `.sl3`.

## Tests

- **`unittest`**, not pytest. A database in a temporary folder; a
  `MemoryLog` in place of the log.
- **Green before every commit.** A failing test is never commented out.
- **One test per behaviour**, named after what it expects:
  `test_a_failed_send_is_a_warning_and_raises`.
- **Negative cases count**: a barcode refused, a setting refused, a
  failure halfway leaving nothing behind, a name that must not reach the
  log.
- **No real data in tests**, and no names that could be a person's except
  where a test proves they are not kept.

## Versions and the repository

- `version.py` holds `__version__`, semantic, and `__date__`, the release
  as a Latin season and a Roman year: `autumnus MMXXVI`.
- Commits in English, one purpose each, files staged by name.
- Nothing of one laboratory in the repository: queue names, addresses and
  paths live in `pittacium.ini`, which is not versioned.
- Licence GPL-3.0-or-later.

## When to break a rule

A rule is right in the normal case, not in every case. A departure is
allowed on three conditions: you know which rule you are breaking; the
reason is written at that exact line; it stays local.

Never broken: placeholders in SQL, nothing of a printed label kept, no
failure hidden from the operator.
