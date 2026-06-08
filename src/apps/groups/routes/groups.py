from src.apps.groups.routes import groups_router


@groups_router.get("/groups", response_model=None)
def groups(): ...
