
import socket
from lib.src.networks.net_utils import setReuseAddress
import threading
import queue


class TcpHost:
    def __init__(self, port: int = 50000):
        self.port = port
        self.server = None
        self.conn = None

        self.events = queue.Queue()
        self.running = False
        self.connected = False

    def start(self) -> None:
        self.running = True
        threading.Thread(
            target=self._accept,
            daemon=True
        ).start()

    def _accept(self) -> None:
        try:
            self.server = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            setReuseAddress(self.server)

            self.server.bind(("0.0.0.0", self.port))
            self.server.listen(1)

            self.events.put(("listening", self.port))

            self.conn, address = self.server.accept()

            self.connected = True
            self.events.put(("connected", address))

            buffer = bytearray()

            while self.running:
                data = self.conn.recv(4096)

                if not data:
                    break

                buffer.extend(data)

                while b"\n" in buffer:
                    message, _, remainder = buffer.partition(b"\n")
                    buffer = bytearray(remainder)

                    if message:
                        self.events.put(("message", bytes(message)))

        except OSError as e:
            if self.running:
                self.events.put(("error", str(e)))

        finally:
            # 自分からcloseした場合は通知しない
            disconnected = self.running and self.connected

            self.close()

            if disconnected:
                self.events.put(("disconnected", None))

    def send(self, data: bytes) -> None:
        if self.conn is not None:
            self.conn.sendall(data)

    def close(self) -> None:
        self.running = False
        self.connected = False

        for sock in (self.conn, self.server):
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()

        self.conn = None
        self.server = None
