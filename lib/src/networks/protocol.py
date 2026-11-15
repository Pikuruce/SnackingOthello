import json


def encodeMessage(action: str, row: int, col: int) -> bytes:
    message = {
        "action": action,
        "position": [row, col]
    }

    return (
        json.dumps(message).encode("utf-8")
        + b"\n"
    )


def decodeMessage(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))