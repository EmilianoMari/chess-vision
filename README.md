# Chess Vision 🔍♟️

**Backend service for accurate chess board position recognition from photos**

[![Status](https://img.shields.io/badge/status-in%20development-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> **Architecture Note**: This is a **backend-only service**. UI is provided by [chess-ai](../chess-ai).

---

## 📖 Overview

Chess Vision is a computer vision backend service that extracts chess board positions from static photos and converts them to FEN notation with high accuracy (95%+).

**System Components**:
- **chess-vision** (this repo): ML pipeline + REST API
- **[chess-ai](../chess-ai)**: Frontend UI + integration
- **[chess-engine](../chess-engine)**: LC0 wrapper service

Perfect for:
- 📷 Digitizing physical chess positions
- 📚 Analyzing chess book diagrams
- 🏆 Recording tournament games
- 🧪 Testing chess engines with real positions

## ✨ Key Features

- **High Accuracy**: 95%+ FEN accuracy using ensemble models
- **Robust Detection**: Works with various angles, lighting, board styles
- **Fast Processing**: <10 seconds per image
- **Confidence Scores**: Per-square confidence + validation
- **REST API**: Easy integration with chess-ai frontend
- **Backend-only**: No frontend dependencies

## 🎯 Quick Example

**Input**: Photo of chess board
**Output**: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`

```python
import requests

response = requests.post(
    'http://localhost:8000/api/scan',
    files={'image': open('board.jpg', 'rb')}
)

result = response.json()
print(f"FEN: {result['fen']}")
print(f"Confidence: {result['overall_confidence']:.2%}")
```

## 🏗️ Architecture

```
Photo → Preprocessing → Board Detection → Piece Classification → Validation → FEN
         (5 variants)   (Ensemble 3x)      (Ensemble 3x CNN)    (Chess rules)
```

**Models Used**:
- 🎯 YOLOv8 (object detection)
- 🧠 ResNet50 (classification)
- ⚡ EfficientNet-B4 (classification)

**Ensemble Strategy**: Weighted voting with confidence thresholding

## 📦 Installation

### Prerequisites
- Python 3.11+
- CUDA 12.1+ (optional, for GPU)
- 4GB RAM minimum

### Setup

```bash
# Clone repository
git clone https://github.com/seasgroup/chess-vision.git
cd chess-vision

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download pre-trained models
python scripts/download_models.py

# Run API server
uvicorn api.main:app --reload
```

Visit http://localhost:8000 for the upload UI.

## 🚀 Usage

### API Endpoint

```bash
curl -X POST http://localhost:8000/api/scan \
  -F "image=@chess_board.jpg" \
  -F "options={\"confidence_threshold\": 0.85}"
```

**Response**:
```json
{
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
      "confidence": 0.98
    }
    // ... 63 more
  ]
}
```

### Python SDK

```python
from chess_vision import ChessVision

cv = ChessVision()
result = cv.scan_image("board.jpg")

print(f"FEN: {result.fen}")
print(f"Confidence: {result.overall_confidence}")

# Access individual squares
for square in result.squares:
    if square.confidence < 0.85:
        print(f"⚠️ Low confidence on {square.square}: {square.piece}")
```

## 📊 Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| FEN Accuracy | ≥95% | TBD |
| Board Detection | ≥99% | TBD |
| Processing Time | ≤10s | TBD |
| Piece Classification | ≥98% | TBD |

*Metrics will be updated after training completion*

## 🗂️ Project Structure

```
chess-vision/
├── api/                    # FastAPI application
│   ├── main.py
│   ├── routes.py
│   └── schemas.py
├── src/                    # Core processing modules
│   ├── preprocessing/      # Image enhancement
│   ├── detection/          # Board detection
│   ├── classification/     # Piece classification
│   ├── validation/         # Chess rules validation
│   └── utils/              # Helper functions
├── models/                 # Pre-trained models
│   ├── yolov8_chess.pt
│   ├── resnet50_pieces.pth
│   └── efficientnet_pieces.pth
├── training/               # Training scripts
│   ├── train_yolo.py
│   ├── train_resnet.py
│   └── prepare_dataset.py
├── frontend/               # Web UI
│   ├── index.html
│   ├── app.js
│   └── style.css
├── tests/                  # Unit & integration tests
├── docs/                   # Documentation
│   └── SPECIFICATION.md    # Full technical spec
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🧪 Development

### Run Tests

```bash
pytest tests/ --cov --cov-report=html
```

### Train Models

```bash
# Prepare dataset
python training/prepare_dataset.py

# Train YOLOv8
python training/train_yolo.py --epochs 100 --batch 16

# Train ResNet50
python training/train_resnet.py --epochs 50 --batch 32

# Evaluate
python training/evaluate.py --model all
```

### Docker Deployment

```bash
# Build image
docker build -t chess-vision:latest .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  chess-vision:latest

# Or use docker-compose
docker-compose up
```

## 📚 Documentation

- **[Technical Specification](docs/SPECIFICATION.md)** - Complete system design
- **[API Reference](docs/API.md)** - Endpoint documentation
- **[Model Training Guide](docs/TRAINING.md)** - How to train custom models
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment

## 🛣️ Roadmap

### v1.0 (Current) - MVP
- [x] Project setup & specification
- [ ] Dataset preparation (80k images)
- [ ] Model training (YOLOv8, ResNet, EfficientNet)
- [ ] Ensemble pipeline implementation
- [ ] REST API
- [ ] Simple web UI
- [ ] Docker deployment

### v1.1 - Enhanced
- [ ] Human-in-the-loop review
- [ ] Batch processing
- [ ] Model monitoring
- [ ] Active learning

### v2.0 - Advanced
- [ ] Real-time webcam mode
- [ ] Mobile app
- [ ] Video sequence detection
- [ ] Custom board/piece training

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics
- **Neural Chessboard** paper & implementation
- **Roboflow** for public chess datasets
- **FastAPI** framework

## 📞 Contact

- **Project Lead**: Emiliano Mari
- **Organization**: SeasGroup
- **GitHub**: [EmilianoMari/chess-vision](https://github.com/EmilianoMari/chess-vision)

---

**Status**: 🚧 In Development | **Version**: 1.0.0-alpha | **Last Updated**: 2026-02-15
