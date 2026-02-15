# Chess Vision - Architecture Deep Dive

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Web Browser │    │  Mobile App  │    │  CLI Tool    │     │
│  │   (Upload)   │    │   (Camera)   │    │  (Batch)     │     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│         │                   │                    │              │
│         └───────────────────┴────────────────────┘              │
│                             │                                   │
│                             ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                        API GATEWAY                               │
├─────────────────────────────┼───────────────────────────────────┤
│                             │                                    │
│         ┌───────────────────▼─────────────────┐                 │
│         │      Traefik Reverse Proxy          │                 │
│         │  • SSL Termination                  │                 │
│         │  • Rate Limiting                    │                 │
│         │  • Load Balancing                   │                 │
│         └───────────────────┬─────────────────┘                 │
│                             │                                    │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                     APPLICATION LAYER                            │
├─────────────────────────────┼───────────────────────────────────┤
│                             │                                    │
│    ┌────────────────────────▼──────────────────────┐            │
│    │         FastAPI Application                   │            │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │            │
│    │  │ Upload   │  │  Status  │  │  Result  │   │            │
│    │  │ Handler  │  │ Handler  │  │ Handler  │   │            │
│    │  └────┬─────┘  └────┬─────┘  └────┬─────┘   │            │
│    └───────┼─────────────┼─────────────┼──────────┘            │
│            │             │             │                        │
│            ▼             ▼             ▼                        │
│    ┌──────────────────────────────────────────┐                │
│    │       Request Processing Service         │                │
│    │  • Validation                            │                │
│    │  • Queue Management                      │                │
│    │  • Result Caching                        │                │
│    └──────────────┬───────────────────────────┘                │
│                   │                                             │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼ Async Queue
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: PREPROCESSING (2s)                             │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  Input Image ──┬─> Original                             │   │
│  │                ├─> Contrast Enhanced                     │   │
│  │                ├─> Denoised (Gaussian)                   │   │
│  │                ├─> Sharpened (Unsharp Mask)              │   │
│  │                └─> Perspective Corrected (Auto)          │   │
│  │                                                          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: BOARD DETECTION (1s)                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  5 Variants ──┬─> Hough Lines + RANSAC ─┐               │   │
│  │               ├─> Neural Chessboard ────┼─> Ensemble    │   │
│  │               └─> Template Matching ────┘    Voting     │   │
│  │                                               ↓          │   │
│  │                                         64 Grid Points   │   │
│  │                                                          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: SQUARE EXTRACTION & PARALLEL PROCESSING (5s)   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  Grid → Extract 64 Squares → Process in Parallel        │   │
│  │                                                          │   │
│  │  For each square:                                       │   │
│  │    ┌─────────────────────────────────────┐              │   │
│  │    │ Square Image (150x150)              │              │   │
│  │    │         │                            │              │   │
│  │    │         ├─> YOLOv8 (w=0.40) ─┐      │              │   │
│  │    │         ├─> ResNet50 (w=0.35)┼─> Weighted Vote    │   │
│  │    │         └─> EfficientNet(w=0.25)     │              │   │
│  │    │                              │       │              │   │
│  │    │         If confidence < 0.85:│       │              │   │
│  │    │         Re-classify with TTA │       │              │   │
│  │    │                              │       │              │   │
│  │    │                              ▼       │              │   │
│  │    │         { piece, confidence }        │              │   │
│  │    └─────────────────────────────────────┘              │   │
│  │                                                          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: CHESS VALIDATION (1s)                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  64 Predictions ──> Chess Rules Engine                  │   │
│  │                     • Exactly 2 kings                    │   │
│  │                     • Max 16 pieces per side             │   │
│  │                     • No pawns on rank 1/8               │   │
│  │                     • Total pieces ≤ 32                  │   │
│  │                     • Check if position is legal         │   │
│  │                           │                              │   │
│  │                           ├─> Valid ✓                    │   │
│  │                           └─> Invalid ✗ → Flag for review│   │
│  │                                                          │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STAGE 5: OUTPUT GENERATION (1s)                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  Validated Predictions ──┬─> FEN Converter               │   │
│  │                          ├─> Confidence Map              │   │
│  │                          ├─> Annotation Renderer         │   │
│  │                          └─> Result Serializer           │   │
│  │                                     │                    │   │
│  │                                     ▼                    │   │
│  │           ┌──────────────────────────────────────┐       │   │
│  │           │ Final Result                         │       │   │
│  │           │ • FEN string                         │       │   │
│  │           │ • Per-square confidence              │       │   │
│  │           │ • Validation errors                  │       │   │
│  │           │ • Annotated image (base64)           │       │   │
│  │           │ • Processing metrics                 │       │   │
│  │           └──────────────────────────────────────┘       │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼ Store Results
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    MinIO     │  │    Redis     │  │  PostgreSQL  │          │
│  │  (Images)    │  │  (Cache)     │  │  (Metadata)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Preprocessing Module

