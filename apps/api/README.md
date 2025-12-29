# sunny-2 API

Solar Generation Estimator API - Powered by Copernicus CDSE and Gemini 2.0

## Quick Start

### Prerequisites

- Python 3.12+
- uv (recommended) or pip

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[all]"

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Or using the CLI
sunny-api
```

### Running Tests

```bash
pytest
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Project Structure

```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Pydantic settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── estimate.py      # Solar estimation endpoints (TODO)
│   ├── services/
│   │   ├── copernicus.py    # CDSE integration (TODO)
│   │   ├── solar_calculator.py  # Pvlib calculations (TODO)
│   │   └── ai_consultant.py # Gemini integration (TODO)
│   └── models/
│       └── schemas.py       # Pydantic models (TODO)
├── tests/
│   └── test_health.py
├── pyproject.toml
└── README.md
```

