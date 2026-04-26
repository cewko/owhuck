import secrets


def generate_signing_key() -> str:
    return secrets.token_urlsafe(32)