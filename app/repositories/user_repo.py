"""
AI-LMS User Repository — database access for user accounts.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import EmailVerification, PasswordReset, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch active user by email address (case-insensitive)."""
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower(),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        user = await self.get_by_email(email)
        return user is not None

    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 20) -> list[User]:
        """Fetch all users with a specific role."""
        result = await self.db.execute(
            select(User)
            .where(User.role == role, User.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.student,
    ) -> User:
        """Create a new user record."""
        return await self.create(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True,
            is_verified=False,
        )

    # =========================================================================
    # Email Verification
    # =========================================================================

    async def create_email_verification(self, user_id: uuid.UUID, token: str) -> EmailVerification:
        """Store an email verification token."""
        record = EmailVerification(user_id=user_id, token=token)
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_email_verification(self, token: str) -> EmailVerification | None:
        """Find an unused email verification record by token."""
        result = await self.db.execute(
            select(EmailVerification).where(
                EmailVerification.token == token,
                EmailVerification.is_used.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def mark_email_verified(self, verification: EmailVerification, user: User) -> None:
        """Mark token as used and set user as verified."""
        verification.is_used = True
        user.is_verified = True
        self.db.add(verification)
        self.db.add(user)
        await self.db.flush()

    # =========================================================================
    # Password Reset
    # =========================================================================

    async def create_password_reset(self, user_id: uuid.UUID, token: str) -> PasswordReset:
        """Store a password reset token."""
        record = PasswordReset(user_id=user_id, token=token)
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_password_reset(self, token: str) -> PasswordReset | None:
        """Find an unused password reset record by token."""
        result = await self.db.execute(
            select(PasswordReset).where(
                PasswordReset.token == token,
                PasswordReset.is_used.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def mark_password_reset_used(
        self, reset: PasswordReset, user: User, new_hashed_password: str
    ) -> None:
        """Mark token as used and update the user's password."""
        reset.is_used = True
        user.hashed_password = new_hashed_password
        self.db.add(reset)
        self.db.add(user)
        await self.db.flush()
