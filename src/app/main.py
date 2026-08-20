from fastapi import FastAPI
from app.api.api_router import api_router
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="MyActivities API",
    description="Welcome to the MyActivities API documentation!",
    root_path="/api/v1",
    docs_url="/docs",
    openapi_url="/docs/openapi.json",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix="/myactivities")