**Purpose**: Enhance image quality and create multiple variants for robustness

**Input**: Raw uploaded image (any size, JPEG/PNG)
**Output**: 5 normalized image variants (640x640)

```python
class PreprocessingPipeline:
    def process(self, image: np.ndarray) -> dict[str, np.ndarray]:
        return {
            "original": self._normalize(image),
            "contrast": self._enhance_contrast(image),
            "denoised": self._denoise(image),
            "sharpened": self._sharpen(image),
            "corrected": self._auto_perspective(image)
        }

    def _normalize(self, img):
        # Resize to 640x640, preserve aspect ratio with padding
        pass

    def _enhance_contrast(self, img):
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        pass

    def _denoise(self, img):
        # Gaussian blur σ=1.5
        pass

    def _sharpen(self, img):
        # Unsharp mask with radius=2, amount=1.5
        pass

    def _auto_perspective(self, img):
        # Detect lines → Find largest quadrilateral → Warp to square
        pass
```

---

### 2. Board Detection Module

**Purpose**: Locate chessboard and extract 64 grid points

**Input**: 5 image variants
**Output**: Grid coordinates (8x8 = 64 points)

```python
class BoardDetectionEnsemble:
    def __init__(self):
        self.detectors = [
            HoughLinesDetector(weight=0.35),
            NeuralChessboardDetector(weight=0.40),
            TemplateMatchingDetector(weight=0.25)
        ]

    def detect(self, images: dict) -> GridCoordinates:
        predictions = []

        for detector in self.detectors:
            for variant_name, img in images.items():
                pred = detector.detect(img)
                predictions.append({
                    "grid": pred.grid,
                    "confidence": pred.confidence,
                    "weight": detector.weight,
                    "variant": variant_name
                })

        # Weighted voting
        final_grid = self._ensemble_vote(predictions)

        if final_grid.confidence < 0.95:
            raise BoardNotDetectedError()

        return final_grid
```

#### 2.1 Hough Lines Detector

```python
class HoughLinesDetector:
    def detect(self, image):
        # 1. Canny edge detection
        edges = cv2.Canny(image, 50, 150)

        # 2. Hough line transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )

        # 3. Separate horizontal/vertical lines
        h_lines, v_lines = self._classify_lines(lines)

        # 4. RANSAC to find best-fit grid
        grid = self._ransac_grid(h_lines, v_lines)

        return grid
```

#### 2.2 Neural Chessboard Detector

```python
class NeuralChessboardDetector:
    def __init__(self):
        self.model = load_model("models/board_detector.onnx")

    def detect(self, image):
        # CNN predicts 64 corner coordinates directly
        corners = self.model.predict(image)  # Shape: (64, 2)

        # Verify geometric consistency
        if not self._is_valid_grid(corners):
            return None

        return GridCoordinates(corners, confidence=0.95)
```

---

### 3. Piece Classification Module

**Purpose**: Classify each of 64 squares (13 classes: empty + 12 piece types)

**Classes**:
```
0: empty
1: wp (white pawn)
2: wn (white knight)
3: wb (white bishop)
4: wr (white rook)
5: wq (white queen)
6: wk (white king)
7: bp (black pawn)
8: bn (black knight)
9: bb (black bishop)
10: br (black rook)
11: bq (black queen)
12: bk (black king)
```

**Ensemble Strategy**:

