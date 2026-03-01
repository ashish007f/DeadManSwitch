"""
API routes for check-in and authentication endpoints.

Clean separation:
- Auth routes: /api/auth/* → AuthService → AuthRepository
- Check-in routes: /api/* → CheckInService → CheckInRepository
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.checkin_service import CheckInService
from app.services.auth_service import AuthService
from app.api.auth_bearer import get_current_user_phone
from app.domain.models import (
    CheckInRequest,
    CheckInResponse,
    StatusResponse,
    SettingsUpdate,
    SettingsResponse,
    InstructionsUpdate,
    InstructionsResponse,
)

router = APIRouter(prefix="/api", tags=["check-in"])


def get_checkin_service(db: Session = Depends(get_db)) -> CheckInService:
    """Dependency: Inject CheckInService with database session"""
    return CheckInService(db)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency: Inject AuthService with database session"""
    return AuthService(db)


# Reusable dependencies
CheckInServiceDep = Depends(get_checkin_service)
AuthServiceDep = Depends(get_auth_service)


# ============ CHECK-IN ENDPOINTS ============

@router.post("/checkin", response_model=CheckInResponse)
async def checkin(
    payload: CheckInRequest = None,
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> CheckInResponse:
    """
    Record a check-in.
    
    Returns current status and hours remaining.
    """
    try:
        return service.record_checkin(phone=phone, hours_ago=(payload.hours_ago if payload else None))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> StatusResponse:
    """
    Get current check-in status.
    
    Returns SAFE / DUE_SOON / MISSED along with timing info.
    """
    try:
        return service.get_status(phone=phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> SettingsResponse:
    """Get current check-in interval setting for a user"""
    try:
        return service.get_settings(phone=phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/settings", response_model=SettingsResponse)
async def update_settings(
    update: SettingsUpdate,
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> SettingsResponse:
    """Update settings (interval, buffers, contacts)"""
    try:
        return service.update_settings(update, phone=phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instructions", response_model=InstructionsResponse)
async def get_instructions(
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> InstructionsResponse:
    """Get instructions for trusted contacts"""
    try:
        return service.get_instructions(phone=phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/instructions", response_model=InstructionsResponse)
async def save_instructions(
    update: InstructionsUpdate,
    phone: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> InstructionsResponse:
    """Save/update instructions for trusted contacts"""
    try:
        return service.save_instructions(update.content, phone=phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ AUTHENTICATION ENDPOINTS ============

@router.post("/auth/verify-firebase")
async def verify_firebase(payload: dict, service: AuthService = AuthServiceDep):
    """
    (Production) Verify Firebase ID Token and authenticate user.
    
    Returns custom Access and Refresh tokens.
    """
    id_token = payload.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="id_token required")
        
    user = service.verify_firebase_login(id_token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid or expired Firebase token")
        
    return user


@router.post("/auth/refresh")
async def refresh_token(payload: dict, service: AuthService = AuthServiceDep):
    """Exchange Refresh Token for a new Access Token"""
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
        
    result = service.refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="invalid or expired refresh token")
        
    return result


@router.post("/auth/logout")
async def logout():
    """Client-side handles token clearing, this is for completeness"""
    return {"ok": True}


@router.post("/auth/update-display-name")
async def update_display_name(
    payload: dict,
    phone: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Update user's display name"""
    display_name = payload.get("display_name")
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name required")
    return service.update_display_name(phone, display_name)


@router.post("/auth/update-fcm-token")
async def update_fcm_token(
    payload: dict,
    phone: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Update user's FCM token for push notifications"""
    fcm_token = payload.get("fcm_token")
    if not fcm_token:
        raise HTTPException(status_code=400, detail="fcm_token required")
    return service.update_fcm_token(phone, fcm_token)


@router.get("/me")
async def whoami(
    phone: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Get current authenticated user info"""
    user = service.get_user_info(phone)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user
