# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The interface in the operator's language.

A dictionary keyed by the English string, one entry per language, a
single translator and a `_()` that every window calls. English is the key
and not a code: `_("Print")` reads as what it says, and a string with no
translation yet comes out in English rather than as a symbol.

Not translated, deliberately: the log, exception messages, and anything
stored - a symbology code means the same whoever wrote the row.
"""

#: Language code to the name in that language: somebody who has the
#: interface in the wrong language finds their own by recognising it.
LANGUAGES = {"en": "English",
             "it": "Italiano"}

DEFAULT_LANGUAGE = "en"

#: The English string to its translations, grouped as the interface is.
TRANSLATIONS = {

    # -- shared sentences ----------------------------------------------------
    "Nothing selected.": {"it": "Nessuna selezione."},
    "Please fill in every field.": {"it": "Compila tutti i campi."},
    "Choose a value from the list.": {"it": "Scegli un valore dall'elenco."},
    "Items: {0}": {"it": "Elementi: {0}"},

    # -- main window ---------------------------------------------------------
    "File": {"it": "File"},
    "Exit": {"it": "Esci"},
    "Section: {0}": {"it": "Sezione: {0}"},
}


class I18N:
    """Holds the chosen language and answers with it."""

    def __init__(self, language=None):
        self.language = DEFAULT_LANGUAGE
        if language in LANGUAGES:
            self.language = language

    def __str__(self):
        return "class: {0}\nlanguage: {1}".format(self.__class__.__name__,
                                                  self.language)

    def get(self, key):
        """The string in the current language, or the English it was given.

        Falling back to the key is the point: a string not yet in the
        dictionary shows in English, legible and obviously untranslated. It
        never raises - a missing translation must not stop a label.
        """
        text = key
        if self.language != DEFAULT_LANGUAGE:
            text = TRANSLATIONS.get(key, {}).get(self.language, key)
        return text

    def set_language(self, language):
        if language not in LANGUAGES:
            raise ValueError("unknown language: {0}".format(language))
        self.language = language


#: One translator for the process, set by the Engine at start. Built here
#: and not on first use: it touches neither disk nor database, so there is
#: nothing to defer, and set_language changes it rather than replacing it.
_i18n = I18N()


def set_language(language):
    _i18n.set_language(language)


def get_language():
    return _i18n.language


def _(key):
    """Translate. The name is short because it appears on every string."""
    return _i18n.get(key)


def get_untranslated(language):
    """Keys with no translation into `language`, so the gap can be counted."""
    if language not in LANGUAGES:
        raise ValueError("unknown language: {0}".format(language))

    missing = []
    if language != DEFAULT_LANGUAGE:
        for key in sorted(TRANSLATIONS):
            if not TRANSLATIONS[key].get(language):
                missing.append(key)
    return missing
