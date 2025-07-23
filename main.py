from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.database import engine, Base
import uvicorn

# Create FastAPI application
app = FastAPI(
    title="Calendar Integration API",
    description="API for calendar integration and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="")

# # Root endpoint
# @app.get("/")
# async def root():
#     return {
#         "message": "Calendar Integration API",
#         "version": "1.0.0",
#         "status": "running"
#     }

# # Health check endpoint
# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "message": "API is running"}

# # Create database tables on startup
# @app.on_event("startup")
# async def create_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )