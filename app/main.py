"""
GDPR-aware User Data Service - Main FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import engine, Base
from app.routers import auth, users, consents, rtbf, audit

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="GDPR-aware User Data Service",
    description="A privacy-by-design user data service with PII encryption, consent tracking, and Right-to-be-Forgotten",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(consents.router)
app.include_router(rtbf.router)
app.include_router(audit.router)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "GDPR-aware User Data Service",
        "version": "1.0.0",
        "description": "Privacy-by-design user data service with PII encryption, consent tracking, and RTBF",
        "docs": "/docs",
        "features": [
            "PII encryption at rest using envelope encryption",
            "Consent tracking and management",
            "Right-to-be-Forgotten (RTBF) processing",
            "Comprehensive audit logging",
            "GDPR compliance tools"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-data-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
