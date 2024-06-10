from quart import Blueprint, current_app as app, request, abort
from prisma.models import Post  # noqa: F401
import security
import splashclasses

home = Blueprint('home', __name__, url_prefix='/home')

@home.get("/")
async def get_posts():
    # get param page
    page = int(request.args.get('page', 0))
    posts = app.db.post.find_many(include={
        "post_revisions": True,
    }, take=25, skip=(page*25))
    return [post.model_dump() for post in posts] if posts else []

@home.post("/")
async def post():
    if not request.user:
        return 401

    for restrict in request.restrictions:
        if security.has_restriction(restrict.restrictions, splashclasses.Restrictions.HOME_POSTS):
            return abort(403)
    data = await request.get_json()
    try:
        post_content = data["content"]
    except KeyError:
        return abort(400)
    
    result = await app.helper.create_post(request.user, post_content, "home", request)
    return abort(result) if isinstance(result, int) else result