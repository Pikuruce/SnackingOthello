import ipaddress
import socket
import sys


def setReuseAddress(sock: socket.socket) -> None:
    """
    待ち受けソケットのアドレス再利用設定。

    Windows の SO_REUSEADDR は「他プロセスが同じポートを横取りできる」意味になり、
    古いプロセスが残っていると通信がそちらに届いてしまうため、排他設定にする。
    それ以外の OS では TIME_WAIT 中の再バインドのために SO_REUSEADDR を使う。
    """
    if sys.platform == "win32" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def getPrimaryIPv4() -> str | None:
    """
    外部への経路に使われる自分の IPv4 アドレスを返す（実際にパケットは送らない）
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        address = sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()

    if address.startswith("127.") or address == "0.0.0.0":
        return None
    return address


def getLocalIPv4Addresses() -> list[str]:
    """
    このPCが持つ IPv4 アドレスの一覧（ループバック除く）。主経路のアドレスを先頭にする。
    """
    addresses: list[str] = []

    primary = getPrimaryIPv4()
    if primary is not None:
        addresses.append(primary)

    try:
        infos = socket.getaddrinfo(
            socket.gethostname(),
            None,
            socket.AF_INET
        )
    except OSError:
        infos = []

    for info in infos:
        address = info[4][0]
        if address.startswith("127.") or address in addresses:
            continue
        addresses.append(address)

    return addresses


def parseIPv4(text: str) -> str | None:
    """
    文字列が IPv4 アドレスならそれを返す。違えば None
    """
    try:
        return str(ipaddress.IPv4Address(text.strip()))
    except ValueError:
        return None
