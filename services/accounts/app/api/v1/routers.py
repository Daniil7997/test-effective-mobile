from fastapi import APIRouter

from app.api.v1.endpoints import router


main_router = APIRouter()

main_router.include_router(router)
