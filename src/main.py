from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import the router and driver functions
from src.api.v1.endpoints import categories, concepts
from src.db.neo4j_driver import close_driver, get_driver

# Use lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup...")
    try:
        # Initialize driver on startup to catch connection errors early
        get_driver()
    except Exception as e:
        print(f"FATAL: Could not connect to Neo4j on startup: {e}")
        # Depending on policy, you might want to exit or prevent startup
    yield
    # Code to run on shutdown
    print("Application shutdown...")
    close_driver()


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
app.include_router(concepts.router, prefix="/api/v1", tags=["Concepts"])


# Remove the __main__ block if you always run with uvicorn command
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)
