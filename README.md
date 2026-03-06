# Research Dashboard

Research Dashboard workspace containing a Next.js frontend and a FastAPI backend skeleton.

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## Backend auth bootstrap
The backend no longer uses hardcoded default credentials.

1. Run migrations to create auth/RBAC tables.
2. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
3. Execute `python backend/scripts/bootstrap_admin.py` once to seed the first admin account.
