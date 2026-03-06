from fastapi import FastAPI

from app.api.routes import admin, projects

app = FastAPI(title="Research Dashboard API")
app.include_router(admin.router)
app.include_router(projects.router)
