-- ----------------------------------------------------------------------------
-- project:  pittacium
-- authors:  Giuseppe Costanzi (1966bc)
-- licence:  GPL-3.0-or-later, see LICENSE
-- ----------------------------------------------------------------------------
-- Schema version 1 to 2.
--
-- A label too low to carry the section's band: section_band_mm may now be
-- 0, which means no band at all. The 40 x 10 roll of microbiology is the
-- first such format: one line, a text or a barcode with its text above.
--
-- SQLite 3.21 cannot change a CHECK in place, so formats is rebuilt the
-- way the SQLite documentation describes: a new table, the rows copied, the
-- old table dropped, the new one renamed. Foreign keys are off while it
-- happens, or dropping formats would be refused for the templates that
-- point at it; they point at it again, by name, once the rename is done.
-- ----------------------------------------------------------------------------

PRAGMA foreign_keys = OFF;

BEGIN;

CREATE TABLE formats_new (
    format_id       INTEGER PRIMARY KEY,
    description     TEXT NOT NULL UNIQUE,
    width_mm        REAL NOT NULL CHECK (width_mm > 0),
    height_mm       REAL NOT NULL CHECK (height_mm > 0),
    margin_mm       REAL NOT NULL DEFAULT 1.5 CHECK (margin_mm >= 0),
    section_band_mm REAL NOT NULL DEFAULT 4.0 CHECK (section_band_mm >= 0),
    enable          INTEGER NOT NULL DEFAULT 1 CHECK (enable IN (0, 1))
);

INSERT INTO formats_new (format_id, description, width_mm, height_mm,
                         margin_mm, section_band_mm, enable)
    SELECT format_id, description, width_mm, height_mm,
           margin_mm, section_band_mm, enable
      FROM formats;

DROP TABLE formats;

ALTER TABLE formats_new RENAME TO formats;

-- The microbiology roll: 40 x 10 mm, no band.
INSERT INTO formats (description, width_mm, height_mm, margin_mm,
                     section_band_mm)
    VALUES ('40 x 10', 40, 10, 1.0, 0);

PRAGMA user_version = 2;

COMMIT;

PRAGMA foreign_keys = ON;
