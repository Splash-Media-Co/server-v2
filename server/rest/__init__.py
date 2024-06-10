from quart import Quart, request
from .home import home
from .users import users
from .auth import auth
import orjson
from database import db
import security
from prisma.models import User

app = Quart(__name__)

app.db = db
app.register_blueprint(home)
app.register_blueprint(users)
app.register_blueprint(auth)

async def get_user_data(token: str) -> User:
    user = await db.user.find_first(
        where={"tokens": {"some": {"token": token}}},
        include={"restrictionsBy": True}
    )
    return user

@app.before_request
async def check_auth():
    request.user = None
    request.permissions = 0
    if "Token" in request.headers:
        token = request.headers["Token"]
        user = security.get_user_data(token)
        if user:
            request.user = user.username
            request.permissions = user.permissions
            request.restrictions = user.restrictionsBy


@app.route("/", methods=["GET", "POST"])
async def main():
    return "Hello world! The Splash API is up and running!"


@app.route("/ip", methods=["GET"])
async def ip():
    return orjson.dumps(request.remote_addr)


@app.errorhandler(400)
async def bad_request(e):
    return {"error": True, "type": "bad_request"}, 400


@app.errorhandler(401)
async def unauthorized(e):
    return {"error": True, "type": "unauthorized"}, 401


@app.errorhandler(403)
async def missing_permissions(e):
    return {"error": True, "type": "missing_permissions"}, 403


@app.errorhandler(424)
async def profanity_detected(e):
    return {"error": True, "type": "profanity_detected"}, 424


@app.errorhandler(404)
async def not_found(e):
    return {"error": True, "type": "not_found"}, 404


@app.errorhandler(405)
async def method_not_allowed(e):
    return {"error": True, "type": "method_not_allowed"}, 405


@app.errorhandler(429)
async def too_many_requests(e):
    return {"error": True, "type": "too_many_requests"}, 429


@app.errorhandler(500)
async def internal(e):
    return {"error": True, "type": "internal"}, 500


@app.errorhandler(501)
async def not_implemented(e):
    return {"error": True, "type": "not_implemented"}, 501
