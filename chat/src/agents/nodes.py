"""Workflow nodes for each triage phase."""

from typing import Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .state import TriageState, PhaseTransition


async def consent_node(state: TriageState) -> dict[str, Any]:
    """Phase 1: Obtain user consent for triage.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    # Check if last message indicates consent
    if state["messages"]:
        last_msg = state["messages"][-1]
        if isinstance(last_msg, HumanMessage):
            content_lower = last_msg.content.lower()
            if any(word in content_lower for word in ["yes", "agree", "consent", "ok", "sure"]):
                return {
                    "phase": "red_flag_check",
                    "consent_given": True,
                    "messages": [
                        AIMessage(
                            content="Thank you for your consent. Let me ask you a few questions about your symptoms.\n\n"
                            "**Important:** I'm an AI triage assistant, not a doctor. My role is to help assess the "
                            "urgency of your condition and guide you to appropriate care.\n\n"
                            "Please describe your eye problem or symptoms in detail."
                        )
                    ],
                }

    # Request consent
    consent_message = AIMessage(
        content="Welcome to the Ocular Triage System.\n\n"
        "Before we begin, I need to inform you:\n\n"
        "1. This is an AI-powered triage tool, not a replacement for medical advice\n"
        "2. Your responses will be saved for medical record purposes\n"
        "3. If I detect any emergency conditions, I'll direct you to seek immediate care\n"
        "4. All information is confidential and HIPAA/GDPR compliant\n\n"
        "Do you consent to proceed with the triage assessment?"
    )

    return {
        "phase": "consent",
        "messages": [consent_message],
    }


async def red_flag_check_node(state: TriageState) -> dict[str, Any]:
    """Phase 2: Check for red flag symptoms indicating emergencies.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    # Get the patient's description from last message
    if not state["messages"] or not isinstance(state["messages"][-1], HumanMessage):
        return {"phase": "red_flag_check"}

    patient_input = state["messages"][-1].content.lower()

    # Simple keyword-based red flag detection
    # TODO: Replace with LLM-based semantic analysis + GraphRAG red flags
    red_flag_keywords = {
        "sudden vision loss": ["sudden", "lost vision", "can't see", "went blind"],
        "chemical burn": ["chemical", "splash", "burned", "acid", "alkali"],
        "penetrating trauma": ["penetrat", "stab", "puncture", "sharp object"],
        "severe pain with nausea": ["severe pain", "nausea", "vomit", "throwing up"],
        "new floaters with flashes": ["floater", "flashes", "flash", "curtain"],
    }

    detected_flags = []
    for flag_name, keywords in red_flag_keywords.items():
        if any(keyword in patient_input for keyword in keywords):
            detected_flags.append(flag_name)

    if detected_flags:
        # EMERGENT - direct to ER
        return {
            "phase": "completed",
            "has_red_flags": True,
            "red_flag_details": {"detected": detected_flags},
            "urgency_level": "emergent",
            "recommendation": "Go to the emergency room immediately",
            "messages": [
                AIMessage(
                    content="🚨 **IMMEDIATE ATTENTION REQUIRED**\n\n"
                    f"Based on your symptoms, I've identified potential emergency conditions: {', '.join(detected_flags)}.\n\n"
                    "**You should go to the emergency room immediately.**\n\n"
                    "Do not wait for an appointment. These symptoms require immediate evaluation by an ophthalmologist.\n\n"
                    "If you're experiencing severe symptoms, call emergency services (911 in US) or have someone drive you to the ER."
                )
            ],
        }

    # No red flags detected, proceed to detailed assessment
    return {
        "phase": "chief_complaint",
        "has_red_flags": False,
        "chief_complaint": state["messages"][-1].content,
    }


async def chief_complaint_node(state: TriageState) -> dict[str, Any]:
    """Phase 3: Standardize chief complaint and query knowledge graph.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    # TODO: Integrate with GraphRAG to:
    # 1. Standardize the chief complaint
    # 2. Query knowledge graph for differential diagnoses
    # 3. Get relevant symptoms/signs to ask about

    # For now, move to systematic questions
    return {
        "phase": "systematic_questions",
        "standardized_complaint": state.get("chief_complaint", ""),
        "messages": [
            AIMessage(
                content="I understand you're experiencing eye problems. Let me ask you some specific questions "
                "to better understand your condition.\n\n"
                "**Question 1:** How long have you been experiencing these symptoms?\n"
                "- Less than 24 hours\n"
                "- 1-3 days\n"
                "- More than 3 days\n"
                "- More than a week"
            )
        ],
    }


async def systematic_questions_node(state: TriageState) -> dict[str, Any]:
    """Phase 4: Ask systematic questions based on differential diagnoses.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    # TODO: Implement dynamic questioning based on GraphRAG differential diagnoses
    # For now, collect basic information and move to risk stratification

    patient_responses = state.get("patient_responses", {})
    question_count = len(patient_responses)

    if question_count < 3:
        # Ask more questions
        questions = [
            "Is your vision affected? If yes, how?\n- Blurry\n- Double vision\n- Decreased vision\n- Normal vision",
            "Are you experiencing pain?\n- No pain\n- Mild discomfort\n- Moderate pain\n- Severe pain",
            "Do you have any discharge or redness?\n- No\n- Mild redness\n- Heavy discharge\n- Both redness and discharge"
        ]

        if state["messages"] and isinstance(state["messages"][-1], HumanMessage):
            # Store the answer
            patient_responses[f"q{question_count}"] = state["messages"][-1].content

        next_question = questions[question_count] if question_count < len(questions) else None

        if next_question:
            return {
                "phase": "systematic_questions",
                "patient_responses": patient_responses,
                "messages": [AIMessage(content=f"**Question {question_count + 1}:** {next_question}")],
            }

    # Done with questions, move to risk stratification
    return {
        "phase": "risk_stratification",
        "patient_responses": patient_responses,
    }


