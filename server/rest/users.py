from quart import Blueprint, current_app as app, request, abort
import security

users = Blueprint('users', __name__, url_prefix='/users')

@users.get("/")
async def get_users():
    user = str(request.args.get('username'))
    if user is not None:
        user_result = await app.helper.get_user(user)
        return abort(user_result) if isinstance(user_result, int) else user_result
    else:
        page = int(request.args.get('page', 0))
        users_result = await app.helper.get_users(page)
        return abort(users_result) if isinstance(users_result, int) else users_result

@users.post("/")
async def create_user():
    if request.user is not None:
        return {"error": True, "message": "User already logged in"}, 400
    # chech ratelimit
    if security.is_ratelimited(f"user_creation:{request.remote_addr}"):
        return abort(429)
    security.ratelimit(f"user_creation:{request.remote_addr}", 1, 1800) # one account every 30 minutes
    user = await request.get_json()
    user_result = await app.helper.create_user(user)
    return abort(user_result) if isinstance(user_result, int) else user_result