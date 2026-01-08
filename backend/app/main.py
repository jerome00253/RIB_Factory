from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

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

# Mount static files (Frontend)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Ensure the static directory exists (it will be populated in Docker)
static_dir = "/app/static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/_next", StaticFiles(directory=f"{static_dir}/_next"), name="static_next")

# Catch-all for SPA (serve index.html for non-API routes)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Check if a specific file exists in static (e.g. favicon.ico, etc.)
    file_path = f"{static_dir}/{full_path}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise return index.html for client-side routing
    index_path = f"{static_dir}/index.html"
    if os.path.exists(index_path):
         return FileResponse(index_path)
    return {"error": "Frontend not found (index.html missing)"}

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {"status": "ok", "service": "RIB-App Backend", "ocr_engine": "DocTR"}
