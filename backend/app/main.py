
from fastapi import FastAPI

from app.routes.database import router as database_router
from app.routes.users import router as users_router
from app.routes.prompts import router as prompt_router


# Create the FastAPI application
app = FastAPI(
    title="AI Prompt Firewall",
    description="AI Security and Prompt Guardrail Middleware",
    version="1.0.0"
)


# Register API routers
app.include_router(database_router)
app.include_router(users_router)
app.include_router(prompt_router)


# Root endpoint
@app.get("/")
def home():
    return {
        "message": "AI Prompt Firewall API is running!",
        "status": "active"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "AI Prompt Firewall"
    }
