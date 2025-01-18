from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.agent import Agent
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentController:
    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate):
        return AgentService.create_agent(db, agent_data)

    @staticmethod
    def get_agent(db: Session, agent_id: str):
        agent = AgentService.get_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @staticmethod
    def update_agent(db: Session, agent_id: str, agent_data: AgentUpdate):
        agent = AgentService.update_agent(db, agent_id, agent_data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: str):
        agent = AgentService.delete_agent(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent deleted successfully"}

    @staticmethod
    def get_agent_by_name(db: Session, agent_name: str) -> Agent:
        agent = AgentService.get_agent_by_name(db, agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @staticmethod
    def get_all_agents(db: Session):
        return AgentService.get_all_agents(db)

    @staticmethod
    def chat_with_agent(db: Session, agent_name: str):
        agent = AgentService.chat_with_agent(db, agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
