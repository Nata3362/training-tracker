"""Password hashing helpers used by the authentication services."""

import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    """Hash a password with a random salt using ``hashlib.scrypt``."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """Compare a plaintext password with a stored salted hash."""
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
    )
    return hmac.compare_digest(digest, bytes.fromhex(digest_hex))


if __name__ == "__main__":
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)
    print("ok")
