"""LangGraph workflow for triage system."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import TriageState
from .nodes import (
    consent_node,
    red_flag_check_node,
    chief_complaint_node,
    systematic_questions_node,
    risk_stratification_node,
    recommendation_node,
    appointment_booking_node,
    should_continue,
)


def create_triage_workflow() -> StateGraph:
    """Create and configure the triage workflow graph.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(TriageState)

    # Add all nodes
    workflow.add_node("consent", consent_node)
    workflow.add_node("red_flag_check", red_flag_check_node)
    workflow.add_node("chief_complaint", chief_complaint_node)
    workflow.add_node("systematic_questions", systematic_questions_node)
    workflow.add_node("risk_stratification", risk_stratification_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("appointment_booking", appointment_booking_node)

    # Set entry point
    workflow.set_entry_point("consent")

    # Add conditional edges based on current phase
    workflow.add_conditional_edges(
        "consent",
        should_continue,
        {
            "consent": "consent",
            "red_flag_check": "red_flag_check",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "red_flag_check",
        should_continue,
        {
            "red_flag_check": "red_flag_check",
            "chief_complaint": "chief_complaint",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "chief_complaint",
        should_continue,
        {
            "chief_complaint": "chief_complaint",
            "systematic_questions": "systematic_questions",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "systematic_questions",
        should_continue,
        {
            "systematic_questions": "systematic_questions",
            "risk_stratification": "risk_stratification",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "risk_stratification",
        should_continue,
        {
            "risk_stratification": "risk_stratification",
            "recommendation": "recommendation",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "recommendation",
        should_continue,
        {
            "recommendation": "recommendation",
            "appointment_booking": "appointment_booking",
            "end": END,
        }
    )

    workflow.add_conditional_edges(
        "appointment_booking",
        should_continue,
        {
            "appointment_booking": "appointment_booking",
            "end": END,
        }
    )

    # Compile with memory checkpointer for conversation persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
