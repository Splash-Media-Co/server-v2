from quart import Blueprint, current_app as app, request, abort
import security

users = Blueprint('users', __name__, url_prefix='/users')

@users.get("/")
async def get_users():
    user = request.args.get('username', None)
    if user:
        user_result = await app.helper.get_user(user)
        if user_result == 404:
            return {"error": True, "message": "User not found"}, 404
        return user_result
    else:
        page = int(request.args.get('page', 0))
        users_result = await app.helper.get_users(page)
        if users_result == 416:
            return {"error": True, "message": "No more users"}, 416
        return users_result

@users.post("/")
async def create_user():
    if request.user is not None:
        return {"error": True, "message": "User already logged in"}, 400
    
    # chech ratelimit
    if security.is_ratelimited(f"user_creation:{request.remote_addr}"):
        return abort(429)
    security.ratelimit(f"user_creation:{request.remote_addr}", 5, 1800) # one account every 30 minutes

    user = await request.get_json()

    # Check if it includes a body
    if not user:
        abort(400)
    
    # Check if it has all the required parameters
    if "username" not in user or "password" not in user:
        return abort(400)
    
    # Check if username is the same as password (thanks engineerrunner)
    if user["username"] == user["password"]:
        return abort(400)

    # Check parameter lenght
    if len(user["username"]) < 1 or len(user["username"]) > 20 or len(user["password"]) < 6 or len(user["password"]) > 255:
        return abort(400)
    
    # If everything is okay, proceed with creation
    user_result = await app.helper.create_user(user["username"], user["password"])
    if isinstance(user_result, int):
        return abort(user_result)
    
    for key in ["password", "restrictionsTo"]:
        user_result.pop(key)
    return user_result