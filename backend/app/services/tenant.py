from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


class TenantService:

    @staticmethod
    def create(
        db: Session,
        name: str,
        slug: str,
    ) -> Tenant:
        existing = db.scalar(
            select(Tenant).where(Tenant.slug == slug)
        )

        if existing:
            raise ValueError("Ce slug existe déjà.")

        tenant = Tenant(
            name=name.strip(),
            slug=slug.strip().lower(),
        )

        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def get_by_id(
        db: Session,
        tenant_id: UUID,
    ) -> Tenant | None:
        return db.get(Tenant, tenant_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Tenant | None:
        return db.scalar(
            select(Tenant).where(Tenant.slug == slug.lower())
        )