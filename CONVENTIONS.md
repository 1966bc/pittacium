# pittacium — Conventions

The general rules are in `fundamenta/python.md`: style, the shape of the
application, errors, Tkinter, SQLite, tests. They are not repeated here.
This file holds only what is particular to pittacium, and where it departs
from the general rules it says so.

## Rules

- **Only `Zpl` writes printer commands.** No other module contains a ZPL
  string, not even one `^XA`. The day the printer changes make, one class
  changes.
- **Only `Layout` decides where things go.** `Zpl` and `Preview` read the
  same `Layout` and add no position, size or proportion of their own. A
  number that places something on the label and lives in a renderer is a
  second copy, and the second copy is the one that drifts.
- **Millimetres in the formats, dots in the layout.** A format never holds
  a value in dots; the conversion happens once, with the printer's
  resolution.
- **Printer settings are data.** No resolution, darkness or queue name is
  a constant in the code.
- **A failed print is never reported as printed.** `Spooler.send` either
  returns having handed the job over, or raises. The `file` transport says
  on screen and in the log that nothing was printed, every time.
- **What is printed is not kept.** A label is the fair copy of a
  handwritten one and may carry anything, a name included. Its text never
  reaches the database or the log: the log records that a label was
  printed, in which format, how many copies and the outcome — never what
  it said. Only a template, saved on purpose, is stored. The `file`
  transport writes the ZPL to disk and is for testing only.

## Target

Windows 10 LTSC 2019 with Python 3.7.0 and SQLite 3.21.0: see
`fundamenta/python.md`, *Target environment*.

## Language

The interface goes through `_()` from `i18n.py`, as in CDTrack: the keys
are the English strings, Italian is the first translation. The repository
is public and the program may be useful elsewhere.
