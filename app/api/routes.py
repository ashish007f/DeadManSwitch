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

@router.post("/auth/send-otp")
async def send_otp(payload: dict, service: AuthService = AuthServiceDep):
    """
    Initiate signup/login: send OTP to phone number.
    
    Returns OTP code (dev mode only).
    """
    phone = payload.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="phone required")
    result = service.send_otp(phone)
    return result


@router.post("/auth/verify-otp")
async def verify_otp(payload: dict, response: Response, service: AuthService = AuthServiceDep):
    """
    Verify OTP and authenticate user.
    
    Sets phone cookie on success and returns user info.
    """
    phone = payload.get("phone")
    code = payload.get("code")
    if not phone or not code:
        raise HTTPException(status_code=400, detail="phone and code required")
    user = service.verify_otp(phone, code)
    if not user:
        raise HTTPException(status_code=401, detail="invalid or expired OTP")
    # Set a persistent cookie for 7 days to keep session across navigation
    # Set an HttpOnly session cookie so the browser sends it on subsequent
    # navigations and JS cannot tamper with it. Keep SameSite lax for normal
    # navigation. For local development we leave `secure` False.
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


