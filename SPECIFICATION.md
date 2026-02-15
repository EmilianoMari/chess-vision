# Chess Vision - Technical Specification

**Version:** 1.0.0
**Last Updated:** 2026-02-15
**Status:** Draft
**Architecture:** Backend-only (Frontend in chess-ai project)

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Requirements](#requirements)
3. [System Architecture](#system-architecture)
4. [Data Pipeline](#data-pipeline)
5. [Model Specifications](#model-specifications)
6. [API Specification](#api-specification)
7. [Frontend Integration](#frontend-integration)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Performance Targets](#performance-targets)

---

## 1. Project Overview

### 1.1 Objective

Develop a highly accurate computer vision system to extract chess board positions from static photos and convert them to FEN notation.

### 1.2 Core Requirements

- **Input**: Static photo (JPEG/PNG) of chess board at any angle
- **Output**: FEN notation with confidence scores per square
- **Accuracy Target**: 95%+ overall FEN accuracy
- **Performance**: ≤10 seconds processing time per image
- **Priority**: Accuracy over speed

### 1.3 Key Features

> **Note**: Chess Vision is a **backend-only service**. UI is provided by the [chess-ai](../chess-ai) project frontend.

#### Must Have (v1.0)
- ✅ Multi-stage preprocessing pipeline
- ✅ Ensemble board detection
- ✅ Ensemble piece classification (3+ models)
- ✅ Chess rule validation
- ✅ Confidence scoring per square
- ✅ FEN output with annotated image
- ✅ REST API endpoint
- ✅ Integration with chess-ai frontend

#### Should Have (v1.1)
- 🔄 Human-in-the-loop review for low confidence squares
- 🔄 Batch processing multiple images
- 🔄 Model performance monitoring
- 🔄 A/B testing different ensemble strategies

#### Could Have (v2.0)
- 💡 Real-time webcam mode
- 💡 Mobile app
- 💡 Active learning pipeline
- 💡 Support for different board/piece styles

### 1.4 Non-Goals

- ❌ Real-time video processing (not v1.0)
- ❌ Move suggestion/analysis (use Chess AI project)
- ❌ 3D board reconstruction

---

## 2. Requirements

### 2.1 Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-01 | System accepts JPEG/PNG images up to 10MB | Must | Returns error for invalid formats |
| FR-02 | Detects chessboard in photo at any angle | Must | 99%+ detection rate on test set |
| FR-03 | Classifies all 64 squares (empty + 12 piece types) | Must | 13-class classification |
| FR-04 | Validates output using chess rules | Must | Flags illegal positions |
| FR-05 | Returns confidence score per square | Must | Float 0.0-1.0 |
| FR-06 | Generates annotated image with predictions | Must | Bounding boxes + labels |
| FR-07 | Processes image in ≤10 seconds | Must | P95 latency < 10s |
| FR-08 | Handles poor lighting conditions | Should | Works with ±30% brightness |
| FR-09 | Handles perspective distortion | Should | Works up to 45° viewing angle |
| FR-10 | Supports multiple board styles | Could | Classic, wooden, digital |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-01 | Overall FEN accuracy | ≥95% | Exact match on test set |
| NFR-02 | Board detection accuracy | ≥99% | IoU > 0.9 |
| NFR-03 | Piece classification accuracy | ≥98% | Per-square accuracy |
| NFR-04 | API availability | 99.5% | Uptime monitoring |
| NFR-05 | Concurrent requests | 10 | Load testing |
| NFR-06 | Model size | <500MB total | Disk usage |
| NFR-07 | Memory usage | <4GB RAM | Runtime monitoring |
| NFR-08 | GPU optional | Can run CPU-only | Inference mode |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
├─────────────────────────────────────────┤
│  • Upload endpoint                      │
│  • Async processing                     │
│  • Result caching                       │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     Chess Vision Pipeline               │
├─────────────────────────────────────────┤
│  1. Preprocessing (2s)                  │
│     • 5 variants generation             │
│     • Contrast/denoise/sharpen          │
│                                         │
│  2. Board Detection (1s)                │
│     • Hough Lines + RANSAC              │
│     • Neural Chessboard                 │
│     • Template Matching                 │
│     • Ensemble voting                   │
│                                         │
│  3. Piece Classification (5s)           │
│     • YOLOv8                            │
│     • ResNet50                          │
│     • EfficientNet-B4                   │
│     • Weighted ensemble                 │
│     • Test-time augmentation            │
│                                         │
│  4. Chess Validation (1s)               │
│     • Rule checking                     │
│     • Confidence filtering              │
│                                         │
│  5. Output Generation (1s)              │
│     • FEN conversion                    │
│     • Annotation rendering              │
└─────────────────────────────────────────┘
```

### 3.2 Component Diagram

```
┌────────────────────────────────────────────────────┐
│                  API Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Upload  │  │  Status  │  │  Result  │        │
│  │ Endpoint │  │ Endpoint │  │ Endpoint │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼───────────────┘
        │             │             │
        ▼             ▼             ▼
┌────────────────────────────────────────────────────┐
│               Service Layer                        │
│  ┌────────────────┐  ┌────────────────┐          │
│  │ Image Service  │  │ Pipeline Svc   │          │
│  │  • Validation  │  │  • Orchestrate │          │
│  │  • Storage     │  │  • Monitoring  │          │
│  └────────────────┘  └────────────────┘          │
└────────────────────────────────────────────────────┘
        │                      │
        ▼                      ▼
┌────────────────────────────────────────────────────┐
│              Processing Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Preprocess│ │ Detection│ │Classifier│          │
│  │  Module  │ │  Module  │ │  Module  │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐                       │
│  │Validation│ │  Output  │                       │
│  │  Module  │ │  Module  │                       │
│  └──────────┘ └──────────┘                       │
└────────────────────────────────────────────────────┘
        │                      │
        ▼                      ▼
┌────────────────────────────────────────────────────┐
│                Model Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  YOLOv8  │ │ ResNet50 │ │EfficientN│          │
│  │  (ONNX)  │ │  (ONNX)  │ │  (ONNX)  │          │
│  └──────────┘ └──────────┘ └──────────┘          │
└────────────────────────────────────────────────────┘
```

### 3.3 Data Flow

```
Image Upload
    ↓
[Validate Format/Size]
    ↓
[Generate Request ID]
    ↓
[Store Image (S3/MinIO)]
    ↓
[Enqueue Processing Task]
    ↓
[Return Request ID to Client]

--- ASYNC PROCESSING ---

[Dequeue Task]
    ↓
[Load Image]
    ↓
[Preprocessing Pipeline]
    ↓
[Board Detection Ensemble]
    ↓
[Extract 64 Squares]
    ↓
[Parallel Classification]
    │
    ├─> [YOLOv8 Predict]    ─┐
    ├─> [ResNet Predict]    ─┼─> [Weighted Vote] ─> [Square Prediction]
    └─> [EfficientNet Predict]┘
    ↓
[Aggregate 64 Predictions]
    ↓
[Chess Validation]
    ↓
[Generate FEN]
    ↓
[Render Annotated Image]
    ↓
[Store Results]
    ↓
[Update Status: Complete]
```

---

## 4. Data Pipeline

### 4.1 Dataset Composition

| Source | Quantity | Split | Purpose |
|--------|----------|-------|---------|
| Roboflow Public | 15,000 | 70/15/15 | Real photos |
| Kaggle Chess | 10,000 | 70/15/15 | Tournament photos |
| Synthetic (Blender) | 50,000 | 80/10/10 | Variation coverage |
| Manual Collection | 5,000 | 70/15/15 | Edge cases |
| **Total** | **80,000** | **75/12.5/12.5** | **Training/Val/Test** |

### 4.2 Data Augmentation

#### Training Time
- Random rotation: ±15°
- Random brightness: ±30%
- Random contrast: ±20%
- Random blur: Gaussian σ=0-2
- Random noise: σ=0-10
- Perspective transform: ±10°
- Horizontal flip (for data augmentation, not inference)

#### Test Time (TTA)
- Original
- Rotate 90°/270° (if needed)
- Brightness +10%/-10%
- Contrast +15%/-15%
- Sharpen filter

### 4.3 Labeling Format

```python
# Square-level annotation
{
    "image_id": "img_00123.jpg",
    "board_corners": [
        {"x": 120, "y": 80},   # top-left
        {"x": 520, "y": 85},   # top-right
        {"x": 515, "y": 485},  # bottom-right
        {"x": 125, "y": 480}   # bottom-left
    ],
    "squares": [
        {
            "square": "a1",
            "piece": "wr",  # white rook
            "bbox": {"x": 125, "y": 420, "w": 50, "h": 60}
        },
        {
            "square": "e4",
            "piece": null,  # empty
            "bbox": {"x": 320, "y": 280, "w": 50, "h": 60}
        }
        // ... 62 more squares
    ],
    "metadata": {
        "board_type": "wooden",
        "lighting": "natural",
        "angle": "overhead",
        "quality": "high"
    }
}
```

---

## 5. Model Specifications

### 5.1 Board Detection Models

#### 5.1.1 Hough Lines + RANSAC
```python
# Traditional CV approach
params = {
    "canny_low": 50,
    "canny_high": 150,
    "hough_threshold": 100,
    "min_line_length": 100,
    "max_line_gap": 10,
    "ransac_threshold": 10,
    "ransac_iterations": 1000
}
```

#### 5.1.2 Neural Chessboard (CNN)
```python
# Based on neural-chessboard paper
architecture = {
    "input": (224, 224, 3),
    "backbone": "MobileNetV2",
    "output": "64 corner coordinates",
    "loss": "MSE + geometric consistency",
    "pretrained": "ImageNet"
}
```

#### 5.1.3 Template Matching
```python
# Multi-scale template matching
params = {
    "templates": ["empty_board_1.png", "empty_board_2.png"],
    "scales": [0.5, 0.75, 1.0, 1.25, 1.5],
    "threshold": 0.8
}
```

### 5.2 Piece Classification Models

#### 5.2.1 YOLOv8
```yaml
model:
  name: yolov8m  # Medium variant
  pretrained: yolov8m.pt
  input_size: 640
  classes: 13  # empty + 12 piece types
  anchor_free: true

training:
  epochs: 100
  batch_size: 16
  optimizer: AdamW
  lr: 0.001
  weight_decay: 0.0005
  augmentation: albumentations

inference:
  conf_threshold: 0.25
  iou_threshold: 0.45
  nms: true
  tta: true  # Test-time augmentation
```

#### 5.2.2 ResNet50
```yaml
model:
  name: ResNet50
  pretrained: ImageNet
  input_size: 224
  classes: 13
  dropout: 0.5

modifications:
  - Replace final FC layer
  - Add global average pooling
  - Freeze first 3 blocks (transfer learning)

training:
  epochs: 50
  batch_size: 32
  optimizer: SGD
  lr: 0.01
  momentum: 0.9
  scheduler: CosineAnnealingLR

inference:
  tta_transforms: 8  # Including rotations
```

#### 5.2.3 EfficientNet-B4
```yaml
model:
  name: EfficientNet-B4
  pretrained: ImageNet
  input_size: 380
  classes: 13
  dropout: 0.4

training:
  epochs: 60
  batch_size: 16
  optimizer: AdamW
  lr: 0.001
  scheduler: ReduceLROnPlateau

inference:
  tta: true
  ensemble_weight: 0.25  # Lower than YOLO/ResNet
```

### 5.3 Ensemble Strategy

```python
# Weighted voting
class EnsembleClassifier:
    def __init__(self):
        self.models = {
            "yolov8": {"model": YOLOv8(), "weight": 0.40},
            "resnet50": {"model": ResNet50(), "weight": 0.35},
            "efficientnet": {"model": EfficientNet(), "weight": 0.25}
        }

    def predict(self, square_image):
        predictions = []

        for name, config in self.models.items():
            pred = config["model"].predict(square_image)
            predictions.append({
                "class": pred.class_id,
                "confidence": pred.confidence,
                "weight": config["weight"]
            })

        # Weighted soft voting
        final = self._weighted_vote(predictions)

        # Re-classify if low confidence
        if final["confidence"] < 0.85:
            final = self._reprocess_with_context(square_image)

        return final

    def _weighted_vote(self, predictions):
        # Compute weighted average of class probabilities
        pass

    def _reprocess_with_context(self, square_image):
        # Use larger crop including neighboring squares
        pass
```

---

## 6. API Specification

### 6.1 Endpoints

#### 6.1.1 POST /api/scan

Upload and process chess board image.

**Request**:
```http
POST /api/scan
Content-Type: multipart/form-data

{
  "image": <binary>,
  "options": {
    "confidence_threshold": 0.85,
    "enable_validation": true,
    "return_annotated": true,
    "tta_enabled": true
  }
}
```

**Response** (200 OK):
```json
{
  "request_id": "uuid-123-456",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "overall_confidence": 0.94,
  "processing_time_ms": 8234,
  "validation": {
    "is_valid": true,
    "errors": []
  },
  "squares": [
    {
      "square": "a1",
      "piece": "wr",
      "confidence": 0.98,
      "needs_review": false,
      "bbox": {"x": 10, "y": 10, "w": 50, "h": 50}
    },
    // ... 63 more squares
  ],
  "annotated_image": "data:image/png;base64,iVBORw0KG...",
  "metadata": {
    "image_size": [1024, 768],
    "board_detected": true,
    "detection_confidence": 0.99,
    "models_used": ["yolov8", "resnet50", "efficientnet"]
  }
}
```

**Error Responses**:
- 400: Invalid image format
- 413: Image too large (>10MB)
- 422: Board not detected in image
- 500: Processing error

#### 6.1.2 GET /api/scan/{request_id}

Get processing status and results.

**Response** (200 OK):
```json
{
  "request_id": "uuid-123-456",
  "status": "completed",  // "pending", "processing", "completed", "failed"
  "progress": 100,  // 0-100
  "result": { /* same as POST /api/scan response */ },
  "error": null
}
```

#### 6.1.3 POST /api/scan/batch

Process multiple images in batch.

**Request**:
```json
{
  "images": ["base64_1", "base64_2", ...],
  "options": { /* same as single scan */ }
}
```

**Response** (202 Accepted):
```json
{
  "batch_id": "batch-uuid-789",
  "request_ids": ["uuid-1", "uuid-2", ...],
  "status_url": "/api/scan/batch/batch-uuid-789"
}
```

#### 6.1.4 GET /api/health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "models_loaded": true,
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

### 6.2 Rate Limiting

- Anonymous: 10 requests/hour
- Authenticated: 100 requests/hour
- Batch: 5 batches/hour (max 20 images per batch)

### 6.3 Authentication

Optional for v1.0 (public service).
For v1.1: API key in header `X-API-Key`.

---

## 7. Frontend Integration

> **Important**: Chess Vision is a **backend-only service**. The user interface is provided by the [chess-ai](../chess-ai) project.

### 7.1 Architecture

```
┌─────────────────────────────────────────────────┐
│         Chess AI Frontend (Port 8000)           │
│  ┌───────────────────────────────────────────┐  │
│  │  Main App                                 │  │
│  │  • Play vs AI                             │  │
│  │  • Analysis                               │  │
│  │  • Scan Board from Photo (NEW)            │  │
│  └───────────────┬───────────────────────────┘  │
└──────────────────┼──────────────────────────────┘
                   │ HTTP POST
                   ▼
┌─────────────────────────────────────────────────┐
│      Chess Vision Backend (Port 8001)           │
│  ┌───────────────────────────────────────────┐  │
│  │  API Endpoint: POST /api/scan             │  │
│  │  • Preprocessing                          │  │
│  │  • Board detection                        │  │
│  │  • Piece classification                   │  │
│  │  • Validation                             │  │
│  └───────────────┬───────────────────────────┘  │
└──────────────────┼──────────────────────────────┘
                   │ JSON Response
                   ▼
        { fen, confidence, squares, ... }
```

### 7.2 Integration Flow

1. **User uploads photo** in chess-ai frontend
2. **chess-ai calls** `http://chess-vision:8001/api/scan`
3. **chess-vision processes** image (≤10s)
4. **Returns** FEN + confidence scores
5. **chess-ai displays**:
   - Recognized position on chessboard
   - FEN string (copyable)
   - Confidence map per square
   - Validation errors (if any)
6. **User can**:
   - Play from this position
   - Analyze with Claude + LC0
   - Edit position manually

### 7.3 Chess AI Frontend Requirements

The chess-ai frontend must implement:

#### 7.3.1 New Tab/Section: "Scan Board"

```
┌──────────────────────────────────────────┐
│  [Play vs AI] [Analysis] [Scan Board]   │ ← New tab
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│            Scan Board from Photo         │
├──────────────────────────────────────────┤
│   ┌────────────────────────────────┐    │
│   │  📷 Drop image or click        │    │
│   │     to upload                  │    │
│   │  (JPEG/PNG, max 10MB)          │    │
│   └────────────────────────────────┘    │
│                                          │
│   Options:                               │
│   ☑ Enable validation                   │
│   Confidence threshold: [0.85] ─────     │
│                                          │
│   [  Scan Board  ]                       │
└──────────────────────────────────────────┘
```

#### 7.3.2 Results Display

After scanning, show in chess-ai UI:

```javascript
// API call from chess-ai frontend
const scanBoard = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('options', JSON.stringify({
    confidence_threshold: 0.85,
    enable_validation: true
  }));

  const response = await fetch('http://chess-vision:8001/api/scan', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();

  // Display on chessboard
  window.chessBoard.setPosition(result.fen);

  // Show confidence details
  displayConfidenceMap(result.squares);

  // Show validation errors
  if (result.validation.errors.length > 0) {
    showWarning(result.validation.errors);
  }

  return result;
};
```

#### 7.3.3 UI Components to Add

**File**: `chess-ai/frontend/index.html`
```html
<!-- Add new tab -->
<div class="tabs">
  <button id="tab-play">Play vs AI</button>
  <button id="tab-analysis">Analysis</button>
  <button id="tab-scan">Scan Board</button> <!-- NEW -->
</div>

<!-- Scan panel -->
<div id="scan-panel" class="tab-content">
  <div class="upload-area">
    <input type="file" id="board-image" accept="image/*">
    <div class="drop-zone">
      <p>📷 Drop chess board photo here</p>
    </div>
  </div>

  <div class="scan-options">
    <label>
      <input type="checkbox" id="enable-validation" checked>
      Enable position validation
    </label>
    <label>
      Confidence threshold:
      <input type="range" id="confidence-threshold"
             min="0.5" max="1.0" step="0.05" value="0.85">
      <span id="threshold-value">0.85</span>
    </label>
  </div>

  <button id="btn-scan">Scan Board</button>

  <!-- Results -->
  <div id="scan-results" style="display:none;">
    <div class="fen-display">
      <strong>FEN:</strong>
      <code id="scanned-fen"></code>
      <button id="copy-fen">Copy</button>
    </div>

    <div class="confidence-display">
      <strong>Confidence:</strong>
      <span id="overall-confidence"></span>
      <div class="confidence-bar"></div>
    </div>

    <div class="square-details">
      <h4>Square Details</h4>
      <div id="square-list"></div>
    </div>

    <div class="actions">
      <button id="play-from-position">Play from Here</button>
      <button id="analyze-position">Analyze</button>
    </div>
  </div>
</div>
```

**File**: `chess-ai/frontend/js/scan.js` (new file)
```javascript
class BoardScanner {
  constructor() {
    this.apiUrl = 'http://localhost:8001/api/scan';
  }

  async scanImage(imageFile, options = {}) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('options', JSON.stringify({
      confidence_threshold: options.threshold || 0.85,
      enable_validation: options.validate !== false,
      return_annotated: true,
      tta_enabled: true
    }));

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Scan failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Board scan error:', error);
      throw error;
    }
  }

  displayResults(result) {
    // Update chessboard
    window.chessBoard.setPosition(result.fen);

    // Show FEN
    $('#scanned-fen').text(result.fen);

    // Show confidence
    $('#overall-confidence').text(
      `${(result.overall_confidence * 100).toFixed(1)}%`
    );

    // Show square details
    this.renderSquareDetails(result.squares);

    // Show validation errors
    if (!result.validation.is_valid) {
      this.showValidationErrors(result.validation.errors);
    }

    $('#scan-results').show();
  }

  renderSquareDetails(squares) {
    const $list = $('#square-list');
    $list.empty();

    // Show only low confidence or problematic squares
    const problematic = squares.filter(s =>
      s.confidence < 0.85 || s.needs_review
    );

    if (problematic.length === 0) {
      $list.html('<p class="success">All squares detected with high confidence!</p>');
      return;
    }

    problematic.forEach(square => {
      const confClass = square.confidence >= 0.7 ? 'medium' : 'low';
      $list.append(`
        <div class="square-item confidence-${confClass}">
          <strong>${square.square}</strong>:
          ${square.piece || 'empty'}
          (${(square.confidence * 100).toFixed(1)}%)
          ${square.needs_review ? '⚠️' : ''}
        </div>
      `);
    });
  }
}

// Initialize
const scanner = new BoardScanner();

$('#btn-scan').on('click', async () => {
  const file = $('#board-image')[0].files[0];
  if (!file) {
    alert('Please select an image');
    return;
  }

  const options = {
    threshold: parseFloat($('#confidence-threshold').val()),
    validate: $('#enable-validation').is(':checked')
  };

  try {
    const result = await scanner.scanImage(file, options);
    scanner.displayResults(result);
  } catch (error) {
    alert(`Scan failed: ${error.message}`);
  }
});
```

### 7.4 Service Discovery

In production, chess-ai should discover chess-vision via Consul:

```javascript
// chess-ai/frontend/js/config.js
const CHESS_VISION_URL =
  process.env.NODE_ENV === 'production'
    ? 'http://chess-vision.service.consul:8001'
    : 'http://localhost:8001';
```

### 7.5 Error Handling

Chess-ai frontend must handle:

1. **Board not detected** (422 response)
   - Show: "Could not detect chessboard in image"
   - Suggest: Better lighting, different angle

2. **Invalid position** (validation errors)
   - Show: Specific errors (e.g., "Missing white king")
   - Allow: Manual correction of low-confidence squares

3. **Timeout** (>30s processing)
   - Show: Progress indicator
   - Allow: Cancel request

4. **Service unavailable** (503)
   - Show: "Board scanner temporarily unavailable"
   - Fallback: Manual position entry

---

## 8. Testing Strategy

### 8.1 Unit Tests

| Component | Coverage Target | Key Tests |
|-----------|----------------|-----------|
| Preprocessing | 90% | Image normalization, augmentation |
| Board Detection | 95% | Corner detection, grid extraction |
| Classification | 95% | Model inference, ensemble voting |
| Validation | 100% | Chess rules, FEN conversion |
| API Routes | 90% | Request validation, error handling |

### 8.2 Integration Tests

- End-to-end pipeline with sample images
- API endpoint tests (status codes, response format)
- Database/storage integration
- Model loading and inference

### 8.3 Performance Tests

```python
# Load testing
- 10 concurrent requests for 5 minutes
- Expected: <10s P95 latency
- Expected: 0% error rate

# Stress testing
- 50 concurrent requests until failure
- Measure: max throughput, breaking point

# Accuracy testing
- Test set: 1000 labeled images
- Target: 95%+ exact FEN match
- Measure: per-square accuracy, board detection rate
```

### 8.4 Test Datasets

| Dataset | Size | Purpose |
|---------|------|---------|
| Golden set | 100 images | Hand-verified, regression testing |
| Edge cases | 50 images | Poor lighting, extreme angles, occlusions |
| Board styles | 200 images | Different boards/pieces, generalization |
| Real world | 500 images | User-submitted, production-like |

---

## 9. Deployment

### 9.1 Containerization

```dockerfile
# Dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Install dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy models
COPY models/ /app/models/

# Copy application
COPY src/ /app/src/
COPY api/ /app/api/

WORKDIR /app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.2 Nomad Job Spec

```hcl
job "chess-vision" {
  datacenters = ["dc1"]
  type = "service"

  group "api" {
    count = 2

    network {
      port "http" {
        to = 8000
      }
    }

    task "chess-vision-api" {
      driver = "docker"

      config {
        image = "registry.seasgroup.io/chess-vision:latest"
        ports = ["http"]

        mount {
          type = "bind"
          source = "/opt/models"
          target = "/app/models"
          readonly = true
        }
      }

      resources {
        cpu    = 2000
        memory = 4096
      }

      service {
        name = "chess-vision"
        port = "http"

        tags = [
          "traefik.enable=true",
          "traefik.http.routers.chess-vision.rule=Host(`chess-vision.seasgroup.io`)",
        ]

        check {
          type     = "http"
          path     = "/api/health"
          interval = "10s"
          timeout  = "2s"
        }
      }
    }
  }
}
```

### 9.3 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Chess Vision

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/ --cov

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t chess-vision:${{ github.sha }} .

      - name: Push to registry
        run: docker push registry.seasgroup.io/chess-vision:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Nomad
        run: |
          nomad job run \
            -var="image_tag=${{ github.sha }}" \
            chess-vision.nomad.hcl
```

---

## 10. Performance Targets

### 10.1 Accuracy Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Overall FEN Accuracy | ≥95% | Exact match on 1000-image test set |
| Board Detection Rate | ≥99% | IoU > 0.9 with ground truth |
| Piece Classification | ≥98% | Per-square accuracy (64 squares × 1000 images) |
| High Confidence Rate | ≥80% | % of squares with conf > 0.9 |
| False Positive Rate | ≤2% | Incorrect pieces with high confidence |

### 10.2 Performance Metrics

| Metric | Target | P50 | P95 | P99 |
|--------|--------|-----|-----|-----|
| Processing Time | ≤10s | 6s | 9s | 10s |
| API Response Time | ≤500ms | 200ms | 400ms | 500ms |
| Model Inference (per square) | ≤50ms | 30ms | 45ms | 50ms |
| Throughput | ≥10 req/min | - | - | - |

### 10.3 Resource Metrics

| Resource | Limit | Typical Usage |
|----------|-------|---------------|
| CPU | 2 cores | 1.5 cores (75%) |
| RAM | 4GB | 3GB (75%) |
| GPU VRAM (optional) | 8GB | 6GB (75%) |
| Disk | 10GB | 5GB (models + cache) |
| Network | 100Mbps | 20Mbps |

### 10.4 Monitoring & Alerts

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    severity: critical

  - name: SlowProcessing
    condition: p95_latency > 12s
    severity: warning

  - name: LowAccuracy
    condition: daily_accuracy < 93%
    severity: critical

  - name: ModelNotLoaded
    condition: models_loaded == false
    severity: critical
```

---

## 11. Future Enhancements

### v1.1 (Q2 2026)
- Human-in-the-loop review interface
- Active learning pipeline
- Model versioning & A/B testing
- Prometheus metrics

### v1.2 (Q3 2026)
- Multi-board support in single image
- Video/webcam real-time mode
- Mobile app (iOS/Android)

### v2.0 (Q4 2026)
- Custom board/piece style training
- Move sequence detection from video
- Integration with Chess AI for position analysis

---

## 12. Open Questions

1. **Dataset licensing**: Can we redistribute augmented versions of public datasets?
2. **Model hosting**: Self-host or use model registry (HuggingFace)?
3. **Storage**: MinIO for images or S3-compatible service?
4. **GPU deployment**: Run on GPU nodes or CPU-only for cost?
5. **User accounts**: Anonymous only or user authentication for v1.0?

---

## 13. References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Neural Chessboard Paper](https://arxiv.org/pdf/1708.03898)
- [Chess Vision - Medium](https://medium.com/@daylenyang/building-chess-id-99afa57326cd)
- [Roboflow Chess Dataset](https://universe.roboflow.com/chess)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/)

---

**Document Status**: ✅ Ready for Review
**Next Steps**: Team review → Approval → Implementation kickoff
