"""
API routes for check-in and authentication endpoints.

Clean separation:
- Auth routes: /api/auth/* → AuthService → AuthRepository
- Check-in routes: /api/* → CheckInService → CheckInRepository
"""

from fastapi import APIRouter, Depends, Cookie, Response, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.checkin_service import CheckInService
from app.services.auth_service import AuthService
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
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> CheckInResponse:
    """
    Record a check-in.
    
    Returns current status and hours remaining.
    """
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.record_checkin(phone=phone, hours_ago=(payload.hours_ago if payload else None))
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> StatusResponse:
    """
    Get current check-in status.
    
    Returns SAFE / DUE_SOON / MISSED along with timing info.
    """
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.get_status(phone=phone)
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> SettingsResponse:
    """Get current check-in interval setting for a user"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.get_settings(phone=phone)
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/settings", response_model=SettingsResponse)
async def update_settings(
    update: SettingsUpdate,
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> SettingsResponse:
    """Update settings (interval, buffers, contacts)"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.update_settings(update, phone=phone)
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/instructions", response_model=InstructionsResponse)
async def get_instructions(
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> InstructionsResponse:
    """Get instructions for trusted contacts (user-specific if available)"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.get_instructions(phone=phone)
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/instructions", response_model=InstructionsResponse)
async def save_instructions(
    update: InstructionsUpdate,
    phone: str | None = Cookie(default=None, alias="phone"),
    service: CheckInService = CheckInServiceDep,
    response: Response = None,
) -> InstructionsResponse:
    """Save/update instructions for trusted contacts"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        return service.save_instructions(update.content, phone=phone)
    except ValueError as e:
        if response:
            response.delete_cookie("phone")
        raise HTTPException(status_code=401, detail=str(e))


# ============ AUTHENTICATION ENDPOINTS ============

@router.post("/auth/verify-firebase")
async def verify_firebase(payload: dict, response: Response, service: AuthService = AuthServiceDep):
    """
    (Production) Verify Firebase ID Token and authenticate user.
    
    Sets session cookie on success.
    """
    id_token = payload.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="id_token required")
        
    user = service.verify_firebase_login(id_token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid or expired Firebase token")
        
    # Set session cookie (Phase 2 will replace this with JWT)
    response.set_cookie(
        key="phone",
        value=user["phone"],
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        path='/',
        samesite='lax',
    )
    return user


@router.post("/auth/logout")
async def logout(response: Response):
    # Explicitly clear the cookie with EXACTLY the same parameters
    response.delete_cookie(
        key="phone",
        path='/',
        httponly=True,
        samesite='lax'
    )
    # Adding this header prevents the browser from using a cached version of the page
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return {"ok": True}


@router.post("/auth/update-display-name")
async def update_display_name(
    payload: dict,
    response: Response,
    phone: str | None = Cookie(default=None, alias="phone"),
    service: AuthService = AuthServiceDep,
):
    """Update user's display name (optional profile setup)"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    display_name = payload.get("display_name")
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name required")
    user = service.update_display_name(phone, display_name)
    # refresh cookie to ensure browser keeps it
    response.set_cookie(
        key="phone",
        value=user["phone"],
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        path='/',
        samesite='lax',
    )
    return user


@router.get("/me")
async def whoami(
    phone: str | None = Cookie(default=None, alias="phone"),
    service: AuthService = AuthServiceDep,
    response: Response = None,
):
    """Get current authenticated user info"""
    if not phone:
        raise HTTPException(status_code=401, detail="not authenticated")
    user = service.get_user_info(phone)
    if not user:
        # Clear stale cookie
        try:
            response.delete_cookie("phone")
        except:
            pass
        raise HTTPException(status_code=401, detail="user not found")
    return user


