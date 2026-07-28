"""
API Version 1 Router Aggregator.
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.follows import router as follows_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.ws import router as ws_router
from app.api.v1.blogs import router as blogs_router
from app.api.v1.comments import router as comments_router
from app.api.v1.billing import router as billing_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.notifications import router as notifications_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(follows_router)
api_router.include_router(conversations_router)
api_router.include_router(ws_router)
api_router.include_router(blogs_router)
api_router.include_router(comments_router)
api_router.include_router(billing_router)
api_router.include_router(rooms_router)
api_router.include_router(notifications_router)

__all__ = [
    "api_router",
]
