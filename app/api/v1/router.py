from fastapi import APIRouter

from app.api.v1.messages import router as messages_router
from app.api.v1.smartsheet import router as smartsheet_router

router = APIRouter(prefix="/api/v1")
router.include_router(messages_router)
router.include_router(smartsheet_router)
