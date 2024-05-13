from helper import Helper
from cloudlink import CloudlinkServer, CloudlinkClient
import security 
from database import db

class SplashCommands:
    def __init__(self, cl: CloudlinkServer, helper: Helper):
        self.cl = cl
        self.helper = helper
        # Auth
        self.cl.add_command("auth", self.auth)

    async def auth(self, client: CloudlinkClient, val, listener: str = None):
        # This is very similar to Meower's format because of many reasons...

        # Check if client is already authenticated
        if client.username:
            return await client.send_statuscode("OK", listener)
        
        # Check if val is a dict
        if not isinstance(val, dict):
            return await client.send_statuscode("Datatype", listener)
        
        # Check if val contains the data we need
        if not ("username" in val) or not ("password" in val):
            return await client.send_statuscode("Syntax", listener)
        
        # Get values from dict
        username = val["username"]
        password = val["password"]

        # Check if values are strings
        if (not isinstance(username, str)) or (not isinstance(password, str)):
            return await client.send_statuscode("Datatype", listener)
        
        # Check username and password syntax
        if len(username) < 1 or len(username) > 20 or len(password) < 6 or len(password) > 255:
            return await client.send_statuscode("Syntax", listener)

        # Check if ratelimited
        for bucket in [f"login:i:{client.ip}", f"login:u:{username}:success", f"login:u:{username}:failed"]:
            if security.is_ratelimited(bucket):
                return await client.send_statuscode("RateLimit", listener)
        
        # Ratelimit the IP
        security.ratelimit(f"login:i:{client.ip}", 150, 1800)

        account = db.user.find_first(where={
            "username", username
            }, include={
                "token": True,
                "password": True,
                "extra_flags": True,
                "banned": True,
                "delete": True,
            })