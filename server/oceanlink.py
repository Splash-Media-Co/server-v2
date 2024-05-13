import websockets
import asyncio
import json
from typing import Optional, Iterable, TypedDict

VER = "0.0.0.1"
STATUS_CODES = {
    0: {
        "error": True,
        "message": "Banned"
    }
}


def construct(errorCode: int) -> str:
    if errorCode not in STATUS_CODES:
        return "Internal Server Error - Wrong ErrorCode"
    toReturn = ""
    if STATUS_CODES[errorCode]["error"]:
        toReturn += "Error — "
    return toReturn + STATUS_CODES[errorCode]["message"]

class OceanLinkAuthPkg(TypedDict):
    token: str
    listen_to: str
    
class OceanLinkServer:
    def __init__(self):
        self.message = "YDOLO - Your data only lives once"
        self.clients
        self.true_ip_header = Optional[str]

class OceanLinkClient:
    def __init__(
        self,
        server: OceanLinkServer,
        websocket: websockets.WebSocketServerProtocol
    ):
        self.server = server
        self.ws = websocket
        self.username = Optional[str] #grr, no username? :megamind:
        self.ip: str = self.get_ip()

    def get_ip(self):
        # thanks, cloudlink.
        if self.server.real_ip_header and self.server.real_ip_header in self.websocket.request_headers:
            return self.websocket.request_headers[self.server.real_ip_header]
        elif type(self.websocket.remote_address) == tuple:
            return self.websocket.remote_address[0]
        else:
            return self.websocket.remote_address