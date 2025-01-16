from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.agent import AgentController
from app.db.database import get_db
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate


router = APIRouter()

@router.post("/", response_model=AgentResponse)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    return AgentController.create_agent(db, agent)

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    return AgentController.get_agent(db, agent_id)

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, agent: AgentUpdate, db: Session = Depends(get_db)):
    return AgentController.update_agent(db, agent_id, agent)

@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    return AgentController.delete_agent(db, agent_id)

@router.get("/by-name/{agent_name}", response_model=AgentResponse)
def get_agent_by_name(agent_name: str, db: Session = Depends(get_db)):
    return AgentController.get_agent_by_name(db, agent_name)
