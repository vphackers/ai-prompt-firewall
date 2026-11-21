
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.database import router as database_router
from app.routes.users import router as users_router
from app.routes.prompts import router as prompt_router


# Create the FastAPI application
app = FastAPI(
    title="AI Prompt Firewall",
    description="AI Security and Prompt Guardrail Middleware",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
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
