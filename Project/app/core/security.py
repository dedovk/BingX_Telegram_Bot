import bcrypt
from cryptography.fernet import Fernet


def hash_pin(pin: str) -> str:
    """ converts the PIN code into an unreadable hash """
    pin_bytes = str(pin).encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pin_bytes, salt)

    return hashed.decode('utf-8')


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """ check whether entered PIN matches the hash"""
    try:
        return bcrypt.checkpw(str(plain_pin).encode('utf-8'), str(hashed_pin).encode('utf-8'))
    except Exception:
        return False


def encrypt_secret(data: str, master_key: str) -> str:
    """encode a string using master key"""
    f = Fernet(master_key.encode())
    return f.encrypt(data.encode()).decode()


def decrypt_secret(encrypted_data: str, master_key: str) -> str:
    """decode back to string"""
    f = Fernet(master_key.encode())
    return f.decrypt(encrypted_data.encode()).decode()
