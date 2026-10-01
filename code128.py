# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Code 128, encoded by hand.

The printer draws the bars; this class is for knowing how wide they will
be, drawing them in the preview, and refusing what cannot be encoded.

One subset for the whole symbol, chosen here and told to the printer, so
the preview and the label are the same symbol: subset C when the data is
an even number of digits - two digits per symbol character, the narrowest
- and subset B otherwise, printable ASCII. Mixed data is not split into
runs: on a label a few modules more are worth a choice nobody has to
reproduce.

'>' is refused: in a ZPL Code 128 field it starts an invocation code.
"""


class Code128:
    """Subset B or C, start, data, checksum, stop."""

    #: Bar and space widths, in modules, of the symbol characters 0-106.
    PATTERNS = (
        "212222 222122 222221 121223 121322 131222 122213 122312 132212 "
        "221213 221312 231212 112232 122132 122231 113222 123122 123221 "
        "223211 221132 221231 213212 223112 312131 311222 321122 321221 "
        "312212 322112 322211 212123 212321 232121 111323 131123 131321 "
        "112313 132113 132311 211313 231113 231311 112133 112331 132131 "
        "113123 113321 133121 313121 211331 231131 213113 213311 213131 "
        "311123 311321 331121 312113 312311 332111 314111 221411 431111 "
        "111224 111422 121124 121421 141122 141221 112214 112412 122114 "
        "122411 142112 142211 241211 221114 413111 241112 134111 111242 "
        "121142 121241 114212 124112 124211 411212 421112 421211 212141 "
        "214121 412121 111143 111341 131141 114113 114311 411113 411311 "
        "113141 114131 311141 411131 211412 211214 211232 2331112"
    ).split()

    START = {"B": 104, "C": 105}
    STOP = 106

    #: Modules around the symbol that must stay blank for a scanner.
    QUIET = 10

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    def get_problem(self, data):
        """Why data cannot be encoded, or an empty string."""
        problem = ""
        wrong = [char for char in data
                 if not 32 <= ord(char) <= 126 or char == ">"]
        if data == "":
            problem = "Nothing to encode."
        elif wrong:
            problem = ("Code 128 takes letters, digits and signs without "
                       "accents, and not '>'.")
        return problem

    def get_subset(self, data):
        """C for an even number of digits, B for anything else."""
        subset = "B"
        if data.isdigit() and len(data) % 2 == 0:
            subset = "C"
        return subset

    def get_values(self, data):
        """Start, data, checksum and stop, as symbol character values."""
        subset = self.get_subset(data)
        values = [self.START[subset]]
        if subset == "C":
            for index in range(0, len(data), 2):
                values.append(int(data[index:index + 2]))
        else:
            for char in data:
                values.append(ord(char) - 32)

        checksum = values[0]
        for position in range(1, len(values)):
            checksum += position * values[position]
        values.append(checksum % 103)
        values.append(self.STOP)
        return values

    def get_modules(self, data):
        """Bars and spaces as a string of '1' (bar) and '0' (space)."""
        modules = []
        for value in self.get_values(data):
            bar = True
            for width in self.PATTERNS[value]:
                colour = "0"
                if bar:
                    colour = "1"
                modules.append(colour * int(width))
                bar = not bar
        return "".join(modules)