```python
class EnsembleClassifier:
    def __init__(self):
        self.models = {
            "yolov8": YOLOv8Classifier(weight=0.40),
            "resnet50": ResNet50Classifier(weight=0.35),
            "efficientnet": EfficientNetClassifier(weight=0.25)
        }

    def predict_square(self, square_image: np.ndarray) -> Prediction:
        # Get predictions from all models
        predictions = []
        for name, model in self.models.items():
            pred = model.predict(square_image)
            predictions.append({
                "class_probs": pred.probabilities,  # Shape: (13,)
                "weight": model.weight
            })

        # Weighted soft voting
        final_probs = self._weighted_average(predictions)
        class_id = np.argmax(final_probs)
        confidence = final_probs[class_id]

        # If low confidence, try TTA
        if confidence < 0.85:
            tta_pred = self._tta_predict(square_image)
            if tta_pred.confidence > confidence:
                return tta_pred

        return Prediction(
            class_id=class_id,
            piece=CLASS_NAMES[class_id],
            confidence=confidence
        )

    def _tta_predict(self, square_image):
        # Test-time augmentation: 8 transforms
        augmentations = [
            lambda x: x,                          # Original
            lambda x: np.rot90(x, k=1),           # Rotate 90°
            lambda x: np.rot90(x, k=3),           # Rotate 270°
            lambda x: np.flip(x, axis=1),         # Flip horizontal
            lambda x: adjust_brightness(x, 1.1),  # Brighten
            lambda x: adjust_brightness(x, 0.9),  # Darken
            lambda x: adjust_contrast(x, 1.15),   # More contrast
            lambda x: sharpen(x)                  # Sharpen
        ]

        predictions = []
        for aug in augmentations:
            aug_image = aug(square_image)
            pred = self.predict_square(aug_image)
            predictions.append(pred)

        # Majority voting
        return self._majority_vote(predictions)
```

---

### 4. Chess Validation Module

**Purpose**: Verify position follows chess rules

```python
class ChessValidator:
    def validate(self, predictions: list[SquarePrediction]) -> ValidationResult:
        errors = []

        # Convert to python-chess Board
        board = self._predictions_to_board(predictions)

        # Rule 1: Exactly 1 king per color
        if len(board.pieces(chess.KING, chess.WHITE)) != 1:
            errors.append("Invalid number of white kings")
        if len(board.pieces(chess.KING, chess.BLACK)) != 1:
            errors.append("Invalid number of black kings")

        # Rule 2: Max 8 pawns per color
        if len(board.pieces(chess.PAWN, chess.WHITE)) > 8:
            errors.append("Too many white pawns")
        if len(board.pieces(chess.PAWN, chess.BLACK)) > 8:
            errors.append("Too many black pawns")

        # Rule 3: Pawns not on rank 1 or 8
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                rank = chess.square_rank(square)
                if rank in [0, 7]:
                    errors.append(f"Pawn on illegal rank {rank}")

        # Rule 4: Total pieces ≤ 32
        if len(board.piece_map()) > 32:
            errors.append("Too many pieces on board")

        # Rule 5: Both kings not in check simultaneously
        if self._both_in_check(board):
            errors.append("Both kings in check (impossible)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            confidence=self._compute_overall_confidence(predictions)
        )
```

---

## Model Inference Flow

```
┌────────────────────────────────────────┐
│  Square Image (150x150x3)              │
└───────────┬────────────────────────────┘
            │
            ├──────────────────────────────┐
            │                              │
            ▼                              ▼
    ┌───────────────┐            ┌───────────────┐
    │   YOLOv8      │            │  ResNet50     │
    │   (ONNX)      │            │  (ONNX)       │
    └───────┬───────┘            └───────┬───────┘
            │                            │
            │ Probs (13,)                │ Probs (13,)
            │ Weight: 0.40               │ Weight: 0.35
            │                            │
            └─────────┬──────────────────┘
                      │
                      │            ┌───────────────┐
                      │            │ EfficientNet  │
                      │            │  (ONNX)       │
                      │            └───────┬───────┘
                      │                    │
                      │                    │ Probs (13,)
                      │                    │ Weight: 0.25
                      │                    │
                      ▼                    ▼
              ┌────────────────────────────────┐
              │   Weighted Average             │
              │   avg = Σ(prob_i * weight_i)   │
              └─────────────┬──────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  argmax(avg)  │
                    │  confidence   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────────┐
                    │ confidence < 0.85?│
                    └─────┬─────────┬───┘
                          │ No      │ Yes
                          │         │
                          │         ▼
                          │   ┌──────────────┐
                          │   │ TTA (8 aug)  │
                          │   │ Majority vote│
                          │   └──────┬───────┘
                          │          │
                          ▼          ▼
                    ┌─────────────────────┐
                    │  Final Prediction   │
                    │  {piece, conf}      │
                    └─────────────────────┘
```

