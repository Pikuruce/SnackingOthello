import secrets
import string

def generateRoomCode() -> str:
    characters = string.ascii_uppercase + string.digits
    characters = characters.translate(
        str.maketrans("", "", "0O1I")
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(6)
    )