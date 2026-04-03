from src.apps.groups.routes import groups_router


@groups_router.get("/groups")
def groups(): ...
