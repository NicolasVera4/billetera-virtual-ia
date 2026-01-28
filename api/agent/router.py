from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from api.agent.agent import run_agent

router_agent = APIRouter()

@router_agent.post("/agent")
def agent_endpoint(question: str, db: Session = Depends(get_db)):
    result = run_agent(question, db)
    return result