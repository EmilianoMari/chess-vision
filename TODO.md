# Chess Vision - Development Roadmap

**Last Updated**: 2026-02-15
**Current Phase**: Phase 1 - Setup & Dataset

---

## 🎯 Milestone Overview

```
Phase 1: Setup & Dataset      [░░░░░░░░░░] 0%   (Week 1)
Phase 2: Model Training        [░░░░░░░░░░] 0%   (Week 2-3)
Phase 3: Pipeline Integration  [░░░░░░░░░░] 0%   (Week 3-4)
Phase 4: API & Frontend        [░░░░░░░░░░] 0%   (Week 4)
Phase 5: Testing & Deploy      [░░░░░░░░░░] 0%   (Week 5)
```

---

## Phase 1: Project Setup & Dataset Preparation

### Week 1 - Day 1-2: Project Infrastructure

- [x] Create project directory structure
- [x] Write SPECIFICATION.md (complete technical spec)
- [x] Write README.md (project overview)
- [x] Write ARCHITECTURE.md (system design)
- [x] Write TODO.md (this file)
- [ ] Initialize git repository
- [ ] Setup .gitignore (models/, data/, *.pyc, __pycache__, .env)
- [ ] Create requirements.txt with dependencies
- [ ] Setup virtual environment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Setup pre-commit hooks (black, isort, flake8)

**Dependencies to add to requirements.txt**:
```
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
python-multipart==0.0.6

# Computer Vision
opencv-python==4.9.0.80
numpy==1.26.3
pillow==10.2.0

# Deep Learning
torch==2.1.2
torchvision==0.16.2
onnxruntime==1.16.3
ultralytics==8.1.0  # YOLOv8

# Chess
python-chess==1.999

# Storage & Cache
redis==5.0.1
boto3==1.34.34  # MinIO/S3

# Utilities
loguru==0.7.2
tqdm==4.66.1
scikit-image==0.22.0
albumentations==1.3.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Monitoring
prometheus-client==0.19.0
```

### Week 1 - Day 3-4: Dataset Collection

- [ ] Download Roboflow Chess Dataset
  - [ ] Sign up for Roboflow account
  - [ ] Download dataset (15k images)
  - [ ] Extract to `data/raw/roboflow/`
  - [ ] Verify annotations format

- [ ] Download Kaggle Chess Dataset
  - [ ] Setup Kaggle API credentials
  - [ ] Download dataset (10k images)
  - [ ] Extract to `data/raw/kaggle/`
  - [ ] Convert annotations to standard format

- [ ] Setup Synthetic Data Generation
  - [ ] Research chess piece 3D models (Blender/Unity)
  - [ ] Create script to generate varied boards:
    - Different board styles (wooden, marble, digital)
    - Random piece positions
    - Lighting variations (daylight, tungsten, LED)
    - Camera angles (overhead, 15°, 30°, 45°)
    - Background textures
  - [ ] Generate 50k synthetic images
  - [ ] Store in `data/synthetic/`

**Script**: `scripts/generate_synthetic_dataset.py`
```python
import bpy  # Blender Python API
import random

def generate_board(
    pieces_layout: str,  # FEN
    board_style: str,
    lighting: str,
    camera_angle: float,
    output_path: str
):
    # Setup scene
    # Position pieces
    # Configure lighting
    # Render
    # Save with annotations
    pass
```

### Week 1 - Day 5-7: Dataset Preparation

- [ ] Create unified annotation format
  ```json
  {
    "image_id": "...",
    "image_path": "...",
    "board_corners": [...],
    "squares": [
      {"square": "a1", "piece": "wr", "bbox": {...}},
      ...
    ]
  }
  ```

- [ ] Implement dataset preprocessing pipeline
  - [ ] Resize images to standard size (640x640)
  - [ ] Normalize pixel values
  - [ ] Validate annotations
  - [ ] Remove corrupted/invalid images

- [ ] Split dataset: Train/Val/Test (75/12.5/12.5)
  - [ ] Stratified split (ensure balanced piece distribution)
  - [ ] Save split info to `data/splits.json`

- [ ] Create data loaders (PyTorch)
  - [ ] Training data loader with augmentation
  - [ ] Validation data loader (no aug)
  - [ ] Test data loader (no aug)

**Scripts**:
- `scripts/download_datasets.py`
- `scripts/prepare_dataset.py`
- `scripts/validate_dataset.py`

