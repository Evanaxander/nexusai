import logging
from datetime import datetime, timedelta
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.services.rag_service import generate_answer, retrieve_chunks
from app.services.sentiment_service import classify_batch, summarize_sentiment

from app.core.observability import metrics
import time
import json
from groq import Groq
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentState(TypedDict, total=False):
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

Route to invoices ONLY when: expenses, costs, spending, bills,
receipts, payments, purchases, weekly summary, how much spent, total amount.

Route to documents when: ANYTHING about a PDF, journal, paper, CV,
resume, contract, agreement, policy, what does it say, what is it about,
who is, what are the skills, what are the experiences, tell me about,
summarize the document.

Route to sentiment when: analyze feedback, customer reviews, classify
sentiment, or when the message contains multiple lines of feedback text.

IMPORTANT: Questions about documents, PDFs, journals, or papers
ALWAYS go to documents, never to invoices.

Return ONLY the JSON. No explanation."""


def planner_node(state: AgentState) -> AgentState:
    logger.info(f"Planner analyzing: '{state['user_message'][:60]}...'")

    message_lower = state["user_message"].lower().strip()

    # Handle greetings — return friendly message without hitting any agent
    GREETINGS = ["hi", "hello", "hey", "howdy", "good morning",
                 "good evening", "sup", "what's up", "wassup"]
    if message_lower in GREETINGS or message_lower.rstrip("!").strip() in GREETINGS:
        return {
            **state,
            "needs_invoice": False,
            "needs_document": False,
            "needs_sentiment": False,
            "document_question": "",
            "final_answer": (
                "Hello! I am NexusAI. You can ask me:\n\n"
                "• About your expenses — 'show this week's invoices'\n"
                "• About your documents — 'what is the contract about?'\n"
                "• Analyze customer feedback — paste feedback text\n\n"
                "What would you like to know?"
            )
        }

    INVOICE_KEYWORDS = [
        "spent", "expense", "expenses", "spending", "bill", "receipt",
        "payment", "purchase", "cost", "total", "how much",
        "weekly summary", "invoice", "invoices", "price of", "pricing",
        "pedal", "brake", "cable", "labor", "item", "items",
        "what did i buy", "show invoice", "full expense", "all expense",
        "summarize expense", "this week"
    ]

    DOCUMENT_KEYWORDS = [
        "pdf", "journal", "paper", "cv", "resume", "contract",
        "document", "agreement", "policy", "skills of", "experience of",
        "what is the", "what are the", "who is", "tell me about",
        "summarize the", "about briefly", "what does the"
    ]

    SENTIMENT_KEYWORDS = [
        "feedback", "sentiment", "review", "analyze", "classify",
        "customer said", "complaint", "positive", "negative"
    ]

    invoice_hits = sum(1 for k in INVOICE_KEYWORDS if k in message_lower)
    document_hits = sum(1 for k in DOCUMENT_KEYWORDS if k in message_lower)
    sentiment_hits = sum(1 for k in SENTIMENT_KEYWORDS if k in message_lower)

    if document_hits > 0 and invoice_hits == 0:
        logger.info("Planner → document (rule-based)")
        return {
            **state,
            "needs_invoice": False,
            "needs_document": True,
            "needs_sentiment": False,
            "document_question": state["user_message"]
        }

    if invoice_hits > 0 and document_hits == 0:
        logger.info("Planner → invoice (rule-based)")
        return {
            **state,
            "needs_invoice": True,
            "needs_document": False,
            "needs_sentiment": False,
            "document_question": ""
        }

    if sentiment_hits > 0 and invoice_hits == 0:
        logger.info("Planner → sentiment (rule-based)")
        return {
            **state,
            "needs_invoice": False,
            "needs_document": False,
            "needs_sentiment": True,
            "document_question": ""
        }

    # Ambiguous — use LLM
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": PLANNER_PROMPT},
                {"role": "user", "content": state["user_message"]}
            ],
            max_tokens=200,
            temperature=0.0
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)
        routing = json.loads(raw)

    except Exception as e:
        logger.warning(f"Planner LLM failed: {e} — defaulting to invoice")
        routing = {
            "needs_invoice": True,
            "needs_document": False,
            "needs_sentiment": False,
            "document_question": ""
        }

    logger.info(
        f"Planner routing (LLM) → "
        f"invoice={routing.get('needs_invoice')}, "
        f"document={routing.get('needs_document')}"
    )

    return {
        **state,
        "needs_invoice": routing.get("needs_invoice", False),
        "needs_document": routing.get("needs_document", False),
        "needs_sentiment": routing.get("needs_sentiment", False),
        "document_question": routing.get(
            "document_question", state["user_message"]
        )
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
            self.routing = {}

        def add_node(self, name, func):
            self.nodes[name] = func

        def set_entry_point(self, name):
            self.entry = name

        def add_conditional_edges(self, source, route_fn, edges):
            self.routing[source] = (route_fn, edges)

        def add_edge(self, source, target):
            if source not in self.routing:
                self.routing[source] = (lambda _: [target], {})

        def compile(self):
            return self

        def invoke(self, initial_state):
            """Execute the graph starting from entry point."""
            state = initial_state
            current_node = self.entry

            while current_node:
                if current_node not in self.nodes:
                    logger.error(f"Node '{current_node}' not found in graph")
                    break

                # Execute the node
                node_func = self.nodes[current_node]
                state = node_func(state)

                # Determine next node(s)
                if current_node == "planner":
                    # Route based on planner output
                    next_nodes = route_after_planner(state)
                    if next_nodes:
                        # Execute all required agents
                        for agent_node in next_nodes:
                            if agent_node != "synthesizer":
                                state = self.nodes[agent_node](state)
                        # Then synthesizer
                        current_node = "synthesizer"
                    else:
                        break
                elif current_node == "synthesizer":
                    # End of graph
                    break
                else:
                    # Regular node, no routing
                    break

            return state

    graph = SimpleGraph()

    def document_agent_node(s):
        doc_q = s.get("document_question") or s.get("user_message")
        answer, sources = _answer_document_question(doc_q)
        return {**s, "document_answer": answer, "document_sources": sources}

    def sentiment_agent_node_wrapper(s):
        results, summary = sentiment_agent_node(s.get("user_message", ""))
        return {**s, "sentiment_results": results, "sentiment_summary": summary}

    graph.add_node("planner", planner_node)

    def invoice_agent_node(s):
        week_ago = datetime.utcnow() - timedelta(days=7)
        invoices = db.scalars(
            select(Invoice)
            .where(Invoice.created_at >= week_ago)
            .order_by(Invoice.created_at.desc())
        ).all()

        if not invoices:
            no_invoice_msg = (
                "No invoices are currently available in the past 7 days. "
                "They may have been deleted or no invoices have been uploaded yet. "
                "You can upload a new invoice image to track expenses."
            )
            return {**s, "invoice_summary": no_invoice_msg}

        total = sum(item.amount for item in invoices)
        lines = [
            f"Weekly expense summary ({week_ago.date()} to {datetime.utcnow().date()}):",
            f"Total spent: {total:.2f} BDT",
            f"Invoice count: {len(invoices)}",
        ]

        # Add individual invoices with full detail
        lines.append("\nIndividual invoices:")
        for inv in invoices:
            lines.append(
                f"  • #{inv.id} | {inv.vendor} | "
                f"{inv.amount:.2f} {inv.currency} | "
                f"Date: {inv.invoice_date or 'not detected'} | "
                f"Items: {inv.items or 'see record'}"
            )

        summary = "\n".join(lines)

        # If user asked a specific question, use Groq to answer from invoice data
        specific_keywords = [
            "price", "cost", "how much", "pedal", "brake",
            "cable", "labor", "item", "front", "rear"
        ]
        user_msg = s["user_message"].lower()

        if any(k in user_msg for k in specific_keywords) and invoices:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Answer questions about invoice data precisely. Use only the provided invoice data."
                    },
                    {
                        "role": "user",
                        "content": f"Invoice data:\n{summary}\n\nQuestion: {s['user_message']}"
                    }
                ],
                max_tokens=300,
                temperature=0.1
            )
            summary = response.choices[0].message.content

        return {**s, "invoice_summary": summary}

    graph.add_node("invoice_agent", invoice_agent_node)
    graph.add_node("document_agent", document_agent_node)
    graph.add_node("sentiment_agent", sentiment_agent_node_wrapper)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("planner")
    return graph.compile()


def run_agent(user_message: str, db: Session) -> dict:
    """
    Public function called by the API endpoint.
    Now includes timing and metrics collection.
    """
    graph = build_graph(db)
    start_time = time.time()

    initial_state: AgentState = {
        "user_message": user_message,
        "needs_invoice": False,
        "needs_document": False,
        "needs_sentiment": False,
        "document_question": "",
        "invoice_summary": "",
        "document_answer": "",
        "document_sources": [],
        "sentiment_results": [],
        "sentiment_summary": {},
        "final_answer": "",
        "messages": []
    }

    logger.info(f"Running agent for: '{user_message[:60]}...'")
    # Check if planner short-circuited with a greeting response
    test_state = planner_node(initial_state)
    if test_state.get("final_answer"):
        return {
            "user_message": user_message,
            "final_answer": test_state["final_answer"],
            "invoice_summary": "",
            "document_answer": "",
            "document_sources": [],
            "sentiment_summary": {},
            "agents_used": {"invoice": False, "document": False, "sentiment": False},
            "duration_seconds": round(time.time() - start_time, 3)
        }

    success = True
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        success = False
        logger.error(f"Agent run failed: {e}")
        raise

    finally:
        # Always record metrics even if agent failed
        duration = time.time() - start_time
        agents_used = {
            "invoice": final_state.get("needs_invoice", False)
                if success else False,
            "document": final_state.get("needs_document", False)
                if success else False,
            "sentiment": final_state.get("needs_sentiment", False)
                if success else False,
        }
        metrics.record_run(
            user_message=user_message,
            agents_used=agents_used,
            duration_seconds=duration,
            success=success,
            final_answer_length=len(
                final_state.get("final_answer", "")
                if success else ""
            )
        )
        logger.info(f"Agent completed in {round(duration, 3)}s")

    return {
        "user_message": user_message,
        "final_answer": final_state["final_answer"],
        "invoice_summary": final_state.get("invoice_summary", ""),
        "document_answer": final_state.get("document_answer", ""),
        "document_sources": final_state.get("document_sources", []),
        "sentiment_summary": final_state.get("sentiment_summary", {}),
        "agents_used": agents_used,
        "duration_seconds": round(duration, 3)
    }