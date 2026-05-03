import logging
from datetime import datetime, timedelta
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.services.rag_service import generate_answer, retrieve_chunks
from app.services.sentiment_service import classify_batch, summarize_sentiment

logger = logging.getLogger(__name__)


class AgentResult(TypedDict):
    user_message: str
    final_answer: str
    invoice_summary: str
    document_answer: str
    document_sources: list[dict]
    agents_used: dict[str, bool]
    sentiment_results: list[dict]
    sentiment_summary: dict


class AgentState(TypedDict):
    user_message: str
    needs_invoice: bool
    needs_document: bool
    needs_sentiment: bool
    document_question: str
    invoice_summary: str
    document_answer: str
    document_sources: list[dict]
    sentiment_results: list[dict]
    sentiment_summary: dict
    final_answer: str
    messages: list[dict]


INVOICE_KEYWORDS = {
    "invoice",
    "invoices",
    "expense",
    "expenses",
    "spend",
    "spent",
    "cost",
    "costs",
    "payment",
    "payments",
    "purchase",
    "purchases",
    "receipt",
    "receipts",
    "weekly",
    "total",
}

DOCUMENT_KEYWORDS = {
    "document",
    "documents",
    "contract",
    "agreement",
    "policy",
    "terms",
    "condition",
    "conditions",
    "clause",
    "report",
    "search",
    "find",
}


def _needs_invoice_agent(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in INVOICE_KEYWORDS)


def _needs_document_agent(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in DOCUMENT_KEYWORDS)


def _summarize_weekly_invoices(db: Session) -> str:
    week_ago = datetime.utcnow() - timedelta(days=7)
    invoices = db.scalars(
        select(Invoice)
        .where(Invoice.created_at >= week_ago)
        .order_by(Invoice.created_at.desc())
    ).all()

    if not invoices:
        return "No invoices were recorded in the past 7 days."

    total = sum(item.amount for item in invoices)
    lines = [
        f"Weekly expense summary ({week_ago.date()} to {datetime.utcnow().date()}):",
        f"Total spent: {total:.2f} BDT",
        f"Invoice count: {len(invoices)}",
    ]
    return "\n".join(lines)


def _answer_document_question(question: str) -> tuple[str, list[dict]]:
    try:
        chunks = retrieve_chunks(question=question, top_k=5)
        if not chunks:
            return "No relevant information found in uploaded documents.", []
        answer = generate_answer(question, chunks)
        return answer, chunks
    except Exception as exc:
        logger.warning("Document agent failed: %s", exc)
        return (
            "I could not search documents right now. Please verify document indexing and try again.",
            [],
        )


def sentiment_agent_node(message: str) -> tuple[list[dict], dict]:
    """
    Sentiment Agent.

    Classifies customer feedback embedded in the user message.
    Activates when the message contains feedback-like lines. Returns
    (results, summary). Uses `classify_batch` and `summarize_sentiment`.
    """
    logger.info("Sentiment Agent analyzing feedback...")

    # Extract feedback lines from the message
    # Split by newlines or semicolons — common paste formats
    lines = [
        line.strip()
        for line in message.replace(";", "\n").split("\n")
        if len(line.strip()) > 10  # ignore very short lines
    ]

    if not lines:
        return [], {}

    try:
        results = classify_batch(lines)
        summary = summarize_sentiment(results)

        logger.info(
            f"Sentiment Agent: {summary.get('total', 0)} texts, "
            f"dominant={summary.get('dominant')}, alert={summary.get('alert')}"
        )

        return results, summary
    except FileNotFoundError:
        logger.warning("Sentiment model not found — skipping")
        return [], {}


def _compose_final_answer(invoice_summary: str, document_answer: str) -> str:
    parts: list[str] = []
    if invoice_summary:
        parts.append(f"Invoice summary:\n{invoice_summary}")
    if document_answer:
        parts.append(f"Document answer:\n{document_answer}")
    if not parts:
        return "I can help with invoices and uploaded documents. Please ask a related question."
    return "\n\n".join(parts)


PLANNER_PROMPT = """You are a query routing agent for a business intelligence system.

Analyze the user's message and return ONLY valid JSON:
{
    "needs_invoice": true/false,
    "needs_document": true/false,
    "needs_sentiment": true/false,
    "document_question": "refined question for document search, or empty string"
}

Route to invoices when: expenses, costs, spending, bills, receipts,
payments, purchases, weekly summary, how much spent, total amount.

Route to documents when: contract, agreement, policy, terms, conditions,
clause, what does it say, document, report, find in, search for.

Route to sentiment when: feedback, reviews, customer comments, analyze
sentiment, classify, positive negative, customer satisfaction, complaints,
or when the message contains multiple lines of customer feedback text.

Return ONLY the JSON. No explanation."""


