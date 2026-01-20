from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="RIB Extraction API")

# Allow CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

import sys
from fastapi import HTTPException

# Paths for static files (Frontend)
if getattr(sys, 'frozen', False):
    # Running in a bundle (PyInstaller)
    base_dir = sys._MEIPASS
    static_dir = os.path.join(base_dir, "static")
else:
    # Running in normal Python environment
    # In dev, static might be inside backend/static or just /app/static in docker
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    if not os.path.exists(static_dir):
         static_dir = "/app/static"

# Only mount static files if the directory exists
if os.path.exists(static_dir):
    # Mount /_next and other static folders if they exist
    next_dir = os.path.join(static_dir, "_next")
    if os.path.exists(next_dir):
        app.mount("/_next", StaticFiles(directory=next_dir), name="static_next")
    
    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Prevent intercepting API calls (prefix /api/v1)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        # Check if a specific file exists in static (e.g. favicon.ico, etc.)
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Otherwise return index.html for client-side routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
             return FileResponse(index_path)
        
        return {"error": "Frontend not found (index.html missing)", "path_checked": index_path}
else:
    # Dev mode: Static files not mounted, frontend runs separately
    pass

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {"status": "ok", "service": "RIB-App Backend", "ocr_engine": "DocTR"}
