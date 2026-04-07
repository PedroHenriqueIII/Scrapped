import os
import base64
from cryptography.fernet import Fernet
from app.core.settings import get_settings

settings = get_settings()


def get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode()
    if len(key) < 32:
        key = key.ljust(32, b'0')
    key = base64.urlsafe_b64encode(key[:32])
    return Fernet(key)


def encrypt_value(value: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(encrypted_value.encode()).decode()
