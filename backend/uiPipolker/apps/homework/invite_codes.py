import hashlib
import secrets


def make_invite_code():
    return secrets.token_urlsafe(32)


def digest_invite_code(code):
    return hashlib.sha256(code.strip().encode('utf-8')).hexdigest()
