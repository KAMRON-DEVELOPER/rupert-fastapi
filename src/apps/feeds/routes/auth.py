from src.apps.users.routes import users_router


@users_router.get("/auth")
def auth(): ...
