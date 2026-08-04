# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

# Initialize the FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Agentic GSTR-2B Reconciliation, TDS Anomaly Detection, and Tally ERP Bridge.",
    docs_url="/docs",  # Enables interactive Swagger UI testing at /docs
)

# Enable CORS so our React 19 Frontend can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your Vercel frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug in all our API v1 endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System Health"])
async def health_check():
    """Simple status check to verify the API server is running."""
    return {"status": "ONLINE", "project": settings.PROJECT_NAME}