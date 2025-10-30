# utils/otp_service.py
"""
OTP helper module
────────────────────────────────────────────────────────────
Doctor SQLAlchemy model must include:
    otp_hash         : str   (HMAC‑SHA256 of the OTP)
    otp_expires_at   : datetime
    otp_verified     : bool
    otp_last_sent_at : datetime
    otp_send_count   : int
    phone_number     : str   (for SMS delivery)
────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import hmac
import logging
import os
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Tuple

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# ────────────────────────────
# .env → runtime settings
# ────────────────────────────
load_dotenv()  # reads the .env once when the module is imported


@dataclass(frozen=True)
class _Env:
    SECRET_KEY: str                  = os.getenv("SECRET_KEY", "CHANGE_ME")
    OTP_TTL_MIN: int                 = int(os.getenv("OTP_TTL_MIN", 10))
    OTP_RESEND_COOL_MIN: int         = int(os.getenv("OTP_RESEND_COOL_MIN", 2))
    OTP_MAX_HOURLY: int              = int(os.getenv("OTP_MAX_HOURLY", 5))
    FAST2SMS_API_KEY: str            = os.getenv("FAST2SMS_API_KEY", "")
    SMS_SENDER_ID: str               = os.getenv("SMS_SENDER_ID", "NIKAPP")
    SMS_TEMPLATE: str                = os.getenv("SMS_TEMPLATE", "Your OTP is {otp}")


settings = _Env()  # immutable instance

logger = logging.getLogger(__name__)

# ────────────────────────────
# Internal helpers
# ────────────────────────────
_now = datetime.utcnow


def _random_otp() -> str:
    """Return a zero‑padded 6‑digit OTP like '042991'."""
    return f"{random.randint(0, 999_999):06}"


def _hash_otp(otp: str) -> str:
    """HMAC‑SHA256 hash; secret key from .env (SECRET_KEY)."""
    return hmac.new(settings.SECRET_KEY.encode(), otp.encode(), "sha256").hexdigest()


# ────────────────────────────
# Delivery channels
# ────────────────────────────
def send_email(to_email: str, otp: str) -> None:
    """Stub – swap with SendGrid / SES / SMTP as needed."""
    logger.info("[EMAIL] OTP %s → %s", otp, to_email)
    print(f"[EMAIL] To {to_email} | OTP: {otp}")


def send_sms(to_number: str, otp: str) -> None:
    """Fast2SMS sample implementation."""
    logger.info("[SMS] OTP %s → %s", otp, to_number)

    if not settings.FAST2SMS_API_KEY:  # dev guard
        print(f"[SMS‑DEV] To {to_number} | OTP: {otp}")
        return

    payload = {
        "route": "q",
        "message": settings.SMS_TEMPLATE.format(otp=otp),
        "language": "english",
        "flash": 0,
        "numbers": to_number,
        "sender_id": settings.SMS_SENDER_ID,
    }
    headers = {
        "authorization": settings.FAST2SMS_API_KEY,
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://www.fast2sms.com/dev/bulkV2",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if r.status_code != 200:
        logger.error("Fast2SMS error %s – %s", r.status_code, r.text)
        raise RuntimeError("SMS gateway failure")


# ────────────────────────────
# Core: generate + store + send
# ────────────────────────────
def generate_and_store_otp(
    doctor,
    db: Session,
    *,
    channel: str,
    sender: Callable[[str, str], None],
) -> str:
    """
    Create an OTP, enforce quotas, persist metadata, dispatch via `sender`.
    Returns the plain OTP (for logs / tests).
    """
    now = _now()

    # Hourly quota
    if doctor.otp_last_sent_at and doctor.otp_send_count:
        if (
            doctor.otp_last_sent_at > now - timedelta(hours=1)
            and doctor.otp_send_count >= settings.OTP_MAX_HOURLY
        ):
            raise RuntimeError("Hourly OTP limit reached")

    # Cool‑down
    if doctor.otp_last_sent_at and doctor.otp_last_sent_at > now - timedelta(
        minutes=settings.OTP_RESEND_COOL_MIN
    ):
        raise RuntimeError("Please wait before requesting another OTP")

    otp_plain = _random_otp()
    doctor.otp_hash = _hash_otp(otp_plain)
    doctor.otp_expires_at = now + timedelta(minutes=settings.OTP_TTL_MIN)
    doctor.otp_verified = False
    doctor.otp_last_sent_at = now
    doctor.otp_send_count = (doctor.otp_send_count or 0) + 1

    db.commit()

    sender(channel, otp_plain)
    return otp_plain


# ────────────────────────────
# Verification
# ────────────────────────────
def verify_otp(
    doctor,
    db: Session,
    otp_input: str,
    *,
    invalidate_on_success: bool = True,
) -> bool:
    now = _now()

    if not doctor.otp_hash or not doctor.otp_expires_at:
        return False
    if doctor.otp_expires_at < now:
        return False
    if not hmac.compare_digest(_hash_otp(otp_input), doctor.otp_hash):
        return False

    if invalidate_on_success:
        doctor.otp_verified = True
        doctor.otp_hash = None
        doctor.otp_expires_at = None
        doctor.otp_send_count = 0
        db.commit()

    return True


# ────────────────────────────
# Aadhaar (stub)
# ────────────────────────────
def send_aadhaar_otp(aadhaar_number: str) -> Tuple[str, datetime]:
    logger.info("[AADHAAR] Send OTP for %s", aadhaar_number)
    txn_id = str(uuid.uuid4())
    expires = _now() + timedelta(minutes=settings.OTP_TTL_MIN)
    # TODO: real UIDAI call
    return txn_id, expires


def verify_aadhaar_with_uidai(txn_id: str, otp: str) -> bool:
    logger.info("[AADHAAR] Verify txn=%s otp=%s", txn_id, otp)
    # TODO: real UIDAI call
    return otp == "123456"
