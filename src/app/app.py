from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import router as main_router
from core.database import initialize_database
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await initialize_database()
    yield


app = FastAPI(
    lifespan=lifespan,
)

@app.get("/", include_in_schema=False)
def index_to_docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="docs")


app.include_router(main_router)
