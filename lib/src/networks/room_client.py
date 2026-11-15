import socket
import json

def findLanRoom(
    room_code: str,
    discovery_port: int = 50001,
    timeout: float = 5.0
) -> dict | None:
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    sock.settimeout(0.5)

    request = {
        "type": "discover",
        "room_code": room_code
    }

    try:
        sock.bind(("", 0))

        # LAN内に問い合わせをブロードキャスト
        sock.sendto(
            json.dumps(request).encode("utf-8"),
            ("255.255.255.255", discovery_port)
        )

        import time
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                data, address = sock.recvfrom(1024)
            except socket.timeout:
                continue

            try:
                response = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

            if response.get("type") != "room_found":
                continue

            return {
                "host": address[0],
                "port": response["tcp_port"]
            }

        return None

    finally:
        sock.close()
