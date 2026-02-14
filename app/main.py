from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.database import init_db
from app.routers import orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Orders API", lifespan=lifespan)

app.include_router(orders.router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
