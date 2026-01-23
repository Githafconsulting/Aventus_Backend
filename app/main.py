from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routes import auth, contractors, third_parties, timesheets, clients, contracts, work_orders, templates, quote_sheets, proposals, payroll, payslips, invoices, notifications
from app.database import engine, Base
import traceback

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

# CORS configuration - allow all origins for development
# In production, you would want to restrict this to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handler to ensure errors are returned with proper format
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
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
app.include_router(notifications.router)  # Already has /api/v1/notifications prefix


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
