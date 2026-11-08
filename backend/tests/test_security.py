import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.security import (
    hash_password,
    hash_session_token,
    issue_session_token,
    session_is_active,
    verify_password,
)


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_password_hash_rejects_weak_input_and_malformed_hash():
    with pytest.raises(ValueError):
        hash_password("short")
    assert not verify_password("anything", "not-a-valid-hash")


def test_session_token_is_random_and_only_hash_is_persistable():
    first = issue_session_token(ttl_seconds=300, now=1_000)
    second = issue_session_token(ttl_seconds=300, now=1_000)
    assert first.token != second.token
    assert first.token_hash == hash_session_token(first.token)
    assert first.token not in first.token_hash
    assert first.expires_at == 1_300


def test_session_expiry_and_revocation():
    assert session_is_active(expires_at=2_000, now=1_999)
    assert not session_is_active(expires_at=2_000, now=2_000)
    assert not session_is_active(expires_at=2_000, revoked_at=1_500, now=1_600)


def test_session_ttl_and_token_validation():
    with pytest.raises(ValueError):
        issue_session_token(ttl_seconds=30)
    with pytest.raises(ValueError):
        hash_session_token("tiny")
