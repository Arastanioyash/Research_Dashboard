# Research Dashboard

Survey data ingestion and analytics playground for CSV/SPSS/Excel-to-dashboard workflows.

---

## Quick start (VS Code)

This project supports **two ways** to run in VS Code:

1. **Docker (recommended)**
2. **Local Python backend + static frontend**

---

## 1) Run with Docker in VS Code (recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- VS Code installed
- Optional but helpful VS Code extensions:
  - **Docker** (`ms-azuretools.vscode-docker`)
  - **YAML** (`redhat.vscode-yaml`)

### Steps

1. Open the project folder in VS Code.
2. Open a terminal in VS Code (`Terminal -> New Terminal`).
3. (Optional) Create local env file:

   ```bash
   cp .env.example .env
   ```

4. Start everything:

   ```bash
   docker compose up --build
   ```

5. Open:
   - Frontend: `http://localhost:3000`
   - Backend health: `http://localhost:8000/health`
   - Backend sample metric: `http://localhost:8000/metrics/nps`

### Optional Redis profile

Run with Redis only when needed:

```bash
docker compose --profile cache up --build
```

### Stop services

In the same terminal press `Ctrl + C`, then optionally clean up:

```bash
docker compose down
```

---

## 2) Run in VS Code without Docker (backend tests/dev utilities)

> Use this mode when Docker is unavailable and you only need backend/test workflows.

### Prerequisites

- Python 3.10+

### Steps

1. Open the project in VS Code.
2. Create and activate a virtual environment:

   **macOS/Linux**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   **Windows (PowerShell)**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   make install
   ```

4. Run tests:

   ```bash
   make test
   ```

5. Format code:

   ```bash
   make fmt
   ```

---

## Makefile commands

- `make install` → install local Python dependencies from `backend/requirements-dev.txt`
- `make dev` → `docker compose up --build`
- `make test` → run backend unit tests
- `make fmt` → format backend code with black

---

## Environment variables

You can configure ports/paths via `.env` (copy from `.env.example`).

```env
BACKEND_PORT=8000
DUCKDB_PATH=/data/research.duckdb
FRONTEND_PORT=3000
REDIS_PORT=6379
```

`docker-compose.yml` uses these with defaults.

---

## Project dependency/config files

- `backend/requirements.txt` → runtime dependencies
- `backend/requirements-dev.txt` → dev/test dependencies
- `backend/pytest.ini` → pytest config
- `backend/Dockerfile` + `backend/.dockerignore` → backend image build
- `frontend/Dockerfile` → frontend image build
- `.env.example` → environment variable template
- `docker-compose.yml` → multi-service orchestration

---

## Sample dataset generation

Generate a sample CSV that includes:

- single-select
- multi-select binaries
- grid Likert
- NPS
- ranking
- constant-sum
- numeric
- text
- unknown

Run:

```bash
python scripts/generate_sample_dataset.py
```

Output:

- `data/sample_survey.csv`

The sample intentionally includes **text** and **unknown** fields for inference/validation checks.
