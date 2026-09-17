from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserService:

    @staticmethod
    def create(
        db: Session,
        tenant_id: UUID,
        email: str,
        username: str,
        password_hash: str,
        role: str = "user",
    ) -> User:

        email = email.strip().lower()

        existing = db.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.email == email,
            )
        )

        if existing:
            raise ValueError(
                "Cet email existe déjà pour ce tenant."
            )

        user = User(
            tenant_id=tenant_id,
            email=email,
            username=username.strip(),
            password_hash=password_hash,
            role=role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: UUID,
    ) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(
        db: Session,
        tenant_id: UUID,
        email: str,
    ) -> User | None:

        return db.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.email == email.strip().lower(),
            )
        )