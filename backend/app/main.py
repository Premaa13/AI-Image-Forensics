# =============================================================================
# FastAPI Application Entry Point
# Purpose: Configures and runs the AI Image Detection API server
# =============================================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="AI Image Forensics API",
    description="Detects whether an image is AI-generated or Real using EfficientNet",
    version="1.0.0",
)

# CORS - Allow frontend to call API during development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["detection"])


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok", "service": "ai-image-forensics"}

@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    # Always return JSON instead of plain "Internal Server Error"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Unhandled server error: {type(exc).__name__}: {str(exc)}"},
    )