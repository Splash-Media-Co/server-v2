import requests as r
import orjson
from pydantic import BaseModel
from prisma.models import Post, User
from cloudlink import CloudlinkServer
from quart import current_app as app, Request
from uuid import uuid4
from time import time
import security
from database import db

"""Your little companion that does what it says."""


def todict(json):
    """Converts a JSON input to a dictionary."""
    return orjson.loads(json)


def uuid():
    """Generates a random UUID."""
    return str(uuid4())


class ProfanityResult(BaseModel):
    """
    A class to represent the result of the profanity detector.

    Attributes
    ----------
    isProfanity : bool
        True if profanity is detected, False otherwise.
    score: float
        The score of the profanity detection.
    """

    isProfanity: bool
    score: float


class Profanity:
    """
    A class to represent the profanity detector.

    Attributes
    ----------
    url : str
        The url to the profanity detector.
    """

    def __init__(self, url):
        """
        Constructs all the necessary attributes for the Profanity object.

        Parameters
        ----------
            url : str
                The url to the profanity detector.
        """
        self.url = url

    def detect(self, text):
        """
        Detects profanity in a text.

        Parameters
        ----------
            text : str
                The text to detect profanity in.

        Returns
        -------
            bool
                True if profanity is detected, False otherwise.
        """
        response = r.post(
            self.url,
            json={"message": text},
            headers={"Content-Type": "application/json"},
        ).content
        return ProfanityResult(**todict(response)).isProfanity


# Classes!
class Helper:
    def __init__(self, cl: CloudlinkServer):
        self.cl = cl
        self.profanity = Profanity("https://vector.profanity.dev")

    async def create_post(
        self, username: str, content: str, origin: str, request: Request
    ) -> dict:
        # badRequest if the post is 4000 characters or longer, is less than 1 character long, or is just whitespaces
        if len(content) > 4000 or content.isspace() or len(content) < 1:
            return 400
        post = Post(
            id=uuid(),
            content=content,
            author_username=username,
            creation_date=round(time()),
            origin=origin,
        )
        if self.profanity.detect(content) and not security.has_permission(
            request.permissions, security.Permissions.BYPASS_PROFANITY
        ):
            return 424
        db_result = db.post.create(
            data=post.model_dump(exclude_unset=True)
        ).model_dump()
        if origin == "home":
            self.cl.broadcast({"type": "post_home", "val": db_result}, direct_wrap=True)
        else:
            chat = db.chat.find_unique(
                where={"chatuuid": origin}, include={"members": True}
            )
            if chat:
                chat_members = [m.userId for m in chat.members]
                self.cl.broadcast(
                    {
                        "cmd": "post_chat",
                        "val": {
                            "username": username,
                            "chat_name": chat.name,
                            "chat_id": origin,
                            "content": content,
                        },
                    },
                    usernames=list(
                        set(app.cl.get_ulist().split(";")) & set(chat_members)
                    ),
                )
        return db_result

    async def get_user(self, username: str) -> dict:
        to_return = db.user.find_first(where={"username": username})
        print(to_return)
        if to_return:
            to_return = to_return.model_dump()
            # remove all entries that have a key in security.SensitiveFields
            for k in security.SensitiveFields:
                to_return.pop(k, None)
        else:
            return 404
        return to_return

    async def get_users(self, page: int) -> list:
        users = db.user.find_many(skip=page * 25, take=25)
        print(users)
        if users:
            # remove all entries that have a key in security.SensitiveFields
            for user in users:
                for k in security.SensitiveFields:
                    user.pop(k, None)
        else:
            return 404
        return users
    async def create_user(self, username: str, password: str) -> dict:
        user = User(
            username=username,
            uuid=uuid(),
            creation_date=round(time()),
            password=security.hash_password(password),
            pfp="default",
            token="none",
            permissions=0,
            banned=False
        ).model_dump(exclude_unset=True)
        return db.user.create(data=user).model_dump()