**Acceptance Criteria**:
- ✅ 80k total images collected
- ✅ All annotations validated
- ✅ Train/Val/Test split created
- ✅ Data loaders tested

---

## Phase 2: Model Training

### Week 2 - Day 1-3: YOLOv8 Training

- [ ] Setup YOLOv8 training environment
  - [ ] Install Ultralytics package
  - [ ] Prepare dataset in YOLO format
  - [ ] Create `dataset.yaml` config

- [ ] Configure YOLOv8 hyperparameters
  ```yaml
  # training/configs/yolov8_config.yaml
  model: yolov8m.pt
  data: dataset.yaml
  epochs: 100
  batch: 16
  imgsz: 640
  optimizer: AdamW
  lr0: 0.001
  ```

- [ ] Train YOLOv8 model
  - [ ] Run training script
  - [ ] Monitor training (TensorBoard)
  - [ ] Save checkpoints every 10 epochs
  - [ ] Early stopping if no improvement (patience=15)

- [ ] Evaluate YOLOv8
  - [ ] mAP@0.5
  - [ ] mAP@0.5:0.95
  - [ ] Per-class accuracy
  - [ ] Confusion matrix

- [ ] Export to ONNX
  ```python
  model.export(format="onnx", dynamic=True)
  ```

**Script**: `training/train_yolo.py`

**Target Metrics**:
- mAP@0.5: ≥95%
- Inference time: <50ms per square

### Week 2 - Day 4-5: ResNet50 Training

- [ ] Implement ResNet50 classifier
  - [ ] Load pretrained ImageNet weights
  - [ ] Modify final layer (13 classes)
  - [ ] Freeze first 3 blocks

- [ ] Configure training
  ```python
  # training/configs/resnet_config.py
  config = {
      "model": "resnet50",
      "pretrained": True,
      "epochs": 50,
      "batch_size": 32,
      "optimizer": "SGD",
      "lr": 0.01,
      "momentum": 0.9,
      "scheduler": "CosineAnnealingLR"
  }
  ```

- [ ] Train ResNet50
  - [ ] Data augmentation pipeline
  - [ ] Learning rate scheduling
  - [ ] Save best model (val accuracy)

- [ ] Evaluate ResNet50
  - [ ] Test set accuracy
  - [ ] Per-class metrics
  - [ ] ROC curves

- [ ] Export to ONNX

**Script**: `training/train_resnet.py`

**Target Metrics**:
- Test accuracy: ≥98%
- Inference time: <40ms per square

### Week 2 - Day 6-7: EfficientNet-B4 Training

- [ ] Implement EfficientNet-B4 classifier
  - [ ] Load pretrained weights
  - [ ] Modify head (13 classes)

- [ ] Train EfficientNet
  - [ ] Similar config to ResNet
  - [ ] Larger input size (380x380)

- [ ] Evaluate & Export

**Script**: `training/train_efficientnet.py`

**Target Metrics**:
- Test accuracy: ≥97%
- Inference time: <60ms per square

### Week 3 - Day 1-2: Model Ensemble & Evaluation

- [ ] Implement ensemble voting logic
  - [ ] Weighted soft voting
  - [ ] Confidence thresholding
  - [ ] Test-time augmentation

- [ ] Evaluate ensemble
  - [ ] Compare vs individual models
  - [ ] Ablation studies (remove each model)
  - [ ] Optimal weight tuning

**Script**: `training/evaluate_ensemble.py`

**Target Metrics**:
- Ensemble accuracy: ≥99%
- Per-square confidence: >0.85 for 80%+ squares

---

## Phase 3: Pipeline Integration

### Week 3 - Day 3-4: Preprocessing Module

- [ ] Implement preprocessing pipeline
  ```
  src/preprocessing/
  ├── __init__.py
  ├── image_enhancer.py
  ├── perspective.py
  └── variants.py
  ```

- [ ] Create 5 variants generator
  - [ ] Original normalization
  - [ ] Contrast enhancement (CLAHE)
  - [ ] Denoising (Gaussian)
  - [ ] Sharpening (Unsharp mask)
  - [ ] Auto perspective correction

- [ ] Unit tests for preprocessing

### Week 3 - Day 5-6: Board Detection Module

- [ ] Implement Hough Lines detector
  ```python
  # src/detection/hough_detector.py
  class HoughLinesDetector:
      def detect(self, image) -> GridCoordinates:
          # Canny → Hough → RANSAC
          pass
  ```

