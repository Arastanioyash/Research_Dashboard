# Research Dashboard

Next.js UI for survey analytics with a basic authentication page and interactive dashboard components.

## Features
- Login page (`/login`) with demo credentials
- Protected dashboard page (`/dashboard`)
- Single-select vs multi-select survey chart
- Survey data table
- Mean score KPI card for single-select questions

## Demo credentials
- Email: `admin@research.com`
- Password: `Password@123`

## One-command local startup (Docker)
From the repository root, start everything (frontend, backend, and Postgres):

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`

## Backend sample data generator
Generate sample survey files (wide CSV + metadata + banner metadata):

```bash
python backend/scripts/generate_sample_data.py --output-dir backend/sample_data
```

Generated files:
- `backend/sample_data/sample_responses_wide.csv`
- `backend/sample_data/sample_metadata.json`
- `backend/sample_data/sample_banner_metadata.json`

## Sample import + quick validation flow
1. Generate sample files:
   ```bash
   python backend/scripts/generate_sample_data.py --output-dir backend/sample_data
   ```
2. Start the stack:
   ```bash
   docker compose up --build
   ```
3. In your import flow (backend endpoint/UI), use:
   - CSV: `backend/sample_data/sample_responses_wide.csv`
   - Metadata: `backend/sample_data/sample_metadata.json`
   - Banner metadata: `backend/sample_data/sample_banner_metadata.json`
4. Run unit tests to validate schema inference + metric computation:
   ```bash
   python -m pytest tests -q
   ```

## Run tests locally
```bash
python -m pytest tests -q
```
