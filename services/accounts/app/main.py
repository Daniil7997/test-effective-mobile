from fastapi import FastAPI

from app.api.v1.routers import main_router
from app.core.config import settings


application = FastAPI(root_path=settings.api_root_url)

application.include_router(main_router)
