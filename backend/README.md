# GestureFlow AI Backend

**Phase 1: Core Backend Foundation**

A modular Python backend built with FastAPI for the GestureFlow AI gesture controller application.

---

## Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core infrastructure
│   │   ├── config.py           # Pydantic Settings configuration
│   │   ├── logging_config.py   # Structured logging with rotation
│   │   └── lifecycle.py        # Startup/shutdown management
│   ├── api/                    # API layer
│   │   ├── router.py           # Central API router (v1)
│   │   └── routes/
│   │       ├── health.py       # GET /api/v1/health
│   │       └── status.py       # GET /api/v1/status
│   ├── schemas/                # Pydantic models
│   │   ├── common.py           # Base response/error schemas
│   │   └── status.py           # Status response with typed enums
│   ├── services/               # Business logic
│   │   └── application_service.py  # Core service with component tracking
│   └── exceptions/             # Error handling
│       └── handlers.py         # Global exception handlers
├── tests/                      # Automated tests
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── .gitignore                  # Git ignore rules
```

---

## Requirements

- **Python 3.11 or 3.12**
- **pip** (package installer)
- **Virtual environment** (recommended)

---

## Quick Start

### 1. Create Virtual Environment

**Windows PowerShell:**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS (bash/zsh):**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (optional for development)
# Default values work for local development
```

### 4. Start the Server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Server will be available at:
- **API**: http://127.0.0.1:8000
- **Health**: http://127.0.0.1:8000/api/v1/health
- **Status**: http://127.0.0.1:8000/api/v1/status
- **Docs (Swagger UI)**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## API Endpoints

### Health Check
```http
GET /api/v1/health
```
**Response:**
```json
{
  "status": "ok",
  "application": "GestureFlow AI",
  "version": "1.0.0"
}
```

Lightweight endpoint verifying API process responsiveness. Does **not** verify camera, model, or controller status.

### Application Status
```http
GET /api/v1/status
```
**Response:**
```json
{
  "application": "GestureFlow AI",
  "version": "1.0.0",
  "environment": "development",
  "backend_state": "ready",
  "current_phase": 1,
  "camera_state": "not_initialized",
  "tracking_state": "not_initialized",
  "model_state": "not_loaded",
  "controller_state": "disabled"
}
```

Returns detailed component states reflecting **actual implementation status**.

---

## Component States (Phase 1)

| Component | State | Description |
|-----------|-------|-------------|
| Camera | `not_initialized` | Webcam access not implemented |
| Tracking | `not_initialized` | Hand tracking not implemented |
| Model | `not_loaded` | Gesture model not implemented |
| Controller | `disabled` | OS control not implemented |

> **Important**: Phase 1 does **not** implement webcam access, hand tracking, gesture recognition, or computer control. These states explicitly reflect that those components are not yet built.

---

## Running Tests

```bash
# Run all tests
python -m pytest -q

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_health.py -v
python -m pytest tests/test_status.py -v
python -m pytest tests/test_config.py -v
```

Tests verify:
- ✅ Health check endpoint responds correctly
- ✅ Status endpoint returns accurate component states
- ✅ Phase identification (current_phase = 1)
- ✅ Uninitialized component states
- ✅ Configuration validation
- ✅ Error response behavior
- ✅ API routing

---

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `GestureFlow AI` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `ENVIRONMENT` | `development` | `development`, `production`, `staging` |
| `API_HOST` | `127.0.0.1` | API bind address |
| `API_PORT` | `8000` | API port |
| `API_PREFIX` | `/api/v1` | API version prefix |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_DIR` | `logs` | Log directory |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | CORS origins (comma-separated) |
| `FRONTEND_DEV_URL` | `http://localhost:5173` | Frontend dev URL |

---

## Logging

Structured logging to console and rotating files:

- **Console**: Real-time output during development
- **File**: `logs/gestureflow.log` (10MB max, 5 backups)
- **Format**: `TIMESTAMP | LEVEL | MODULE | FUNCTION:LINE | MESSAGE`
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

---

## Frontend Integration

The backend is designed to integrate with the existing React + TypeScript + Vite frontend:

- **CORS**: Configured for Vite dev server (`http://localhost:5173`)
- **API Base URL**: Frontend expects `http://localhost:8000/api/v1`
- **Response Format**: Typed JSON matching frontend interfaces
- **No coupling**: Backend has zero dependencies on React/frontend code

### Frontend API Client (Reference)
```typescript
// frontend/src/services/api/client.ts
export const API_CONFIG: ApiConfig = {
  baseUrl: import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api/v1',
  timeout: 5000,
  isBackendConnected: false,
};
```

---

## Future Integration Points

The architecture prepares for these future modules (not implemented in Phase 1):

| Module | Purpose | Interface Location |
|--------|---------|-------------------|
| Camera Manager | Webcam access & frame capture | `app/services/camera_manager.py` |
| Hand Tracking | MediaPipe hand landmark detection | `app/services/hand_tracking.py` |
| Dataset Collection | Gesture sample recording | `app/services/dataset_collector.py` |
| Static Classifier | Single-frame gesture classification | `app/services/static_classifier.py` |
| Temporal Classifier | Sequence-based gesture recognition | `app/services/temporal_classifier.py` |
| Model Training | Custom model training pipeline | `app/services/model_trainer.py` |
| Gesture Config | Gesture definitions & mappings | `app/services/gesture_config.py` |
| Action Router | Gesture → action mapping | `app/services/action_router.py` |
| Mouse Controller | OS mouse control | `app/services/mouse_controller.py` |
| Keyboard Controller | OS keyboard control | `app/services/keyboard_controller.py` |
| Background Runtime | Persistent background service | `app/services/runtime.py` |

Each will integrate via the `ApplicationService` component registry.

---

## Limitations (Phase 1)

- ❌ No webcam access
- ❌ No MediaPipe/TensorFlow dependencies
- ❌ No hand tracking or gesture recognition
- ❌ No mouse/keyboard control
- ❌ No dataset collection or model training
- ❌ No background runtime/service
- ❌ No database (JSON config only)

---

## Development

### Project Structure Principles

1. **Separation of Concerns**: Routes → Services → Schemas
2. **Typed Everything**: Pydantic models for all I/O
3. **Explicit States**: Enums over booleans for component status
4. **Configuration First**: Environment-driven, validated at startup
5. **Observability**: Structured logging, health/status endpoints
6. **Testability**: No external dependencies in tests

### Adding New Endpoints

1. Create route module in `app/api/routes/`
2. Define request/response schemas in `app/schemas/`
3. Add business logic to `app/services/`
4. Register router in `app/api/router.py`
5. Write tests in `tests/`

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS

# Kill process or change API_PORT in .env
```

### Import Errors
```bash
# Ensure virtual environment is activated
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/macOS

# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration Errors
- Check `.env` file exists and is valid
- Verify `ENVIRONMENT` is one of: `development`, `production`, `staging`
- Verify `LOG_LEVEL` is valid: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Check port range: 1-65535

---

## License

Part of GestureFlow AI project.