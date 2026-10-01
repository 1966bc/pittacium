# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The Observer: told when subscribed, not after, and no unknown events."""

import unittest

from events import Events
from memory_log import MemoryLog


class Listener:
    """Remembers the row ids it was told about."""

    def __init__(self):
        self.heard = []

    def on_event(self, row_id):
        self.heard.append(row_id)


class TestEvents(unittest.TestCase):

    def setUp(self):
        self.events = Events(MemoryLog())
        self.listener = Listener()

    def test_a_subscriber_is_told_the_row(self):
        self.events.subscribe("templates", self.listener.on_event)
        self.events.notify("templates", 7)
        self.assertEqual(self.listener.heard, [7])

    def test_an_unsubscribed_window_is_not_told(self):
        self.events.subscribe("templates", self.listener.on_event)
        self.events.unsubscribe("templates", self.listener.on_event)
        self.events.notify("templates", 7)
        self.assertEqual(self.listener.heard, [])

    def test_a_misspelt_event_is_refused(self):
        with self.assertRaises(ValueError):
            self.events.subscribe("template", self.listener.on_event)


if __name__ == "__main__":
    unittest.main()
