from fastapi import APIRouter, Request, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.security import auth_manager

router = APIRouter(prefix="/auth", tags=["Security & Authentication"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str
    user: str = "Commander Abdur Rahman"


class VerifyResponse(BaseModel):
    authenticated: bool
    user: str = "Commander Abdur Rahman"


class VoiceProfilePayload(BaseModel):
    enrolled: bool = True
    phrase: Optional[str] = None
    voiceprint_metadata: Optional[Dict[str, Any]] = None


# Local voice enrollment cache
_voice_enrollment_record: Dict[str, Any] = {
    "enrolled": False,
    "enrolled_at": None,
    "user": "Commander Abdur Rahman"
}


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    """Authenticate with the secure master password and obtain a session token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    success, token, error_msg = auth_manager.authenticate(req.password, client_id=client_ip)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Invalid security credentials."
        )

    return LoginResponse(
        success=True,
        token=token,
        message="Authentication successful. J.A.R.V.I.S. unlocked.",
        user="Commander Abdur Rahman"
    )


@router.get("/verify", response_model=VerifyResponse)
async def verify_session(authorization: Optional[str] = Header(None)):
    """Verify if the current session token is valid and active."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header.")
    
    token = authorization.replace("Bearer ", "").strip()
    if not auth_manager.validate_session(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")
    
    return VerifyResponse(authenticated=True, user="Commander Abdur Rahman")


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Revoke session token and lock J.A.R.V.I.S."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        auth_manager.revoke_session(token)
    return {"success": True, "message": "J.A.R.V.I.S. session terminated. System locked."}


@router.get("/voice-profile")
async def get_voice_profile():
    """Check voice enrollment state."""
    return _voice_enrollment_record


@router.post("/voice-profile")
async def save_voice_profile(payload: VoiceProfilePayload):
    """Save one-time voice enrollment profile."""
    import datetime
    _voice_enrollment_record["enrolled"] = payload.enrolled
    _voice_enrollment_record["enrolled_at"] = datetime.datetime.now().isoformat()
    _voice_enrollment_record["voiceprint_metadata"] = payload.voiceprint_metadata
    return {"success": True, "message": "Voice profile successfully calibrated and saved."}
