from fastapi import Request, HTTPException
from src.validation.kantian_validator import KantianValidationError

async def validation_exception_handler(request: Request, exc: KantianValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": [{
                "msg": str(exc),
                "type": "kantian_validation",
                "loc": [exc.field]
            }]
        }
    )

# Register in FastAPI app
app.add_exception_handler(KantianValidationError, validation_exception_handler) 