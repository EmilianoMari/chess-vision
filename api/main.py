"""
Chess Vision API - Main FastAPI application
Backend-only service for chess board position recognition from photos.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from typing import Optional
import json

logger = structlog.get_logger()

app = FastAPI(
    title="Chess Vision API",
    description="Chess board position recognition from photos using ensemble ML models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for chess-ai frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to chess-ai domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "chess-vision",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint for Nomad."""
    return {
        "status": "healthy",
        "service": "chess-vision",
        "version": "1.0.0"
    }


@app.post("/api/scan")
async def scan_board(
    image: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    """
    Scan chess board from photo and return FEN notation.

    **Note**: This is a placeholder implementation.
    Full ML pipeline will be implemented in future version.

    Args:
        image: Chess board photo (JPEG/PNG, max 10MB)
        options: JSON string with scan options:
            - confidence_threshold: float (0.5-1.0)
            - enable_validation: bool
            - return_annotated: bool
            - tta_enabled: bool

    Returns:
        JSON with FEN, confidence scores, validation status, and per-square details
    """
    try:
        # Parse options
        scan_options = {}
        if options:
            try:
                scan_options = json.loads(options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid options JSON")

        # Validate image
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload JPEG or PNG image."
            )

        # TODO: Implement full ML pipeline
        # For now, return placeholder response with starting position
        logger.info(
            "scan_board_request",
            filename=image.filename,
            content_type=image.content_type,
            options=scan_options
        )

        # Placeholder response - starting chess position
        return {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "overall_confidence": 0.95,
            "processing_time_ms": 100,
            "validation": {
                "is_valid": True,
                "errors": []
            },
            "squares": [
                {
                    "square": f"{chr(97 + col)}{row + 1}",
                    "piece": None,
                    "confidence": 0.98,
                    "needs_review": False
                }
                for row in range(8)
                for col in range(8)
            ],
            "note": "Placeholder implementation - full ML pipeline coming soon"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("scan_board_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/models/status")
async def models_status():
    """Check status of loaded ML models."""
    return {
        "models_loaded": False,
        "yolov8": {"loaded": False, "path": None},
        "resnet50": {"loaded": False, "path": None},
        "efficientnet": {"loaded": False, "path": None},
        "note": "ML models not yet implemented"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
