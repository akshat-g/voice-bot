from sqlalchemy import Column
from sqlalchemy.orm import Session
from app.schemas.agent import AgentCreate, AgentUpdate
from app.db.agent import Agent
from typing import cast, Dict, Any


class AgentService:
    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate):
        agent = Agent(name=agent_data.name, config=agent_data.config)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent(db: Session, agent_id: str):
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def update_agent(db: Session, agent_id: str, agent_data: AgentUpdate):
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None
        if agent_data.name:
            agent.name = cast(Column[str], agent_data.name)
        if agent_data.config:
            agent.config = cast(Column[Dict[str, Any]], agent_data.config)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: str):
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            db.delete(agent)
            db.commit()
        return agent

    @staticmethod
    def get_agent_by_name(db: Session, name: str):
        return db.query(Agent).filter(Agent.name == name).first()

    @staticmethod
    def get_all_agents(db: Session):
        return db.query(Agent).all()