- [ ] Implement Neural Chessboard detector
  - [ ] Load pre-trained model
  - [ ] Inference pipeline

- [ ] Implement Template Matching detector
  - [ ] Multi-scale template matching
  - [ ] Multiple board templates

- [ ] Implement ensemble voting
  ```python
  # src/detection/board_detector.py
  class BoardDetectionEnsemble:
      def detect(self, images) -> GridCoordinates:
          pass
  ```

- [ ] Unit tests for detection

### Week 3 - Day 7 / Week 4 - Day 1: Classification Module

- [ ] Implement model loaders
  ```python
  # src/classification/yolo_classifier.py
  class YOLOv8Classifier:
      def __init__(self, model_path):
          self.session = ort.InferenceSession(model_path)

      def predict(self, image) -> Prediction:
          pass
  ```

- [ ] Implement ensemble classifier
  - [ ] Weighted voting
  - [ ] TTA logic
  - [ ] Confidence filtering

- [ ] Unit tests for classification

### Week 4 - Day 2: Validation Module

- [ ] Implement chess rule validator
  ```python
  # src/validation/chess_rules.py
  class ChessValidator:
      def validate(self, predictions) -> ValidationResult:
          # 1 king per color
          # Max 8 pawns per color
          # No pawns on rank 1/8
          # Total pieces ≤ 32
          pass
  ```

- [ ] Implement FEN converter
  ```python
  # src/utils/fen_converter.py
  def predictions_to_fen(predictions: list[SquarePrediction]) -> str:
      pass
  ```

- [ ] Unit tests for validation

### Week 4 - Day 3: End-to-End Pipeline

- [ ] Integrate all modules
  ```python
  # src/pipeline.py
  class ChessVisionPipeline:
      def __init__(self):
          self.preprocessor = Preprocessor()
          self.board_detector = BoardDetectionEnsemble()
          self.classifier = EnsembleClassifier()
          self.validator = ChessValidator()

      async def process(self, image) -> ScanResult:
          # Stage 1: Preprocessing
          # Stage 2: Board detection
          # Stage 3: Classification
          # Stage 4: Validation
          # Stage 5: Output
          pass
  ```

- [ ] Integration tests
  - [ ] Test with 100 golden images
  - [ ] Measure accuracy
  - [ ] Measure processing time

**Acceptance Criteria**:
- ✅ Pipeline processes image end-to-end
- ✅ Accuracy ≥95% on test set
- ✅ Processing time ≤10s per image

---

## Phase 4: API & Frontend Development

### Week 4 - Day 4: API Development

- [ ] Setup FastAPI application
  ```python
  # api/main.py
  from fastapi import FastAPI
  app = FastAPI(title="Chess Vision API")
  ```

- [ ] Implement endpoints
  - [ ] POST /api/scan
  - [ ] GET /api/scan/{request_id}
  - [ ] POST /api/scan/batch
  - [ ] GET /api/health

- [ ] Implement request validation
  ```python
  # api/schemas.py
  class ScanRequest(BaseModel):
      image: UploadFile
      options: ScanOptions
  ```

- [ ] Implement async processing
  - [ ] Redis queue for tasks
  - [ ] Background worker
  - [ ] Result caching

- [ ] Add rate limiting (10 req/hour anonymous)

- [ ] API documentation (auto-generated Swagger)

### Week 4 - Day 5: Frontend Development

- [ ] Create simple upload UI
  ```html
  <!-- frontend/index.html -->
  <div class="upload-area">
      <input type="file" id="image-upload">
      <button id="scan-btn">Scan Board</button>
  </div>
  <div class="results">
      <div id="fen-output"></div>
      <div id="annotated-image"></div>
      <div id="square-details"></div>
  </div>
  ```

- [ ] Implement JavaScript logic
  ```javascript
  // frontend/js/app.js
  async function scanBoard(imageFile) {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await fetch('/api/scan', {
          method: 'POST',
          body: formData
      });

      const result = await response.json();
      displayResults(result);
  }
  ```

- [ ] Add CSS styling
  - [ ] Responsive design
  - [ ] Loading states
  - [ ] Error messages

### Week 4 - Day 6-7: Integration & Polish

- [ ] Test API with frontend
- [ ] Handle edge cases
  - [ ] Invalid images
  - [ ] Board not detected
  - [ ] Low confidence squares
