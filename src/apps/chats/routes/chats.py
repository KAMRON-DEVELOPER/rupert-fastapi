from src.apps.chats.routes import chats_router


@chats_router.get("/chats")
def chats(): ...