---

## Deployment Architecture

```
┌────────────────────────────────────────────────────┐
│              Nomad Cluster                         │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │  Job: chess-vision (replicas: 2)            │  │
│  │                                             │  │
│  │  ┌────────────┐       ┌────────────┐       │  │
│  │  │ Instance 1 │       │ Instance 2 │       │  │
│  │  │            │       │            │       │  │
│  │  │ FastAPI    │       │ FastAPI    │       │  │
│  │  │ + Models   │       │ + Models   │       │  │
│  │  │            │       │            │       │  │
│  │  │ CPU: 2     │       │ CPU: 2     │       │  │
│  │  │ RAM: 4GB   │       │ RAM: 4GB   │       │  │
│  │  └────────────┘       └────────────┘       │  │
│  └─────────────────────────────────────────────┘  │
│                      │                            │
│                      ▼ Service Discovery          │
│  ┌─────────────────────────────────────────────┐  │
│  │  Consul                                     │  │
│  │  Service: chess-vision.service.consul       │  │
│  └─────────────────────────────────────────────┘  │
│                      │                            │
└──────────────────────┼────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │  Traefik Edge Router    │
         │  chess-vision.seas.io   │
         └─────────────────────────┘
```

---

## Performance Optimization Strategies

### 1. Model Optimization
- Convert PyTorch → ONNX → TensorRT (GPU)
- Quantization: FP32 → FP16 (minimal accuracy loss)
- Batch inference for 64 squares
- Model caching in memory

### 2. Caching
```python
# Redis cache structure
cache_key = f"scan:{image_hash}"
cache_value = {
    "fen": "rnbqkbnr/...",
    "confidence": 0.94,
    "squares": [...],
    "ttl": 3600  # 1 hour
}
```

### 3. Async Processing
```python
@app.post("/api/scan")
async def scan_board(image: UploadFile):
    # 1. Validate & store
    request_id = await storage.save_image(image)

    # 2. Enqueue processing (non-blocking)
    await queue.enqueue(process_image, request_id)

    # 3. Return immediately
    return {"request_id": request_id, "status": "processing"}

@app.get("/api/scan/{request_id}")
async def get_result(request_id: str):
    # Poll for result
    result = await cache.get(request_id)
    return result
```

### 4. Parallel Square Processing
```python
async def classify_all_squares(squares: list[np.ndarray]):
    # Process 64 squares in parallel
    tasks = [
        classify_square(square)
        for square in squares
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Error Handling & Recovery

```python
# Graceful degradation
def process_image(image):
    try:
        # Stage 1: Preprocessing
        variants = preprocess(image)
    except Exception as e:
        logger.error("Preprocessing failed", error=e)
        return Error("Invalid image")

    try:
        # Stage 2: Board detection
        grid = detect_board_ensemble(variants)
    except BoardNotDetectedError:
        # Fallback: Try single best detector
        grid = detect_board_fallback(variants)

    try:
        # Stage 3: Classification
        predictions = classify_squares(grid)
    except Exception as e:
        logger.error("Classification failed", error=e)
        # Fallback: Use only YOLOv8 (fastest)
        predictions = yolo_only_classify(grid)

    # Continue with validation...
```

---

## Monitoring & Observability

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

scan_total = Counter("scans_total", "Total scans processed")
scan_errors = Counter("scan_errors_total", "Total scan errors")
scan_duration = Histogram("scan_duration_seconds", "Scan processing time")
accuracy_gauge = Gauge("scan_accuracy", "Recent scan accuracy")

@scan_duration.time()
def process_scan(image):
    scan_total.inc()
    try:
        result = pipeline.process(image)
        accuracy_gauge.set(result.confidence)
        return result
    except Exception as e:
        scan_errors.inc()
        raise
```

---

## Security Considerations

1. **Input Validation**
   - Max image size: 10MB
   - Allowed formats: JPEG, PNG only
   - Scan for malicious payloads

2. **Rate Limiting**
   - Per-IP: 10 req/hour (anonymous)
   - Per-API-key: 100 req/hour

3. **Resource Limits**
   - Max processing time: 30s (timeout)
   - Max concurrent: 10 requests
   - Memory limit per request: 500MB

4. **Data Privacy**
   - Images auto-deleted after 24h
   - No logging of image content
   - Optional anonymous mode

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-15
