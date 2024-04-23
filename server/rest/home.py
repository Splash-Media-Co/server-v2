from quart import Blueprint, current_app as app, request, abort
from prisma.models import Post  # noqa: F401

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
    data = await request.get_json()
    result = await app.helper.create_post("dummy", data['content'], "home2", request)
    return abort(result) if isinstance(result, int) else result