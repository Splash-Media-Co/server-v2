from quart import current_app as app

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