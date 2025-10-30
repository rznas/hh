"""Authentication service for password hashing and verification."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User, UserRole

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate a user with username/email and password.

    Args:
        session: Database session
        username: Username or email
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Try to find user by username or email
    stmt = select(User).where(
        (User.username == username) | (User.email == username)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        return None

    # Check if account is active
    if not user.is_active:
        return None

    # Verify password
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)

        await session.commit()
        return None

    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    await session.commit()

    return user


async def create_user(
    session: AsyncSession,
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.PATIENT,
    preferred_language: str = "en",
) -> User:
    """Create a new user account.

    Args:
        session: Database session
        email: User email
        username: Username
        password: Plain text password (will be hashed)
        full_name: Full name
        role: User role
        preferred_language: Preferred language code

    Returns:
        Created user object
    """
    hashed_password = get_password_hash(password)

    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        preferred_language=preferred_language,
        is_active=True,
        is_verified=False,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID.

    Args:
        session: Database session
        user_id: User UUID

    Returns:
        User object if found, None otherwise
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        User object if found, None otherwise
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_language(
    session: AsyncSession, user_id: UUID, language: str
) -> Optional[User]:
    """Update user's preferred language.

    Args:
        session: Database session
        user_id: User UUID
        language: Language code (e.g., 'en', 'fa', 'ar')

    Returns:
        Updated user object if found, None otherwise
    """
    user = await get_user_by_id(session, user_id)
    if user:
        user.preferred_language = language
        await session.commit()
        await session.refresh(user)
    return user
