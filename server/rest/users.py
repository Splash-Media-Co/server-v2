from quart import Blueprint, current_app as app, request, abort

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