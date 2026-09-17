from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db

from app.models.tenant import Tenant
from app.models.inventory import InventoryMovement
from app.models.user import User
from app.models.sale import Sale


from app.services.tenant import TenantService


from app.routers.tenant import router as tenant_router
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router
from app.routers.product import router as product_router
from app.routers.inventory import router as inventory_router
from app.routers.sale import router as sale_router



Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Saas-Boutique",
    version="0.1.0",
)

app.include_router(tenant_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(sale_router)


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




