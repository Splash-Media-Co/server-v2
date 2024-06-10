from oceanlink import OceanLinkServer, OceanLinkClient, OceanLinkAuthPkt
from database import db
from prisma.models import User

class Restrictions:
    HOME_POSTS = 1
    CHAT_POSTS = 2
    NEW_CHATS = 4
    EDITING_CHAT_DETAILS = 8
    EDITING_PROFILE = 16

class Permissions:
    """
    Represents the permissions a user has (mostly taken from Meower). 
    """
    ADMIN = 1

    VIEW_REPORTS = 2
    EDIT_REPORTS = 4

    VIEW_NOTES = 8
    EDIT_NOTES = 16

    VIEW_POSTS = 32
    DELETE_POSTS = 64

    VIEW_ALTS = 128
    SEND_ALERTS = 256
    KICK_USERS = 512
    CLEAR_USER_QUOTES = 1024
    VIEW_BAN_STATES = 2048
    EDIT_BAN_STATES = 4096
    DELETE_USERS = 8192

    VIEW_IPS = 16384
    BLOCK_IPS = 32768

    VIEW_CHATS = 65536
    EDIT_CHATS = 131072

    SEND_ANNOUNCEMENTS = 262144
    BYPASS_PROFANITY = 524288

class SplashCommands:
    def __init__(self, server: OceanLinkServer, helper):
        self.server = server
        self.helper = helper
        self.server.set_auth_command_function(self.auth)
    
    async def auth(self, client: OceanLinkClient, packet: OceanLinkAuthPkt):
        if client.username is not None:
            return await client.send_statuscode("success", packet["listen_to"])
        user: User = db.user.find_first(
            where={"tokens": {"some": {"token": packet["token"]}}},
            include={"restrictionsBy": True}
        )
        if user:
            client.set_username(user.username)
            user = user.model_dump()
            for key in ["password", "extra_flags", "restrictionsTo"]:
                user.pop(key, None)
            return await client.send(user, listener=packet["listen_to"])
