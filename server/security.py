from quart import current_app as app
import time
from database import db, redis
import bcrypt
import requests as r
from os import getenv
from dotenv import load_dotenv
load_dotenv()
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

SensitiveFields = ["password", "token"]

class UserFlags:
    """Represents the flags a user has."""
    SYSTEM = 1
    DELETED = 2
    PROTECTED = 4

def has_permission(permissions: int, permission: int) -> bool:
    """
    Checks if a user has a permission.
    """
    if ((permissions & Permissions.ADMIN) == Permissions.ADMIN):
        return True
    return ((permissions & permission) == permission)

def return_blocked_ips():
    """
    Returns a list of blocked IPs.
    """
    return [ip.to_ip for ip in app.db.netblock.find_many()]

def is_blocked(ip):
    """
    Checks if an IP is blocked.
    """
    blocked_ips = [ip.to_ip for ip in app.db.netblock.find_many()]
    return (ip in blocked_ips)

def background_tasks() -> None:
    """
    Runs background tasks.
    """
    while True:
        time.sleep(5) # sleep for 30 minutes
        print("✨ Running background tasks...")
        #print(db.user.find_many(take=25))
        print("✅ Finished background tasks!")

def is_ratelimited(bucket_id: str):
    remaining_time = redis.get(f"ratelimit:{bucket_id}")
    if remaining_time is not None and int(remaining_time.decode()) < 1:
        return True
    else:
        return False


def ratelimit(bucket: str, limit: int, seconds: int):
    remaining_time = redis.get(f"ratelimit:{bucket}")
    if remaining_time is None:
        remaining_time = limit
    else:
        remaining_time = int(remaining_time.decode())

    expires = redis.ttl(f"ratelimit:{bucket}")
    if expires <= 0:
        expires = seconds

    remaining_time -= 1
    redis.set(f"ratelimit:{bucket}", remaining_time, ex=expires)

def hash_password(password: str) -> str:
    """
    Hashes a password.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed_password: str) -> bool:
    """
    Checks a password.
    """
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def check_if_using_vpn(ip: str) -> bool:
    """
    Checks if an IP is using a VPN.
    """
    if not getenv("IPHUB_API_KEY", None):
        return False
    response = r.get(f"http://v2.api.iphub.info/ip/{ip}", headers={"X-Key": getenv("IPHUB_API_KEY")})
    try:
        response.raise_for_status()
    except r.exceptions.HTTPError:
        return f"An http error occured! {response.status_code}"
    
    return response.json()["block"] == 1