async def risk_stratification_node(state: TriageState) -> dict[str, Any]:
    """Phase 5: Stratify risk and determine urgency level.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    # TODO: Use GraphRAG + LLM to analyze all collected information
    # and determine urgency level based on differential diagnoses

    # Simple logic for demo
    patient_responses = state.get("patient_responses", {})

    # Check for urgent indicators
    responses_text = " ".join(str(v).lower() for v in patient_responses.values())

    if "severe pain" in responses_text or "decreased vision" in responses_text:
        urgency = "urgent"
        recommendation = "You should see an ophthalmologist within 24-48 hours"
        action = "Schedule an urgent appointment"
    else:
        urgency = "non_urgent"
        recommendation = "You should schedule a routine eye examination"
        action = "Schedule a routine appointment within 1-2 weeks"

    return {
        "phase": "recommendation",
        "urgency_level": urgency,
        "recommendation": recommendation,
        "recommended_action": action,
    }


async def recommendation_node(state: TriageState) -> dict[str, Any]:
    """Phase 6: Provide recommendation and offer appointment booking.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    urgency = state.get("urgency_level", "non_urgent")
    recommendation = state.get("recommendation", "Please consult an ophthalmologist")

    message = f"## Assessment Complete\n\n"
    message += f"**Urgency Level:** {urgency.upper()}\n\n"
    message += f"**Recommendation:** {recommendation}\n\n"

    if urgency == "urgent":
        message += "⚠️ Based on your symptoms, you should seek care within the next 24-48 hours.\n\n"
    elif urgency == "non_urgent":
        message += "✓ Your symptoms don't indicate an emergency, but you should still see a doctor for proper evaluation.\n\n"

    message += "Would you like me to help you schedule an appointment?\n\n"
    message += "Reply with 'yes' to book an appointment, or 'no' if you'd prefer to schedule it yourself."

    return {
        "phase": "appointment_booking",
        "messages": [AIMessage(content=message)],
    }


async def appointment_booking_node(state: TriageState) -> dict[str, Any]:
    """Phase 7: Handle appointment booking.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
    if state["messages"] and isinstance(state["messages"][-1], HumanMessage):
        response = state["messages"][-1].content.lower()

        if any(word in response for word in ["yes", "sure", "ok", "book"]):
            # TODO: Integrate with internal booking system
            message = "Great! Let me find available appointments for you.\n\n"
            message += "**Available Doctors:**\n"
            message += "1. Dr. Smith - Available tomorrow at 2:00 PM\n"
            message += "2. Dr. Johnson - Available in 2 days at 10:00 AM\n"
            message += "3. Dr. Williams - Available in 3 days at 3:30 PM\n\n"
            message += "Please reply with the number of your preferred appointment."

            return {
                "phase": "appointment_booking",
                "appointment_requested": True,
                "messages": [AIMessage(content=message)],
            }

    # Complete the session
    return {
        "phase": "completed",
        "messages": [
            AIMessage(
                content="Thank you for using the Ocular Triage System. Take care and feel better soon!\n\n"
                "**Disclaimer:** This assessment is not a diagnosis. Please follow up with a qualified "
                "ophthalmologist for proper medical evaluation and treatment."
            )
        ],
    }


def should_continue(state: TriageState) -> str:
    """Determine next node based on current phase.

    Args:
        state: Current workflow state

    Returns:
        Name of next node to execute
    """
    phase = state.get("phase", "consent")

    if phase == "completed":
        return "end"

    phase_map = {
        "consent": "consent",
        "red_flag_check": "red_flag_check",
        "chief_complaint": "chief_complaint",
        "systematic_questions": "systematic_questions",
        "risk_stratification": "risk_stratification",
        "recommendation": "recommendation",
        "appointment_booking": "appointment_booking",
    }

    return phase_map.get(phase, "end")
