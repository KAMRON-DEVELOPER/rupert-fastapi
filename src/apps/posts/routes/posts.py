from src.apps.posts.routes import posts_router


@posts_router.get("/posts")
def posts(): ...
