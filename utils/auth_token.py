# utils/auth_token.py
import os, hmac, hashlib, time, base64

SECRET = os.getenv("APP_SECRET", "change-me")
TOKEN_TTL_SEC = 60 * 60 * 8  # 8 giờ

def _b64(s: bytes) -> str:
    return base64.urlsafe_b64encode(s).decode().rstrip("=")

def _b64dec(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def make_token(username: str, ttl: int = TOKEN_TTL_SEC) -> str:
    exp = int(time.time()) + ttl
    payload = f"{username}|{exp}".encode()
    sig = hmac.new(SECRET.encode(), payload, hashlib.sha256).digest()
    return f"{_b64(payload)}.{_b64(sig)}"

def verify_token(token: str):
    try:
        payload_b64, sig_b64 = token.split(".")
        payload = _b64dec(payload_b64)
        sig = _b64dec(sig_b64)
        expected = hmac.new(SECRET.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        username, exp = payload.decode().split("|")
        if int(exp) < int(time.time()):
            return None
        return username
    except Exception:
        return None