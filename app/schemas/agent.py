from pydantic import BaseModel
from typing import Any, Dict, Optional

class AgentCreate(BaseModel):
    name: str
    config: Dict[str, Any]

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    config: Dict[str, Any]

    class Config:
        from_attributes = True
        
class AgentChatResponse(BaseModel):
    room_url: str
