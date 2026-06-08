from src.apps.posts.routes import posts_router


@posts_router.get("/posts", response_model=None)
def posts(): ...
