from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.auth import (
    TOKEN_LIFETIME, Claims, InvalidToken, create_token, decode_token, hash_password, require_admin, require_barista_claims,
    verify_password,
)

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"
NOW = datetime(2026, 10, 21, 8, 0, tzinfo=timezone.utc)


def test_a_password_matches_its_hash_but_not_another_password():
    hashed = hash_password("s3cret!")

    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed)
    assert not verify_password("wrong", hashed)


def test_a_token_carries_the_role_and_cafe():
    token = create_token(user_id=7, role="barista", cafe_id=3, secret=SECRET, now=NOW)

    assert decode_token(token, SECRET, now=NOW + timedelta(hours=1)) == Claims(
        user_id=7, role="barista", cafe_id=3, expires_at=NOW + TOKEN_LIFETIME,
    )


def test_an_admin_token_has_no_cafe():
    token = create_token(user_id=1, role="admin", cafe_id=None, secret=SECRET, now=NOW)

    assert decode_token(token, SECRET, now=NOW) == Claims(
        user_id=1, role="admin", cafe_id=None, expires_at=NOW + TOKEN_LIFETIME,
    )


def test_a_token_signed_with_another_secret_is_rejected():
    token = create_token(user_id=7, role="barista", cafe_id=3, secret="another-secret-that-is-long-enough-too", now=NOW)

    with pytest.raises(InvalidToken):
        decode_token(token, SECRET, now=NOW)


def test_an_expired_token_is_rejected():
    token = create_token(user_id=7, role="barista", cafe_id=3, secret=SECRET, now=NOW)

    with pytest.raises(InvalidToken):
        decode_token(token, SECRET, now=NOW + timedelta(days=2))


def test_garbage_is_not_a_token():
    with pytest.raises(InvalidToken):
        decode_token("not.a.token", SECRET, now=NOW)


def test_admin_routes_reject_baristas():
    with pytest.raises(HTTPException) as e:
        require_admin(Claims(user_id=7, role="barista", cafe_id=3))
    assert e.value.status_code == 403
    assert require_admin(Claims(user_id=1, role="admin", cafe_id=None)).role == "admin"


def test_kds_routes_reject_admins_and_baristas_without_a_cafe():
    for claims in (Claims(user_id=1, role="admin", cafe_id=None), Claims(user_id=7, role="barista", cafe_id=None)):
        with pytest.raises(HTTPException) as e:
            require_barista_claims(claims)
        assert e.value.status_code == 403
    assert require_barista_claims(Claims(user_id=7, role="barista", cafe_id=3)).cafe_id == 3


def test_a_password_over_72_bytes_never_matches():
    hashed = hash_password("x" * 72)

    assert not verify_password("x" * 73, hashed)