- [ ] Add loading indicators
- [ ] Add result visualization
  - [ ] Annotated image with bounding boxes
  - [ ] Confidence bars per square
  - [ ] Validation errors display

**Acceptance Criteria**:
- ✅ API endpoints working
- ✅ Frontend uploads and displays results
- ✅ Error handling implemented

---

## Phase 5: Testing & Deployment

### Week 5 - Day 1-2: Testing

- [ ] Write unit tests (coverage ≥90%)
  - [ ] Preprocessing tests
  - [ ] Detection tests
  - [ ] Classification tests
  - [ ] Validation tests
  - [ ] API tests

- [ ] Write integration tests
  - [ ] End-to-end pipeline test
  - [ ] API endpoint tests
  - [ ] Database integration tests

- [ ] Write performance tests
  - [ ] Load testing (10 concurrent users)
  - [ ] Stress testing (50 concurrent)
  - [ ] Latency measurement (P50, P95, P99)

- [ ] Run tests
  ```bash
  pytest tests/ --cov --cov-report=html
  ```

**Target Coverage**: ≥90%

### Week 5 - Day 3-4: Deployment Setup

- [ ] Build Docker image
  ```dockerfile
  FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
  # ... (see SPECIFICATION.md)
  ```

- [ ] Create Nomad job spec
  ```hcl
  job "chess-vision" {
    # ... (see SPECIFICATION.md)
  }
  ```

- [ ] Setup CI/CD pipeline
  ```yaml
  # .github/workflows/deploy.yml
  # Test → Build → Push → Deploy
  ```

- [ ] Configure monitoring
  - [ ] Prometheus metrics
  - [ ] Grafana dashboards
  - [ ] AlertManager rules

### Week 5 - Day 5: Production Deployment

- [ ] Deploy to Nomad cluster
  ```bash
  nomad job run chess-vision.nomad.hcl
  ```

- [ ] Verify health checks
- [ ] Test public endpoint
- [ ] Monitor metrics
- [ ] Load test production

### Week 5 - Day 6-7: Documentation & Handoff

- [ ] Update README with deployment info
- [ ] Write API documentation
- [ ] Write user guide
- [ ] Create demo video
- [ ] Write blog post

**Acceptance Criteria**:
- ✅ Service deployed and accessible
- ✅ All health checks passing
- ✅ Documentation complete

---

## Future Enhancements (Post v1.0)

### v1.1 - Human-in-the-Loop
- [ ] Build review interface for low confidence squares
- [ ] Implement feedback collection
- [ ] Active learning pipeline (retrain with corrections)

### v1.2 - Advanced Features
- [ ] Batch processing endpoint (multiple images)
- [ ] Real-time webcam mode
- [ ] Mobile app (React Native)

### v2.0 - Integration
- [ ] Integrate with Chess AI project
  - [ ] Upload board → Get analysis
  - [ ] Upload board → Play against AI from that position
- [ ] Support different board styles (custom training)
- [ ] Video sequence detection (detect moves over time)

---

## Current Sprint (Week 1)

**Goal**: Complete project setup and dataset preparation

**This Week**:
1. ✅ Create project structure
2. ✅ Write documentation (SPECIFICATION, README, ARCHITECTURE, TODO)
3. ⬜ Initialize git repo
4. ⬜ Setup dependencies
5. ⬜ Download datasets
6. ⬜ Generate synthetic data
7. ⬜ Prepare training splits

**Next Week**: Start model training

---

## Notes & Decisions

- **Decision 2026-02-15**: Use ONNX for model export (better compatibility, faster inference)
- **Decision 2026-02-15**: Prioritize accuracy over speed (10s budget allows ensemble)
- **Decision 2026-02-15**: Use MinIO for image storage (consistent with seas-infra)

---

## Blockers & Risks

| Issue | Impact | Mitigation | Status |
|-------|--------|------------|--------|
| Dataset quality | High | Manual review of sample images | 🟡 Monitor |
| Model convergence | Medium | Early stopping, LR scheduling | 🟢 OK |
| GPU availability | Medium | Can train on CPU (slower) | 🟢 OK |
| Deployment resources | Low | Start with CPU-only deployment | 🟢 OK |

---

**Progress**: 5/150 tasks completed (3%)
**ETA**: v1.0 target date: 2026-03-22 (5 weeks)
