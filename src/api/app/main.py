from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import auth, kds, live, menu, orders
from app.config import settings
from app.db import create_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_schema()
    yield


app = FastAPI(title="Qahwati API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.web_origin.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(kds.router)
app.include_router(live.router)


@app.get("/api/health")
def health():
    return {"ok": True}
