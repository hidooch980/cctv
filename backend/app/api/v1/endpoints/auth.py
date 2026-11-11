import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.auth import (
    Token,
    UserResponse,
    UserCreate,
    LoginRequest,
    QRSessionResponse,
    QRStatusResponse,
    QRAuthorizeRequest,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# In-memory storage for dynamic QR login sessions (expiring in 120s)
qr_sessions: Dict[str, Dict[str, Any]] = {}


def cleanup_expired_qr_sessions():
    now = time.time()
    expired = [sid for sid, data in qr_sessions.items() if now > data["expires_at"]]
    for sid in expired:
        qr_sessions.pop(sid, None)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    if user is None:
        # Fallback for default admin if not in DB yet
        if username == settings.DEFAULT_ADMIN_USERNAME:
            return User(
                id=1,
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                role="admin",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
        raise credentials_exception
    return user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Check default admin credentials
    if (
        login_data.username == settings.DEFAULT_ADMIN_USERNAME
        and login_data.password == settings.DEFAULT_ADMIN_PASSWORD
    ):
        access_token = create_access_token(subject=settings.DEFAULT_ADMIN_USERNAME)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "admin",
            "username": settings.DEFAULT_ADMIN_USERNAME,
        }

    # Query DB
    result = await db.execute(select(User).filter(User.username == login_data.username))
    user = result.scalars().first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    login_req = LoginRequest(username=form_data.username, password=form_data.password)
    return await login(login_req, db)


# =========================================================================
# QR Code Authentication Endpoints
# =========================================================================

@router.post("/qr/session", response_model=QRSessionResponse)
async def create_qr_session():
    """
    Generate a cryptographic QR code login session valid for 120 seconds.
    The web client displays this QR code for the mobile CCTV app to scan.
    """
    cleanup_expired_qr_sessions()
    session_id = str(uuid.uuid4())
    now = time.time()
    expires_at = now + 120.0  # 2 minutes

    payload = f"molido://auth/qr?session_id={session_id}&issued_at={int(now)}"

    qr_sessions[session_id] = {
        "session_id": session_id,
        "qr_payload": payload,
        "created_at": now,
        "expires_at": expires_at,
        "status": "pending",  # pending, scanned, approved, expired
        "token_data": None,
    }

    return QRSessionResponse(
        session_id=session_id,
        qr_payload=payload,
        expires_in_seconds=120,
    )


@router.get("/qr/status/{session_id}", response_model=QRStatusResponse)
async def get_qr_status(session_id: str):
    """
    Check the current status of a QR login session (polling endpoint).
    When approved, returns the JWT access token and user role.
    """
    cleanup_expired_qr_sessions()
    data = qr_sessions.get(session_id)
    if not data:
        return QRStatusResponse(session_id=session_id, status="expired", token=None)

    if time.time() > data["expires_at"]:
        data["status"] = "expired"
        return QRStatusResponse(session_id=session_id, status="expired", token=None)

    token = None
    if data["status"] == "approved" and data["token_data"]:
        token = Token(**data["token_data"])

    return QRStatusResponse(session_id=session_id, status=data["status"], token=token)


@router.post("/qr/scan/{session_id}")
async def mark_qr_scanned(session_id: str):
    """
    Mobile app calls this as soon as the camera scans the QR code.
    Changes web status to 'scanned'.
    """
    data = qr_sessions.get(session_id)
    if not data or time.time() > data["expires_at"]:
        raise HTTPException(status_code=404, detail="QR session not found or expired")

    data["status"] = "scanned"
    return {"status": "scanned"}


@router.post("/qr/authorize")
async def authorize_qr_session(
    auth_req: QRAuthorizeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Authenticated mobile app user confirms and authorizes login on web screen.
    """
    data = qr_sessions.get(auth_req.session_id)
    if not data or time.time() > data["expires_at"]:
        raise HTTPException(status_code=404, detail="QR session not found or expired")

    access_token = create_access_token(subject=current_user.username)
    token_dict = {
        "access_token": access_token,
        "token_type": "bearer",
        "role": current_user.role,
        "username": current_user.username,
    }

    data["status"] = "approved"
    data["token_data"] = token_dict
    return {"message": "Session authorized successfully", "username": current_user.username}


@router.post("/qr/simulate-approve/{session_id}")
async def simulate_qr_approve(session_id: str):
    """
    Simulate mobile app QR scan & authorization for demo & testing.
    Approves the session with default admin account.
    """
    data = qr_sessions.get(session_id)
    if not data or time.time() > data["expires_at"]:
        raise HTTPException(status_code=404, detail="QR session not found or expired")

    access_token = create_access_token(subject=settings.DEFAULT_ADMIN_USERNAME)
    token_dict = {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "admin",
        "username": settings.DEFAULT_ADMIN_USERNAME,
    }

    data["status"] = "approved"
    data["token_data"] = token_dict
    return {"message": "Simulated authorization successful", "username": settings.DEFAULT_ADMIN_USERNAME}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    result = await db.execute(select(User).filter(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "operator",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
