"""
FastAPI application entrypoint.

Initializes database, routes, and scheduler.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.db.database import engine
from app.db.schema import Base, init_db
from app.config import settings
from app.api import routes
from app.scheduler.jobs import start_scheduler, stop_scheduler

# Initialize database tables
init_db()

# Create FastAPI app
app = FastAPI(
    title="Dead-Man Check-In",
    description="Local-first check-in system",
    version="0.1.0",
)

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
frontend_dist = os.path.abspath(os.path.join(base_dir, "..", "..", "frontend", "dist"))
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
    print("📍 Dead-Man Check-In starting...")
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on app shutdown"""
    stop_scheduler()
    print("👋 Dead-Man Check-In shutting down...")


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
