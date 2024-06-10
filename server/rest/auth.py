from quart import Blueprint, current_app as app, request, abort
import base64
from security import generate_token
import ast

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.post("/")
async def authenticate():
    # Check if user is already authenticated
    if request.user is not None:
        return {"error": True, "message": "User already logged in"}, 400
    
    # Check if request contains auth header
    if "Authorization" not in request.headers:
        return abort(401)

    # Decode the Authorization header
    try:
        auth_type, auth_data = request.headers["Authorization"].split(" ", 1)
        if auth_type != "Basic":
            return abort(401)

        decoded_auth = base64.urlsafe_b64decode(auth_data).decode('utf-8')
        username, password = decoded_auth.split(":", 1)
    except (ValueError, base64.binascii.Error):
        return abort(401)

    # Validate username and password lengths
    if not (1 <= len(username) <= 20) or not (6 <= len(password) <= 255):
        return abort(400)
    
    # Get the user
    user = app.db.user.find_first(where={"username": username})

    if not user:
        return {"error": True, "message": "User not found"}
    
    token = generate_token()
    
    # If user already has tokens
    if user.tokens:
        # Convert str representation of list to an actual list
        tokens = ast.literal_eval(user.tokens)
        # Append token
        tokens.append(token)
        # Update DB
        app.db.user.update(where={"uuid": user.uuid}, data={
            "tokens": str(tokens)
        })
    # If not
    else:
        # Create new list with token
        tokens = [token]
        # Update DB
        app.db.user.update(where={"uuid": user.uuid}, data={
            "tokens": str(tokens)
        })
    return {"error": False, "token": token}