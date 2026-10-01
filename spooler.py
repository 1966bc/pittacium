# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  pittacium
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Hand a printer job over, by the transport in the settings.

    raw    the system's print queue: win32print on Windows, lpr elsewhere
    tcp    straight to the printer on port 9100, no queue in between
    file   writes the job to a file and prints nothing, for testing

send() either returns having handed the job over, or raises: a label that
did not come out is never reported as printed (CONVENTIONS.md). The 'file'
transport looks as though it works and prints nothing, so its message says
so, every time.

pywin32 is optional: only the raw transport on Windows needs it, and tcp
reaches the same printer without it.
"""

import datetime
import os
import socket
import subprocess
import sys

try:
    import win32print
    HAS_WIN32PRINT = True
except ImportError:
    HAS_WIN32PRINT = False


class Spooler:
    """One transport, one printer, and the sending of a job to it."""

    TRANSPORTS = ("raw", "tcp", "file")

    #: Seconds to wait for the printer on tcp before giving up.
    TIMEOUT = 5

    def __init__(self, transport, queue, host, port, folder, log):
        """
        transport: raw, tcp or file
        queue: the print queue for raw; empty is the system default
        host, port: the printer's address, for tcp
        folder: where the file transport writes
        """
        self.transport = transport
        self.queue = queue
        self.host = host
        self.port = int(port)
        self.folder = folder
        self.log = log
        if self.transport not in self.TRANSPORTS:
            raise ValueError("transport is {0}, one of {1}".format(
                self.transport, ", ".join(self.TRANSPORTS)))

    def __str__(self):
        return "class: {0}\ntransport: {1}".format(self.__class__.__name__,
                                                   self.transport)

    @staticmethod
    def get_queues():
        """The print queues as the system sees them.

        A queue name typed wrong is the commonest reason a label never
        comes out, so the settings window shows the real ones.
        """
        if sys.platform == "win32":
            if not HAS_WIN32PRINT:
                raise RuntimeError("listing the queues on Windows needs "
                                   "pywin32")
            flags = (win32print.PRINTER_ENUM_LOCAL
                     | win32print.PRINTER_ENUM_CONNECTIONS)
            queues = [info[2] for info in win32print.EnumPrinters(flags)]
        else:
            done = subprocess.run(["lpstat", "-a"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            if done.returncode != 0:
                raise IOError("lpstat failed: {0}".format(
                    done.stderr.decode(errors="replace").strip()))
            lines = done.stdout.decode(errors="replace").splitlines()
            queues = [line.split()[0] for line in lines if line.split()]
        return queues

    def is_printing(self):
        """False for the file transport, which prints nothing."""
        return self.transport != "file"

    def send(self, source):
        """Hand the job over and say where it went, or raise."""
        data = source.encode("utf-8")
        self.log.trace("transport={0} queue={1!r} host={2!r} bytes={3}".format(
            self.transport, self.queue, self.host, len(data)))

        if self.transport == "tcp":
            where = self.send_tcp(data)
        elif self.transport == "file":
            where = self.send_file(data)
        elif sys.platform == "win32":
            where = self.send_windows(data)
        else:
            where = self.send_lpr(data)

        return where

    def send_tcp(self, data):
        """Straight to the printer, no spooler in between."""
        if self.host == "":
            raise ValueError("tcp transport and no printer address")
        sock = socket.create_connection((self.host, self.port),
                                        timeout=self.TIMEOUT)
        try:
            sock.sendall(data)
        finally:
            sock.close()
        return "{0}:{1}".format(self.host, self.port)

    def send_file(self, data):
        """Write the job to disk and print nothing."""
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(self.folder, "label_{0}.zpl".format(stamp))
        with open(path, "wb") as f:
            f.write(data)
        return path

    def send_windows(self, data):
        """A raw job through the Windows spooler."""
        if not HAS_WIN32PRINT:
            raise RuntimeError("the raw transport on Windows needs pywin32; "
                               "the tcp transport does not")
        name = self.queue
        if name == "":
            name = win32print.GetDefaultPrinter()
        handle = win32print.OpenPrinter(name)
        try:
            win32print.StartDocPrinter(handle, 1,
                                       ("pittacium label", None, "RAW"))
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        return name

    def send_lpr(self, data):
        """A raw job through lpr, everywhere but Windows."""
        command = ["lpr", "-o", "raw"]
        if self.queue != "":
            command.extend(["-P", self.queue])
        done = subprocess.run(command, input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        if done.returncode != 0:
            detail = done.stderr.decode(errors="replace").strip()
            raise IOError("lpr failed ({0}): {1}".format(done.returncode,
                                                         detail))
        where = self.queue
        if where == "":
            where = "default queue"
        return where
