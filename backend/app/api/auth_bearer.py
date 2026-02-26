from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domain.security import decode_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
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
