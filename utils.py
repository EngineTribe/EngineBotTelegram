from hashlib import sha256
from base64 import b64encode


def calculate_password_hash(password: str):
    return sha256(b64encode(password.encode('utf-8'))).hexdigest()
