
import socket
import threading
import json


class LanDiscoveryHost:
    def __init__(
        self,
        room_code: str,
        tcp_port: int = 50000,
        discovery_port: int = 50001
    ) -> None:
        self.room_code = room_code
        self.tcp_port = tcp_port
        self.discovery_port = discovery_port

        self.running = False
        self.sock = None
        self.thread = None

    def start(self) -> None:
        self.running = True

        self.thread = threading.Thread(
            target=self._listen,
            daemon=True
        )
        self.thread.start()

    def _listen(self) -> None:
        sock = None

        try:
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )
            self.sock = sock

            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            sock.bind(("", self.discovery_port))
            sock.settimeout(1.0)

            print("UDP discovery started")

            while self.running:
                try:
                    data, address = sock.recvfrom(1024)
                except socket.timeout:
                    continue

            # 以下の受信・応答処理は今のままでOK

                try:
                    message = json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

                if message.get("type") != "discover":
                    continue

                if message.get("room_code") != self.room_code:
                    continue

                response = {
                    "type": "room_found",
                    "tcp_port": self.tcp_port
                }

                self.sock.sendto(
                    json.dumps(response).encode("utf-8"),
                    address
                )

                print(f"Room discovered by {address[0]}")

        except OSError as e:
            if self.running:
                print(f"UDP discovery error: {e}")

        finally:
            self.close()

    def close(self) -> None:
        self.running = False

        if self.sock is not None:
            self.sock.close()
            self.sock = None
