
import socket
import threading
import queue


class TcpClient:
    def __init__(self, host: str, port: int = 50000):
        self.host = host
        self.port = port
        self.conn = None

        self.events = queue.Queue()
        self.running = False
        self.connected = False

    def connect(self) -> None:
        self.running = True
        threading.Thread(
            target=self._connect,
            daemon=True
        ).start()

    def _connect(self) -> None:
        try:
            self.conn = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            self.conn.settimeout(5)

            self.conn.connect((self.host, self.port))
            self.conn.settimeout(None)

            self.connected = True
            self.events.put(("connected", None))

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

        if self.conn is not None:
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            self.conn.close()
            self.conn = None
