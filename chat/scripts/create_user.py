#!/usr/bin/env python3
"""Script to create a new user in the database."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.database import db_manager
from src.services.auth import create_user
from src.models.user import UserRole


async def main():
    """Create a new user interactively."""
    print("=== Create New User ===\n")

    # Get user input
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    full_name = input("Full Name (optional): ").strip() or None

    # Role selection
    print("\nAvailable roles:")
    for i, role in enumerate(UserRole, 1):
        print(f"{i}. {role.value}")

    role_choice = input("Select role (1-5, default=4 for patient): ").strip()
    try:
        role_idx = int(role_choice) - 1 if role_choice else 3  # Default to patient
        role = list(UserRole)[role_idx]
    except (ValueError, IndexError):
        role = UserRole.PATIENT

    # Language selection
    print("\nAvailable languages:")
    print("1. English (en)")
    print("2. فارسی (fa)")

    lang_choice = input("Select language (1-2, default=1 for English): ").strip()
    language = "fa" if lang_choice == "2" else "en"

    # Confirm
    print("\n=== User Details ===")
    print(f"Email: {email}")
    print(f"Username: {username}")
    print(f"Full Name: {full_name or 'N/A'}")
    print(f"Role: {role.value}")
    print(f"Language: {language}")

    confirm = input("\nCreate this user? (y/n): ").strip().lower()
    if confirm != "y":
        print("User creation cancelled.")
        return

    # Initialize database
    db_manager.initialize()

    # Create user
    async for session in db_manager.session():
        try:
            user = await create_user(
                session=session,
                email=email,
                username=username,
                password=password,
                full_name=full_name,
                role=role,
                preferred_language=language,
            )

            print(f"\n✅ User created successfully!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role.value}")

        except Exception as e:
            print(f"\n❌ Error creating user: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
