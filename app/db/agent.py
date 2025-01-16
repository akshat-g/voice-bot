import uuid
from sqlalchemy import Column, String, JSON
from .database import Base

class Agent(Base):
    __tablename__ = "agent"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    config = Column(JSON, nullable=False)