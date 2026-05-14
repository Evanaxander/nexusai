import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent_service import run_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    user_message: str
    final_answer: str
    invoice_summary: str
    document_answer: str
    document_sources: list[dict]
    sentiment_summary: dict        # ← add
    agents_used: dict[str, bool]
    duration_seconds: float    

@router.post(
    "/chat",
    response_model=AgentResponse,
    summary="Send a message to the NexusAI multi-agent system"
)
def chat(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Main agent endpoint.

    Send any business question in natural language.
    The Planner decides which agents to activate.
    The Synthesizer combines their outputs into one answer.

    Examples:
    - "What did I spend this week?"
    - "What are the payment terms in my supplier contract?"
    - "Summarize my expenses and check if the contract mentions penalties"
    """
    result = run_agent(
        user_message=request.message,
        db=db
    )
    return AgentResponse(**result)