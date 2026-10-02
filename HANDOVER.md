# pittacium — Handover

Where this working copy stands and what is still to be established at
the laboratory. A note with a date on it, 2 October 2026: overwrite it
as things change, and delete it when it is spent.

## Where it stands

84 unittest tests green on the laboratory's Windows 10 LTSC 2019, Python
3.7.0 and SQLite 3.21.0. Built with PyInstaller 5.13.2; a copy of the
build makes its settings, database and log at its first start, and
migrates a version 1 database after copying it.

Printed with the `raw` transport, over USB, on:

- a Zebra GX430t, 300 dpi, thermal transfer: the test label and labels
  with text and barcodes, on 50 x 30;
- a Zebra ZD421, in another section, from a copy of the build.

Steps 1, 2, 3 and 6 below are done; 4 and 5 are still to be checked on
paper, and so is the 40 x 10 (see Still open).

Settled and not to be reopened without a reason:

- Two rolls: 50 x 30 mm, and 40 x 10 mm for microbiology tubes, which
  can share a printer. The format is chosen in the main window when the
  roll is changed.
- One installation per section: its own folder, settings, database and
  templates.
- The section band reads "Lab" until `[label] section` is set. The
  40 x 10 has no band: it is too low for one.
- A Code 128 has its text above the bars; a 2 of 5 has its digits under
  them.
- The preview is always visible: Print prints at once, no question.
- Nothing printed is kept; only templates saved on purpose are stored.
- The interface is translated through `_()`; Italian is the default.

## At the laboratory, in this order

Commands are for PowerShell on Windows.

**1. Run it from source.**

```
git clone https://github.com/1966bc/pittacium.git
cd pittacium
py -3.7 -m unittest discover -s tests -v
py -3.7 pittacium.py
```

The tests first: this is the first time on Python 3.7 and SQLite 3.21,
and whatever is newer than 2018 in the code shows up here. Then Help >
About must say Python 3.7.x and SQLite 3.21.0.

**2. Find the printer.**

File > Settings > Print queues lists the queues Windows knows. Look also
at how the Zebra is connected - a `USB001` port or a TCP/IP port with an
address. It decides the transport now, and whether a web version is
possible later.

If it has an address, check that the printer answers on its raw port
before blaming the program:

```
Test-NetConnection -ComputerName <printer address> -Port 9100
```

`TcpTestSucceeded : True` means a job sent there arrives. 9100 is the
Zebra default; the printer's own configuration label (hold the feed
button) says which port it really listens on. A different one goes in
Settings > Port (tcp). Try it from the PC first, and later from the
hospital's internal web server: whether that server reaches the printer
is what a web version depends on.

**3. Set the transport and print the test label.**

- `raw`: the queue name exactly as listed. Needs pywin32:
  `py -3.7 -m pip install pywin32` if the import fails.
- `tcp`: the printer's address, port 9100. Needs nothing.

Save, then Test label: it must print "pittacium / Test / 300 dpi T Y"
with the section at the bottom. If nothing comes out, the log
(`pittacium.log`) has the transport, the queue and the error.

**4. Compare the label with the preview.**

The preview draws the text with a narrow screen font; the printer uses
its own font 0 (`^A0N,h,h`). Check, on a label with a long line:

- does a line the preview shows fitting also fit on paper?
- is the text height on paper the height in mm that was set?
- are the margins and the section band where the preview puts them?

A systematic difference is corrected in `Layout`, once.

**5. Scan the barcodes.**

One label with Interleaved 2 of 5 (e.g. `0042`), one with Code 128 (e.g.
`LOT-2026-0042`), both at 8 mm, read with the laboratory's scanner. Try a
long Code 128 too, where Layout chooses thinner bars.

**6. Build it.**

```
py -3.7 -m PyInstaller --clean --noconfirm pittacium.spec
```

PyInstaller 5.13.2 is the last that supports Python 3.7. Copy
`dist\pittacium` to another folder before running it: the next build
rewrites `dist\`. The first start of the copy must create `pittacium.ini`,
`pittacium.sl3` and `pittacium.log` beside `pittacium.exe`.

## Still open

- **The 40 x 10 on paper.** Schema version 2 adds it; the first start of
  a version 1 database migrates it, after a copy beside it
  (`pittacium.sl3.v1.<date>.bak`). Not yet printed: check that the
  printer finds the gap after the roll is changed (calibrate if not), and
  that microbiology's scanner reads bars 4.5 mm high.
- **A Zebra GK420d** still to be tried: ZPL, 203 dpi, direct thermal
  (media D). Watch accented letters on an old firmware, and Code 128
  longer than about 13 characters, which 203 dpi refuses on 50 mm.
- **The Datamax E-4206P** of another bench speaks DPL, and its settings
  cannot be changed: it needs a `Dpl` class. Put aside for now.
- **Minimum line height.** 2 mm now, which allows 7 lines on 50 x 30.
  Decide on paper whether 2 mm is readable at the bench; 2.5 mm allows 6.
- **Which symbology the laboratory's tube labels use**, if a colleague
  wants to reproduce one.
- **Other printer models** colleagues have: their make and language
  (ZPL, TSPL, EPL) before any of them is supported.

## Ideas for later, not started

- Variables in templates: `{today}` for the date, a field to fill in.
- Print on scan: read a barcode, print its label.
- A calibrate command for when the roll is changed (`~JC`).
- A web version on the hospital's internal server, only if the printers
  are on the network.
