from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import jwt
from fastapi import Depends, HTTPException
from app.core.jwt import JWT_ALGORITHM, JWT_SECRET


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré.",
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    role = payload.get("role")

    if not user_id or not tenant_id or not role:
        raise HTTPException(
            status_code=401,
            detail="Token invalide.",
        )

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
    }

