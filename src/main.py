from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Import the router and driver functions
from src.api.v1.endpoints import categories, concepts, relationships
from src.db.neo4j_driver import get_async_driver, close_async_driver
from src.validation.kantian_validator import KantianValidationError # Adjust import path if needed

# Use lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup...")
    try:
        # Initialize driver on startup to catch connection errors early
        await get_async_driver()
        print("Neo4j driver initialized successfully.")
    except Exception as e:
        print(f"FATAL: Error during application startup: {e}")
        # Depending on policy, you might want to exit or prevent startup
    yield
    # Code to run on shutdown
    print("Application shutdown...")
    await close_async_driver()
    print("Neo4j driver closed.")


app = FastAPI(
    title="Chat Ontology Builder Backend",
    description="API for managing and querying the Kantian knowledge graph.",
    version="0.1.0",
    lifespan=lifespan # Add the lifespan manager
)

@app.get("/")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Chat Ontology Builder API"}

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}

# Include the categories router
app.include_router(categories.router, prefix="/api/v1", tags=["Categories"])

# Mount concepts router under /api/v1/concepts
app.include_router(concepts.router, prefix="/api/v1/concepts", tags=["Concepts"])

# Mount relationships router under /api/v1/relationships
app.include_router(
    relationships.router,
    prefix="/api/v1/relationships",
    tags=["Relationships"]
)

# Add Exception Handlers

@app.exception_handler(KantianValidationError)
async def kantian_validation_exception_handler(request: Request, exc: KantianValidationError):
    """
    Handles custom validation errors defined by KantianValidator.
    Returns a standard 422 Unprocessable Entity response.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": [{
                # Use field name from the exception if available
                "loc": ["body", exc.field] if exc.field else ["body"],
                "msg": str(exc),
                "type": "kantian_validation_error" # Specific type for clarity
            }]
        },
    )

@app.exception_handler(RequestValidationError)
async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic validation errors.
    Formats the response to be consistent with FastAPI's default or your desired structure.
    """
    # You can customize the formatting here if needed,
    # otherwise, FastAPI provides a default handler.
    # This example shows how to return the standard Pydantic error structure.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Remove the __main__ block if you always run with uvicorn command
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)
