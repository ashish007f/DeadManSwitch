"""
FastAPI application entrypoint.

Initializes database, routes, and scheduler.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
import os

from app.config import settings
from app.api import routes
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.limiter import limiter

# Custom rate limit handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler to return JSON instead of plain text"""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

# Add limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)

# Resolve frontend dist path
base_dir = os.path.dirname(os.path.abspath(__file__))
default_local_dist = os.path.abspath(os.path.join(base_dir, "..", "..", "frontend", "dist"))
frontend_dist = settings.frontend_dist or os.getenv("FRONTEND_DIST", default_local_dist)

print(f"📦 Serving frontend from: {frontend_dist}")
print(f"📁 Exists: {os.path.exists(frontend_dist)}")

# Serve React static files if frontend/dist exists
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Specific PWA / Static files at root
    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(os.path.join(frontend_dist, "sw.js"))

    @app.get("/manifest.webmanifest")
    async def serve_manifest():
        return FileResponse(os.path.join(frontend_dist, "manifest.webmanifest"))

    @app.get("/registerSW.js")
    async def serve_register_sw():
        return FileResponse(os.path.join(frontend_dist, "registerSW.js"))

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    # Fallback for React SPAs
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # 1. Try to serve a specific file if it exists in dist (e.g., icons, favicon)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 2. Handle API 404s
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # 3. Default to index.html for all other routes (for client-side routing)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"msg": "Frontend not built. Run 'npm run build' in frontend/ directory."}


@app.on_event("startup")
async def startup():
    """Initialize on app startup"""
    print("📍 I'mGood Check-In starting...")
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on app shutdown"""
    stop_scheduler()
    print("👋 I'mGood Check-In shutting down...")


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
