from src.apps.companies.routes import companies_router


@companies_router.get("/companies")
def companies(): ...
