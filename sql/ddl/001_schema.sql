-- ----------------------------------------------------------------------------
-- project:  pittacium
-- authors:  Giuseppe Costanzi (1966bc)
-- licence:  GPL-3.0-or-later, see LICENSE
-- ----------------------------------------------------------------------------
-- Schema version 1.
--
-- Written for SQLite 3.21, the laboratory's: no UPSERT, no window
-- functions, no RENAME or DROP COLUMN. Measures are in millimetres; dots
-- belong to the printer and are computed by Layout, never stored.
--
-- What is printed is not kept: there is no table of printed labels.
-- ----------------------------------------------------------------------------

PRAGMA foreign_keys = ON;

BEGIN;

-- The section's name, printed in the band at the bottom of every label, is
-- not here: it belongs to the workstation and lives in pittacium.ini.

-- The barcodes the program can print. code is what the printer-language
-- classes recognise: it is not translated and not edited.
CREATE TABLE symbologies (
    symbology_id    INTEGER PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,
    description     TEXT NOT NULL,
    enable          INTEGER NOT NULL DEFAULT 1 CHECK (enable IN (0, 1))
);

-- The physical label on the roll. section_band_mm is the strip reserved at
-- the bottom for the section's name; the elements fill what is above it.
CREATE TABLE formats (
    format_id       INTEGER PRIMARY KEY,
    description     TEXT NOT NULL UNIQUE,
    width_mm        REAL NOT NULL CHECK (width_mm > 0),
    height_mm       REAL NOT NULL CHECK (height_mm > 0),
    margin_mm       REAL NOT NULL DEFAULT 1.5 CHECK (margin_mm >= 0),
    section_band_mm REAL NOT NULL DEFAULT 4.0 CHECK (section_band_mm > 0),
    enable          INTEGER NOT NULL DEFAULT 1 CHECK (enable IN (0, 1))
);

-- A label saved on purpose, to be printed again: "PBS 1X".
CREATE TABLE templates (
    template_id     INTEGER PRIMARY KEY,
    format_id       INTEGER NOT NULL REFERENCES formats (format_id),
    description     TEXT NOT NULL,
    enable          INTEGER NOT NULL DEFAULT 1 CHECK (enable IN (0, 1))
);

-- The lines of a template, from the top: text or a barcode. A barcode
-- names its symbology; a text line does not.
CREATE TABLE template_elements (
    template_element_id INTEGER PRIMARY KEY,
    template_id     INTEGER NOT NULL REFERENCES templates (template_id),
    symbology_id    INTEGER REFERENCES symbologies (symbology_id),
    position        INTEGER NOT NULL CHECK (position > 0),
    kind            TEXT NOT NULL CHECK (kind IN ('text', 'barcode')),
    content         TEXT NOT NULL DEFAULT '',
    height_mm       REAL NOT NULL CHECK (height_mm > 0),
    align           TEXT NOT NULL DEFAULT 'L' CHECK (align IN ('L', 'C', 'R')),
    module_mm       REAL CHECK (module_mm > 0),
    human_readable  INTEGER NOT NULL DEFAULT 1
                    CHECK (human_readable IN (0, 1)),
    enable          INTEGER NOT NULL DEFAULT 1 CHECK (enable IN (0, 1)),
    CHECK ((kind = 'text' AND symbology_id IS NULL AND module_mm IS NULL)
        OR (kind = 'barcode' AND symbology_id IS NOT NULL
            AND module_mm IS NOT NULL))
);

CREATE INDEX ix_templates_format ON templates (format_id);
CREATE INDEX ix_template_elements_template
    ON template_elements (template_id, position);

PRAGMA user_version = 1;

COMMIT;
