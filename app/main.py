"""
FastAPI application entrypoint.

Initializes database, routes, and scheduler.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os

from app.db.database import engine
from app.db.schema import Base, init_db
from app.config import settings
from app.api import routes
# from app.scheduler.jobs import start_scheduler, stop_scheduler  # Disabled for now

# Initialize database tables
init_db()

# Create FastAPI app
app = FastAPI(
    title="Dead-Man Check-In",
    description="Local-first check-in system",
    version="0.1.0",
)

# Include API routes
app.include_router(routes.router)


@app.on_event("startup")
async def startup():
    """Initialize on app startup"""
    print("📍 Dead-Man Check-In starting...")
    # start_scheduler()  # Disabled for now


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on app shutdown"""
    # stop_scheduler()  # Disabled for now
    print("👋 Dead-Man Check-In shutting down...")


@app.get("/")
async def root(request: Request):
    phone_cookie = request.cookies.get('phone')
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    login_path = os.path.join(base_dir, "templates", "login.html")
    index_path = os.path.join(base_dir, "templates", "index.html")

    if not phone_cookie:
        response = FileResponse(login_path) if os.path.exists(login_path) else {"msg": "no login"}
    else:
        response = FileResponse(index_path) if os.path.exists(index_path) else {"msg": "no index"}

    # CRITICAL: Prevent Safari from caching the "mode" (login vs dashboard)
    if isinstance(response, FileResponse):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response


@app.get("/login")
async def login_page():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    login_path = os.path.join(base_dir, "templates", "login.html")
    return FileResponse(login_path)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
