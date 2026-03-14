import os
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domain.security import decode_token
from app.domain.auth_provider import verify_app_check_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        # 1. Verify App Check token if enforced
        enforce = os.getenv("ENFORCE_APP_CHECK", "false").lower() == "true"
        if enforce:
            app_check_token = request.headers.get("X-Firebase-AppCheck")
            if not verify_app_check_token(app_check_token):
                raise HTTPException(status_code=401, detail="Unauthorized app traffic.")

        # 2. Verify JWT Bearer token
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
            payload = decode_token(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            
            if payload.get("type") != "access":
                raise HTTPException(status_code=403, detail="Invalid token type.")
                
            return payload
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

# Dependency to get current user phone from token
def get_current_user_phone(token_payload: dict = Security(JWTBearer())):
    phone = token_payload.get("sub")
    if not phone:
        raise HTTPException(status_code=403, detail="Token payload missing subject.")
    return phone
