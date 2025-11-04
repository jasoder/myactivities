from fastapi import FastAPI
from app.api.api_router import api_router

app = FastAPI(
    title="MyActivities API",
    description="Welcome to the MyActivities API documentation!",
    root_path="/api/v1",
    docs_url=None,
    openapi_url="/docs/openapi.json",
    redoc_url="/docs",
)

app.include_router(api_router, prefix="/myactivities")