"""Main Chainlit application for ocular triage chat."""

import chainlit as cl
from langchain_core.messages import HumanMessage
from uuid import uuid4, UUID
from typing import Optional

from agents.workflow import create_triage_workflow
from agents.state import TriageState
from config.settings import get_settings
from services.database import db_manager, get_db_session
from services.auth import authenticate_user


# Initialize settings
settings = get_settings()

# Initialize database
db_manager.initialize()

# Create workflow
workflow = create_triage_workflow()


@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """Authenticate user with username/email and password.

    Args:
        username: Username or email address
        password: Plain text password

    Returns:
        cl.User object if authentication successful, None otherwise
    """
    # Get database session
    async for session in get_db_session():
        # Authenticate user
        user = await authenticate_user(session, username, password)

        if user:
            # Return Chainlit User object
            return cl.User(
                identifier=str(user.id),
                metadata={
                    "role": user.role.value,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "preferred_language": user.preferred_language,
                    "provider": "credentials",
                }
            )

        return None


@cl.on_chat_start
async def start() -> None:
    """Initialize chat session."""
    # Generate session ID
    session_id = str(uuid4())
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("conversation_id", None)

    # Initialize state
    initial_state: TriageState = {
        "messages": [],
        "phase": "consent",
        "consent_given": False,
        "has_red_flags": False,
        "urgency_level": "unknown",
        "patient_responses": {},
        "appointment_requested": False,
        "total_tokens": 0,
    }

    cl.user_session.set("state", initial_state)

    # Trigger consent phase
    config = {"configurable": {"thread_id": session_id}}
    result = await workflow.ainvoke(initial_state, config)

    # Send initial message
    if result.get("messages"):
        last_message = result["messages"][-1]
        await cl.Message(content=last_message.content).send()

    # Update state
    cl.user_session.set("state", result)


@cl.on_message
async def main(message: cl.Message) -> None:
    """Handle incoming messages."""
    session_id = cl.user_session.get("session_id")
    current_state = cl.user_session.get("state")

    if not session_id or not current_state:
        await cl.Message(content="Session error. Please refresh the page.").send()
        return

    # Check if workflow is completed
    if current_state.get("phase") == "completed":
        await cl.Message(
            content="This triage session has been completed. Please refresh the page to start a new session."
        ).send()
        return

    # Add user message to state
    current_state["messages"].append(HumanMessage(content=message.content))

    # Run workflow
    config = {"configurable": {"thread_id": session_id}}

    try:
        # Stream the response
        async with cl.Step(name="Processing", type="tool") as step:
            step.input = message.content

            result = await workflow.ainvoke(current_state, config)

            # Get the last AI message
            if result.get("messages"):
                last_message = result["messages"][-1]
                step.output = last_message.content

                # Send response
                await cl.Message(content=last_message.content).send()

            # Update session state
            cl.user_session.set("state", result)

            # Log phase transition
            new_phase = result.get("phase", "unknown")
            await cl.Message(
                content=f"*[Phase: {new_phase}]*",
                author="System",
            ).send()

    except Exception as e:
        await cl.Message(
            content=f"An error occurred: {str(e)}\n\nPlease try again or refresh the page."
        ).send()


@cl.on_chat_end
async def end() -> None:
    """Clean up when chat ends."""
    # TODO: Save conversation to database
    session_id = cl.user_session.get("session_id")
    state = cl.user_session.get("state")

    if session_id and state:
        print(f"Session {session_id} ended. Final phase: {state.get('phase')}")
        # Here you would save to database


@cl.on_settings_update
async def setup_settings(settings_dict: dict) -> None:
    """Handle settings updates."""
    # TODO: Allow users to configure preferences
    pass


if __name__ == "__main__":
    # This allows running with: python src/app.py
    # But typically you'll use: chainlit run src/app.py
    pass
