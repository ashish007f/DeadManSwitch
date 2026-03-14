"""
API routes for check-in and authentication endpoints using Cloud Firestore.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from google.cloud import firestore

from app.db.database import get_db
from app.services.checkin_service import CheckInService
from app.services.auth_service import AuthService
from app.config import settings
from app.api.auth_bearer import get_current_user_phone
from app.limiter import limiter
from app.scheduler.jobs import _scheduler # Import global instance
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


def get_checkin_service(db: firestore.Client = Depends(get_db)) -> CheckInService:
    """Dependency: Inject CheckInService with Firestore client"""
    return CheckInService(db)


def get_auth_service(db: firestore.Client = Depends(get_db)) -> AuthService:
    """Dependency: Inject AuthService with Firestore client"""
    return AuthService(db)


# Reusable dependencies
CheckInServiceDep = Depends(get_checkin_service)
AuthServiceDep = Depends(get_auth_service)


# ============ CHECK-IN ENDPOINTS ============

@router.post("/checkin", response_model=CheckInResponse)
@limiter.limit(settings.rate_limit_general)
def checkin(
    request: Request,
    payload: CheckInRequest = None,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> CheckInResponse:
    """Record a check-in."""
    try:
        return service.record_checkin(p_hash=p_hash, hours_ago=(payload.hours_ago if payload else None))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=StatusResponse)
@limiter.limit(settings.rate_limit_general)
def get_status(
    request: Request,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> StatusResponse:
    """Get current check-in status."""
    try:
        return service.get_status(p_hash=p_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings", response_model=SettingsResponse)
@limiter.limit(settings.rate_limit_general)
def get_settings(
    request: Request,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> SettingsResponse:
    """Get settings"""
    try:
        return service.get_settings(p_hash=p_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/settings", response_model=SettingsResponse)
@limiter.limit(settings.rate_limit_general)
def update_settings(
    request: Request,
    update: SettingsUpdate,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> SettingsResponse:
    """Update settings"""
    try:
        return service.update_settings(update, p_hash=p_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instructions", response_model=InstructionsResponse)
@limiter.limit(settings.rate_limit_general)
def get_instructions(
    request: Request,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> InstructionsResponse:
    """Get instructions"""
    try:
        return service.get_instructions(p_hash=p_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/instructions", response_model=InstructionsResponse)
@limiter.limit(settings.rate_limit_general)
def save_instructions(
    request: Request,
    update: InstructionsUpdate,
    p_hash: str = Depends(get_current_user_phone),
    service: CheckInService = CheckInServiceDep,
) -> InstructionsResponse:
    """Save instructions"""
    try:
        return service.save_instructions(update.content, p_hash=p_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ AUTHENTICATION ENDPOINTS ============

@router.post("/auth/verify-firebase")
@limiter.limit(settings.rate_limit_auth)
async def verify_firebase(request: Request, payload: dict, service: AuthService = AuthServiceDep):
    """Verify Firebase ID Token and authenticate user."""
    id_token = payload.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="id_token required")
        
    user = service.verify_firebase_login(id_token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid or expired Firebase token")
        
    return user


@router.post("/auth/refresh")
@limiter.limit(settings.rate_limit_auth)
async def refresh_token(request: Request, payload: dict, service: AuthService = AuthServiceDep):
    """Exchange Refresh Token for a new Access Token"""
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
        
    result = service.refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="invalid or expired refresh token")
        
    return result


@router.post("/auth/logout")
async def logout(request: Request):
    return {"ok": True}


@router.post("/auth/update-display-name")
async def update_display_name(
    request: Request,
    payload: dict,
    p_hash: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Update user's display name"""
    display_name = payload.get("display_name")
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name required")
    return service.update_display_name(p_hash, display_name)


@router.post("/auth/update-fcm-token")
async def update_fcm_token(
    request: Request,
    payload: dict,
    p_hash: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Update user's FCM token"""
    fcm_token = payload.get("fcm_token")
    if not fcm_token:
        raise HTTPException(status_code=400, detail="fcm_token required")
    return service.update_fcm_token(p_hash, fcm_token)


@router.get("/me")
async def whoami(
    request: Request,
    p_hash: str = Depends(get_current_user_phone),
    service: AuthService = AuthServiceDep,
):
    """Get current authenticated user info"""
    user = service.get_user_info(p_hash)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user


@router.get("/health", tags=["system"])
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@router.post("/system/check-status", tags=["system"])
async def trigger_system_check(request: Request):
    """
    Internal endpoint to trigger the check-in evaluation.
    Called by Google Cloud Scheduler.
    """
    # Security check: Ensure it's called with the secret key
    internal_secret = request.headers.get("X-Internal-Secret")
    if not internal_secret or internal_secret != settings.secret_key:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid internal secret")
    
    # Trigger the check logic
    _scheduler._check_status()
    return {"status": "triggered"}
