from __future__ import annotations

from typing import Callable, ParamSpec

from multiprocessing import Process
from os import kill as _kill, getpid
from pickle import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from tkinter import Tk

try:
    # UNIX
    from signal import SIGKILL as __sig1, SIGABRT as __sig2, SIGTERM as __sig3
except ImportError:
    # WIN
    from signal import SIGBREAK as __sig1, SIGABRT as __sig2, SIGTERM as __sig3

_killsigs = (__sig1, __sig2, __sig3)

_P = ParamSpec("_P")


class TkBgReceiver:

    server_address: tuple[str, int]
    process: Process
    sock: socket

    def __init__(
            self,
            server_address: tuple[str, int],
            process: Process,
    ):
        self.server_address = server_address
        self.process = process
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.connect(self.server_address)

    def close(self):
        self.sock_kill()

    def sock_kill(self):
        self.sock.shutdown(SHUT_RDWR)
        self.sock.close()

    def term_server(self):
        self.sock_kill()
        self.process.terminate()

    def receive(self, block: bool = False, block_value: object = None) -> object:
        self.sock.setblocking(block)
        try:
            data = b''
            while _data := self.sock.recv(1024):
                data += _data
            return loads(data)
        except BlockingIOError:
            return block_value

    def __delete__(self):
        self.sock_kill()


class TkBgServer:

    tk: Tk
    sock: socket
    instand_return: bool
    instand_block: bool
    daemon: bool

    def kill(self):
        pid = getpid()
        for sig in _killsigs:
            _kill(pid, sig)

    def send(self, obj: object):
        conn, addr = self.sock.accept()
        return conn.send(dumps(obj))

    def sock_kill(self):
        self.sock.shutdown(SHUT_RDWR)
        self.sock.close()

    def exit(self):
        self.tk.destroy()
        self.sock_kill()

    def __delete__(self):
        self.sock_kill()

    def __init__(
            self, 
            address: str = "127.0.0.11",
            port: int = 50_000,
            daemon: bool = True,
            instand_return: bool = False,
            instand_return_blocking: bool = True,
    ):
        self.server_address = (address, port)
        self.instand_return = instand_return
        self.instand_block = instand_return_blocking
        self.daemon = daemon

    def __call__(self, make: Callable[[TkBgServer, _P], Tk]) -> Callable[[_P], TkBgReceiver | object]:

        def wrapper(*args, **kwargs) -> TkBgReceiver | object:

            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.sock.bind(self.server_address)
            self.sock.listen(1)

            def proc(*_args, _sock=self.sock, **_kwargs):
                self.sock = _sock
                self.tk = make(*_args, **_kwargs | dict(server=self))
                # (Trial-and-Error knowledge)
                # The styling for <SelectTreeWidget.SelectTree(ttk.Treeview)> is not applied 
                # if <.update_idletasks> is only executed here.
                # [ see also <treeselectpopup.popup.func> ]
                self.tk.mainloop()
                try:
                    self.send(None)
                except OSError as e:
                    if e.errno != 9:  # recv closed
                        raise
                return

            process = Process(target=proc, args=args, kwargs=kwargs, daemon=self.daemon)
            recv = TkBgReceiver(self.server_address, process)
            process.start()

            if self.instand_return:
                return recv.receive(self.instand_block)
            else:
                return recv

        return wrapper
