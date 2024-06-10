import websockets
import asyncio
import json
from typing import Optional, Iterable
from pydantic import BaseModel
from utils import full_stack

VER = "0.0.0.1"
STATUS_CODES = {
    "banned": {
        "error": True,
        "message": "Banned"
    },
    "badSyntax": {
        "error": True,
        "message": "Bad Syntax"
    },
    "userNotFound": {
        "error": True,
        "message": "User not found"
    },
    "success": {
        "error": False,
        "message": "Success"
    }
}


def construct(errorCode: str) -> str:
    if errorCode not in STATUS_CODES:
        return "Internal Server Error - Wrong ErrorCode"
    toReturn = ""
    if STATUS_CODES[errorCode]["error"]:
        toReturn += "Error — "
    return toReturn + STATUS_CODES[errorCode]["message"]

class OceanLinkAuthPkt(BaseModel):
    token: str
    listen_to: str

class OceanLinkPkt(BaseModel):
    mode: str
    value: str | int | bool | list | dict | float

class OceanLinkServer:
    def __init__(self):
        self.message: Optional[str] = "YDOLO - Your data only lives once"
        self.callbacks: dict[str, list[function]] = {}  # noqa: F821
        self.auth_command: function # noqa: F821
        self.websockets: set[websockets.WebSocketServerProtocol] = set()
        self.usernames: dict[str, OceanLinkClient] = {}
        self.clients: set[OceanLinkClient] = set()
        self.true_ip_header = Optional[str]
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        print("client joined, handling thingies")
        client = OceanLinkClient(self, websocket)

        # Add websocket connection to websocket list
        self.websockets.add(websocket)

        # Add client to client list
        self.clients.add(client)

        for callback in self.callbacks.get("connect", []):
            await callback(client)

        if self.message:
            await client.send({"mode": "message", "value": self.message})

        await client.send({"mode": "version", "value": VER})
        await client.send({"mode": "userlist", "value": self.get_userlist()})

        try:
            async for packet in websocket:
                # Parse packet
                try:
                    packet: OceanLinkAuthPkt = json.loads(packet)
                except Exception:
                    await client.send_statuscode("badSyntax")
                    continue
                else:
                    if not isinstance(packet, dict):
                        await client.send_statuscode("badSyntax")
                        continue
                cmd = self.auth_command
                await cmd(client, packet)

        except Exception:
            print(full_stack())
        finally:
            self.websockets.remove(websocket)
            self.clients.remove(client)
            client.remove_username()

            for callback in self.callbacks.get("disconnect", []):
                await callback(client)
    
    def set_true_ip_header(self, true_ip_header: Optional[str] = None):
        """Set the True IP header, used when serving OceanLink behind a tunnel, like Cloudflare."""
        self.true_ip_header = true_ip_header
    
    def set_auth_command_function(self, function):  # noqa: F821
        self.auth_command = function

    def set_message(self, message: Optional[str] = None):
        """Sets the server message, sent when a client connects for the first time."""
        self.message = message
    
    def get_userlist(self) -> list:
        """Returns the current userlist"""
        return [key for key in self.usernames.keys()]

    def send_userlist(self):
        """Broadcasts the current userlist to everyone"""
        return self.broadcast({"mode": "userlist", "value": self.get_userlist()})

    def add_callback(self, event: str, callback):
        if event in self.callbacks:
            self.callbacks[event].append(callback)
        else:
            self.callbacks[event] = [callback]
    
    def broadcast(
        self,
        packet: OceanLinkPkt,
        clients: Optional[Iterable] = None,
        usernames: Optional[Iterable] = None
    ):

        if clients is None and usernames is None:
            _clients = self.clients
        else:
            _clients = []
            if clients is not None:
                _clients += clients
            if usernames is not None:
                for username in usernames:
                    if username in self.usernames:
                        _clients.append(self.usernames[username])

        websockets.broadcast({client.ws for client in _clients}, json.dumps(packet))
    
    async def run(self, host: str = "0.0.0.0", port: int = 3000):
        self.stop = asyncio.Future()
        self.server = await websockets.serve(self.handle_client, host, port)
        await self.stop
        await self.server.close()

class OceanLinkClient:
    def __init__(
        self,
        server: OceanLinkServer,
        websocket: websockets.WebSocketServerProtocol
    ):
        self.server = server
        self.ws = websocket
        self.username: str | None = None #grr, no username? :megamind:
        self.ip: str = self.get_ip()

    def get_ip(self):
        """Gets the IP of the client"""
        # thanks, cloudlink.
        if self.server.true_ip_header and self.server.true_ip_header in self.ws.request_headers:
            return self.ws.request_headers[self.server.true_ip_header]
        elif type(self.ws.remote_address) == tuple:
            return self.ws.remote_address[0]
        else:
            return self.ws.remote_address
    
    def remove_username(self):
        if not self.username:
            return
        
        if self.username in self.server.usernames:
            self.server.usernames[self.username].remove(self)
            if len(self.server.usernames[self.username]) == 0:
                del self.server.usernames[self.username]
        
        self.username = None

        self.server.broadcast(self.server.get_userlist())

    def set_username(self, username: str):
        if self.username:
            self.remove_username()

        self.username = username
        if self.username in self.server.usernames:
            self.server.usernames[username].append(self)
        else:
            self.server.usernames[username] = [self]

        self.server.send_userlist()
    
    async def send(self, packet, listener: Optional[str] = None):
        if listener:
            packet["listen_to"] = listener
        await self.ws.send(json.dumps(packet))

    def broadcast(
        self,
        packet,
        clients: Optional[Iterable] = None,
        usernames: Optional[Iterable] = None
    ):

        if clients is None and usernames is None:
            _clients = self.clients
        else:
            _clients = []
            if clients is not None:
                _clients += clients
            if usernames is not None:
                for username in usernames:
                    _clients += self.usernames.get(username, [])

        websockets.broadcast({client.websocket for client in _clients}, json.dumps(packet))

    async def send_statuscode(self, statuscode: str, listen_to: Optional[str] = None):
        return await self.send({
            "mode": "statuscode",
            "value": construct(statuscode)
        }, listener=listen_to)
    
    