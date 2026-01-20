from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import auth, contractors, third_parties, timesheets, clients, contracts, work_orders, templates, quote_sheets, proposals, payroll, payslips, invoices
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Aventus HR Contractor Management System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - allow localhost and local network IPs
# In production, you would want to restrict this to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(contractors.router, prefix="/api/v1")
app.include_router(third_parties.router)
app.include_router(timesheets.router, prefix="/api/v1")
app.include_router(clients.router)  # Already has /api/v1/clients prefix
app.include_router(contracts.router, prefix="/api/v1")  # Has /contracts prefix
app.include_router(work_orders.router)  # Already has /api/v1/work-orders prefix
app.include_router(templates.router)  # Already has /api/v1/templates prefix
app.include_router(quote_sheets.router)  # Already has /api/v1/quote-sheets prefix
app.include_router(proposals.router)  # Already has /api/v1/proposals prefix
app.include_router(payroll.router)  # Already has /api/v1/payroll prefix
app.include_router(payslips.router)  # Already has /api/v1/payslips prefix
app.include_router(invoices.router)  # Already has /api/v1/invoices prefix


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
