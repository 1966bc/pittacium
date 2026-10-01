-- -----------------------------------------------------------------------------
-- project:  pittacium
-- authors:  Giuseppe Costanzi (1966bc)
-- licence:  GPL-3.0-or-later, see LICENSE
-- -----------------------------------------------------------------------------
-- Starting data. Symbologies are only those the program can print today:
-- a row is added when its class is, not before.
-- -----------------------------------------------------------------------------

BEGIN;

INSERT INTO symbologies (code, description) VALUES
    ('I2OF5', 'Interleaved 2 of 5'),
    ('CODE128', 'Code 128');

-- The roll first_sign and Inventarium print on.
INSERT INTO formats (description, width_mm, height_mm) VALUES
    ('50 x 30', 50, 30);

COMMIT;
