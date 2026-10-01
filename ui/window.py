# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""How a window reaches the engine, written once.

The engine lives on the root window, so any widget can find it by name from
anywhere in the tree, and nothing has to be handed down a constructor:
`self.engine.db.read_all(sql)`.

Not a widget class, which is deliberate: a Toplevel and a Frame both need
this and they are not each other.
"""


class Window:
    """The engine, reached from any widget in the tree.

    Whoever adds a __str__ to a window: Tk uses str(widget) as the widget's
    path name, so a __str__ that returns anything else breaks every call
    that takes parent=self, with `bad window path name`.
    """

    @property
    def engine(self):
        return self.nametowidget(".").engine
