from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db, SessionLocal

from app.models.tenant import Tenant
from app.models.inventory import InventoryMovement
from app.models.user import User
from app.models.sale import Sale
from app.models.sync_outbox import SyncOutbox
from app.models.product import Product
from app.models.sync_state import SyncState

from app.services.sync_worker import sync_worker


from app.routers.tenant import router as tenant_router
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router
from app.routers.sync import router as sync_router
from app.routers.product import router as product_router
from app.routers.inventory import router as inventory_router
from app.routers.sale import router as sale_router


Base.metadata.create_all(bind=engine)


def init_sync_state():
    db = SessionLocal()

    try:
        state = db.get(SyncState, 1)

        if not state:
            db.add(
                SyncState(
                    id=1,
                    last_sequence=0,
                )
            )
            db.commit()

    finally:
        db.close()


init_sync_state()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application startup")

    await sync_worker.start()

    print("🔄 Sync worker démarré depuis lifespan")

    yield

    print("🛑 Application shutdown")

    await sync_worker.stop()


app = FastAPI(
    title="Saas-Boutique",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(tenant_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(sale_router)
app.include_router(sync_router)


@app.get("/")
def root():
    return {
        "app": "Saas-Boutique",
        "status": "running",
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "error",
            "database": "disconnected",
        }