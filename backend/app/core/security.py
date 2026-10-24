import os
import time
import secrets
import hashlib
import hmac
from typing import Dict, Tuple, Optional
from app.core.config import settings

# Memory storage for active authenticated sessions: token -> expiry_timestamp
_active_sessions: Dict[str, float] = {}

# Failed attempt tracker: ip/client -> (failed_count, lockout_until_timestamp)
_failed_attempts: Dict[str, Tuple[int, float]] = {}

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
SESSION_DURATION_SECONDS = 86400  # 24 hours


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Hash a password using scrypt (RFC 7914 memory-hard key derivation).
    Returns (hex_hash, hex_salt).
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    
    # scrypt with n=16384, r=8, p=1
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        maxmem=32 * 1024 * 1024
    )
    return derived.hex(), salt.hex()


def verify_password(plain_password: str, stored_hash_hex: str, stored_salt_hex: str) -> bool:
    """Verify a plain password against stored scrypt hash and salt."""
    try:
        salt = bytes.fromhex(stored_salt_hex)
        candidate_hash, _ = hash_password(plain_password, salt=salt)
        return hmac.compare_digest(candidate_hash, stored_hash_hex)
    except Exception:
        return False


class AuthManager:
    def __init__(self):
        # Initialize master hash from configured initial password
        raw_pw = settings.JARVIS_PASSWORD or "tec jarvis"
        self._master_hash, self._master_salt = hash_password(raw_pw)

    def update_password(self, new_password: str):
        """Update configured master password hash."""
        self._master_hash, self._master_salt = hash_password(new_password)

    def check_rate_limit(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if client is locked out.
        Returns (is_locked, remaining_seconds).
        """
        now = time.time()
        record = _failed_attempts.get(client_id)
        if not record:
            return False, 0
        
        count, lockout_until = record
        if now < lockout_until:
            return True, int(lockout_until - now)
        elif count >= MAX_FAILED_ATTEMPTS and now >= lockout_until:
            # Reset after lockout expires
            del _failed_attempts[client_id]
            return False, 0
        return False, 0

    def record_failed_attempt(self, client_id: str):
        """Increment failed attempts and apply lockout if threshold exceeded."""
        now = time.time()
        record = _failed_attempts.get(client_id)
        count = (record[0] + 1) if record else 1
        
        lockout_until = 0.0
        if count >= MAX_FAILED_ATTEMPTS:
            lockout_until = now + LOCKOUT_DURATION_SECONDS
            
        _failed_attempts[client_id] = (count, lockout_until)

    def record_successful_login(self, client_id: str):
        """Clear failed attempts on successful login."""
        if client_id in _failed_attempts:
            del _failed_attempts[client_id]

    def authenticate(self, password: str, client_id: str = "local") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authenticate password and issue session token if valid.
        Returns (success, token_or_none, error_message_or_none).
        """
        is_locked, remaining = self.check_rate_limit(client_id)
        if is_locked:
            return False, None, f"Security lock engaged. Too many failed attempts. Retry in {remaining} seconds."

        # Verify against master hash
        is_valid = verify_password(password, self._master_hash, self._master_salt)

        # Also support direct runtime check against settings in case .env was refreshed
        if not is_valid and settings.JARVIS_PASSWORD:
            is_valid = (password == settings.JARVIS_PASSWORD)

        if not is_valid:
            self.record_failed_attempt(client_id)
            return False, None, "Invalid authentication credentials. Access denied."

        # Clear failed attempts and generate session token
        self.record_successful_login(client_id)
        token = secrets.token_urlsafe(32)
        expiry = time.time() + SESSION_DURATION_SECONDS
        _active_sessions[token] = expiry

        return True, token, None

    def validate_session(self, token: str) -> bool:
        """Validate if a session token is active and not expired."""
        if not token:
            return False
        
        expiry = _active_sessions.get(token)
        if not expiry:
            return False
            
        if time.time() > expiry:
            del _active_sessions[token]
            return False
            
        return True

    def revoke_session(self, token: str):
        """Revoke / log out session token."""
        if token in _active_sessions:
            del _active_sessions[token]


auth_manager = AuthManager()
