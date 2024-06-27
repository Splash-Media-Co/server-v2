from secrets import token_urlsafe
from splashclasses import Permissions

import time
from os import getenv

import bcrypt
import requests as r
from database import redis
from dotenv import load_dotenv
from quart import current_app as app

load_dotenv()

SensitiveFields = ["password", "tokens", "chats", "delete", "extra_flags", "restrictionsBy", "restrictionsTo"]


class UserFlags:
    """Represents the flags a user has."""

    SYSTEM = 1
    DELETED = 2
    PROTECTED = 4



def has_permission(permissions: int, permission: int) -> bool:
    """
    Checks if a user has a permission.
    """
    if (permissions & Permissions.ADMIN) == Permissions.ADMIN:
        return True
    return (permissions & permission) == permission

def has_restriction(restrictions: int, restriction: int) -> bool:
    """
    Checks if a user has a restriction.
    """
    return (restrictions & restriction) == restriction

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
    return ip in blocked_ips


def background_tasks() -> None:
    """
    Runs background tasks.
    """
    # No background tasks at the moment...
    pass


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


def generate_token() -> str:
    """
    Generates a token.
    """
    return token_urlsafe(32)


def check_if_using_vpn(ip: str) -> bool:
    """
    Checks if an IP is using a VPN.
    """
    if not getenv("IPHUB_API_KEY", None):
        return False
    response = r.get(
        f"http://v2.api.iphub.info/ip/{ip}", headers={"X-Key": getenv("IPHUB_API_KEY")}
    )
    try:
        response.raise_for_status()
    except r.exceptions.HTTPError:
        return f"An http error occured! {response.status_code}"

    return response.json()["block"] == 1
