# -*- mode: python ; coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""PyInstaller recipe. The build lives in a file, not in a command line.

Run it on the laboratory PC, the machine whose build counts:

    py -3.7 -m PyInstaller --clean --noconfirm pittacium.spec

One directory and not one file. A --onefile build unpacks itself into a
temporary folder at every launch, and on a machine with an antivirus each
launch is a fresh set of files to be scanned. A directory starts at once
and can be looked inside.

What the program writes - pittacium.ini, pittacium.sl3, pittacium.log, the
zpl folder - it writes beside the executable (Engine.get_file). What it
only reads travels inside the build and is found through sys._MEIPASS
(Engine.get_resource): beside the executable with PyInstaller 5, in
_internal with 6.

No database is bundled, and no settings either. The first start makes
pittacium.ini from the example and the database from the SQL, so a fresh
build is a fresh installation: the templates of a section stay with that
section's copy. That is also why nothing but a fresh build may live in
dist/: --clean --noconfirm deletes and rewrites it, and the templates and
settings of an installation left there would go with it. An installation
is made by copying dist/pittacium somewhere else.

pywin32 has to be installed where the build is made: the raw transport
imports win32print, and PyInstaller takes it from there.
"""

import os

# What has to be there at run time, and is only read.
DATAS = [# The settings every new installation starts from.
         ("pittacium.ini.example", "."),
         # The icon, as the lines of base64 the windows read.
         ("app", "."),
         # The schema and the starting data: the database is made from
         # them at the first start, and can be made again from the folder.
         ("sql/ddl/*.sql", "sql/ddl"),
         ("sql/dml/*.sql", "sql/dml"),
         # Read by the Licence window: a copy that names the GPL and hides
         # its text hands over half of what it promises.
         ("LICENSE", ".")]

# What is on the build machine because something else needed it. pittacium
# uses the standard library and pywin32, nothing more.
EXCLUDES = ["PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
            "matplotlib", "numpy", "pandas", "scipy", "sympy", "PIL",
            "IPython", "jupyter", "notebook", "nbconvert",
            "pytest", "sphinx", "tkinter.test", "test",
            "lib2to3", "pydoc_data"]


analysis = Analysis(
    ["pittacium.py"],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=DATAS,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False)

pyz = PYZ(analysis.pure, analysis.zipped_data)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="pittacium",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX compression is what an antivirus looks at twice
    console=False,      # a failure to start is shown in a dialog, not a shell
    icon="pittacium.ico")

collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    name="pittacium")
