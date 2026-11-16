import json
import select
import socket
import time

from lib.src.networks.net_utils import getLocalIPv4Addresses


def _openBroadcastSocket(bind_address: str) -> socket.socket | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((bind_address, 0))
        sock.setblocking(False)
        return sock
    except OSError:
        sock.close()
        return None


def _broadcastTargets(bind_address: str) -> list[str]:
    targets = ["255.255.255.255"]

    # 家庭用LANで一般的な /24 を仮定した宛先も併用する
    if bind_address:
        parts = bind_address.split(".")
        targets.append(".".join(parts[:3] + ["255"]))

    return targets


def findLanRoom(
    room_code: str,
    discovery_port: int = 50001,
    timeout: float = 5.0,
    resend_interval: float = 0.5
) -> dict | None:
    """
    LAN 内のホストを UDP ブロードキャストで探す。

    Windows では 255.255.255.255 宛ての送信が1つのネットワークからしか出ないため、
    PC の各 IPv4 アドレスごとにソケットを作り、それぞれから送る。
    UDP は届かないことがあるので、見つかるまで一定間隔で再送する。
    """
    request = json.dumps({
        "type": "discover",
        "room_code": room_code
    }).encode("utf-8")

    sockets: list[tuple[socket.socket, list[str]]] = []

    for address in getLocalIPv4Addresses():
        sock = _openBroadcastSocket(address)
        if sock is not None:
            sockets.append((sock, _broadcastTargets(address)))

    # どのアドレスでも開けなかった場合は OS 任せの経路で送る
    if not sockets:
        sock = _openBroadcastSocket("")
        if sock is None:
            raise OSError("UDP ソケットを開けませんでした")
        sockets.append((sock, _broadcastTargets("")))

    try:
        deadline = time.monotonic() + timeout
        next_send = 0.0

        while True:
            now = time.monotonic()
            if now >= deadline:
                return None

            if now >= next_send:
                for sock, targets in sockets:
                    for target in targets:
                        try:
                            sock.sendto(request, (target, discovery_port))
                        except OSError:
                            # 送れない経路（切断中の仮想NICなど）は無視
                            pass
                next_send = now + resend_interval

            wait = max(0.0, min(next_send, deadline) - time.monotonic())
            readable, _, _ = select.select(
                [sock for sock, _ in sockets], [], [], wait
            )

            for sock in readable:
                try:
                    data, address = sock.recvfrom(1024)
                except OSError:
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

    finally:
        for sock, _ in sockets:
            sock.close()
