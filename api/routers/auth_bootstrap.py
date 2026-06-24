from fastapi import APIRouter

from .auth import router as auth_router
from api.routers.users import router as users_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