def planner_node(state: AgentState) -> AgentState:
    """
    Planner node: classify the incoming message into routing booleans.
    This function uses a simple, local heuristic fallback so it is
    safe to run in tests/environments without external LLM access.
    """
    msg = state.get("user_message", "")

    # Heuristic routing
    needs_invoice = _needs_invoice_agent(msg)
    needs_document = _needs_document_agent(msg)

    # Sentiment detection: keywords or multi-line feedback
    lowered = msg.lower()
    feedback_keywords = ("feedback", "review", "reviews", "customer", "complaint", "complaints")
    multi_line = sum(1 for l in msg.splitlines() if len(l.strip()) > 10) >= 2
    needs_sentiment = any(k in lowered for k in feedback_keywords) or multi_line

    # Default: if none matched, try invoice by default (keeps original behavior)
    if not (needs_invoice or needs_document or needs_sentiment):
        needs_invoice = True

    # document_question remains the same as message by default
    document_question = msg

    return {
        **state,
        "needs_invoice": needs_invoice,
        "needs_document": needs_document,
        "needs_sentiment": needs_sentiment,
        "document_question": document_question,
    }


def route_after_planner(state: AgentState) -> list[str]:
    next_nodes = []

    if state.get("needs_invoice"):
        next_nodes.append("invoice_agent")

    if state.get("needs_document"):
        next_nodes.append("document_agent")

    if state.get("needs_sentiment"):
        next_nodes.append("sentiment_agent")

    if not next_nodes:
        next_nodes.append("synthesizer")

    return next_nodes


def synthesizer_node(state: AgentState) -> AgentState:
    # Compose final answer from available pieces
    final = _compose_final_answer(state.get("invoice_summary", ""), state.get("document_answer", ""))
    return {**state, "final_answer": final}


def build_graph(db: Session):
    """
    Lightweight graph builder compatible with the project's expected
    registration. This is a minimal implementation used by `run_agent`.
    """
    class SimpleGraph:
        def __init__(self):
            self.nodes = {}
            self.entry = None

        def add_node(self, name, func):
            self.nodes[name] = func

        def set_entry_point(self, name):
            self.entry = name

        def add_conditional_edges(self, *_args, **_kwargs):
            pass

        def add_edge(self, *_args, **_kwargs):
            pass

        def compile(self):
            return self

    graph = SimpleGraph()

    graph.add_node("planner", planner_node)
    graph.add_node("invoice_agent", lambda s: {**s, "invoice_summary": _summarize_weekly_invoices(db)})
    graph.add_node("document_agent", lambda s: {**s, **(_answer_document_question(s.get("document_question") or s.get("user_message")) and {"document_answer": (_answer_document_question(s.get("document_question") or s.get("user_message"))[0]), "document_sources": (_answer_document_question(s.get("document_question") or s.get("user_message"))[1])})})
    graph.add_node("sentiment_agent", lambda s: {**s, "sentiment_results": sentiment_agent_node(s.get("user_message", ""))[0], "sentiment_summary": sentiment_agent_node(s.get("user_message", ""))[1]})
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("planner")
    return graph.compile()


def run_agent(user_message: str, db: Session) -> AgentResult:
    """Route a user message to invoice and/or document logic and merge results."""
    needs_invoice = _needs_invoice_agent(user_message)
    needs_document = _needs_document_agent(user_message)

    # Fallback keeps behavior predictable for generic prompts.
    if not needs_invoice and not needs_document:
        needs_invoice = True

    invoice_summary = _summarize_weekly_invoices(db) if needs_invoice else ""
    document_answer, document_sources = (
        _answer_document_question(user_message) if needs_document else ("", [])
    )

    # Sentiment analysis
    sentiment_results, sentiment_summary = sentiment_agent_node(user_message)

    final_answer = _compose_final_answer(
        invoice_summary=invoice_summary,
        document_answer=document_answer,
    )

    return {
        "user_message": user_message,
        "final_answer": final_answer,
        "invoice_summary": invoice_summary,
        "document_answer": document_answer,
        "document_sources": document_sources,
        "agents_used": {
            "invoice": needs_invoice,
            "document": needs_document,
            "sentiment": bool(sentiment_results),
        },
        "sentiment_results": sentiment_results,
        "sentiment_summary": sentiment_summary,
    }