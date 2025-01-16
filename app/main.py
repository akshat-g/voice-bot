from fastapi import FastAPI

from app.db.database import Base, engine
from app.routes import agent

app = FastAPI()

app.include_router(agent.router, prefix="/agent", tags=["Agents"])

# Ensure the database is initialized
Base.metadata.create_all(bind=engine)