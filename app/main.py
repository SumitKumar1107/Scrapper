from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import search, company, research
from app.utils.exceptions import ScraperException, scraper_exception_handler
from app.cache.file_cache import FileCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Clear all cache files
    cache = FileCache()
    deleted = cache.clear_all()
    if deleted > 0:
        logger.info(f"Startup: Cleared {deleted} cache files")
    yield
    # Shutdown: nothing to do


# Create FastAPI app
app = FastAPI(
    title="Financial Data Scraper",
    description="Scrapes financial data from screener.in and displays interactive charts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Exception handlers
app.add_exception_handler(ScraperException, scraper_exception_handler)

# Include API routers
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(company.router, prefix="/api", tags=["Company"])
app.include_router(research.router, prefix="/api", tags=["Research"])


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Financial Data Scraper is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
