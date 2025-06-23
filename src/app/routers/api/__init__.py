from fastapi import APIRouter

from app.routers.api.hello_world import router as hello_world_router
from app.routers.api.chat_bot import router as chat_bot_router
from app.routers.api.channel_api import router as channel_router
from app.routers.api.webhook import router as webhook_router
router = APIRouter(prefix="/api")
router.include_router(hello_world_router)
router.include_router(chat_bot_router)
router.include_router(channel_router)
router.include_router(webhook_router)
