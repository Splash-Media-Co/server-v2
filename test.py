from prisma import Prisma
from secrets import token_urlsafe

db = Prisma()

def generate_token() -> str:
    """
    Generates a token.
    """
    return token_urlsafe(32)

tokens = [generate_token()]

db.connect()
db.user.update(where={"uuid": "14d41628-0927-4640-9244-539f8d9a5fff"}, data={"tokens": str(tokens)})
