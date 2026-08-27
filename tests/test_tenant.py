import pytest

from agents.tenant import (
    BRIGHTKIN_TENANT_ID,
    InvalidTenantError,
    get_tenant,
    normalize_new_tenant_id,
    normalize_tenant_id,
    reset_tenant,
    set_tenant,
)


def test_normalize_tenant_id_defaults_to_canonical_when_missing():
    assert normalize_tenant_id(None) == BRIGHTKIN_TENANT_ID
    assert normalize_tenant_id("") == BRIGHTKIN_TENANT_ID
    assert normalize_tenant_id("   ") == BRIGHTKIN_TENANT_ID


def test_normalize_tenant_id_accepts_canonical_explicitly():
    """Reading the real BrightKin data (the default, documented experience)
    is allowed - only *writing* to it via the intake endpoint is blocked."""
    assert normalize_tenant_id(BRIGHTKIN_TENANT_ID) == BRIGHTKIN_TENANT_ID


def test_normalize_tenant_id_accepts_a_valid_tester_uuid():
    tester_id = "3f9c1a2b-1111-2222-3333-abcdefabcdef"
    assert normalize_tenant_id(tester_id) == tester_id


@pytest.mark.parametrize("bad", ["../etc/passwd", "a b c", "a;b", "a'b", "x" * 65, 123, ["a"]])
def test_normalize_tenant_id_rejects_invalid_values(bad):
    with pytest.raises(InvalidTenantError):
        normalize_tenant_id(bad)


def test_normalize_new_tenant_id_rejects_the_reserved_sentinel():
    """The intake endpoint must never be able to target the real BrightKin
    tenant, no matter how a client tries to supply it."""
    with pytest.raises(InvalidTenantError):
        normalize_new_tenant_id(BRIGHTKIN_TENANT_ID)


@pytest.mark.parametrize("bad", [None, "", "   ", BRIGHTKIN_TENANT_ID, "has spaces", "semi;colon"])
def test_normalize_new_tenant_id_rejects_bad_or_reserved_values(bad):
    with pytest.raises(InvalidTenantError):
        normalize_new_tenant_id(bad)


def test_normalize_new_tenant_id_accepts_a_fresh_uuid():
    tester_id = "3f9c1a2b-1111-2222-3333-abcdefabcdef"
    assert normalize_new_tenant_id(tester_id) == tester_id


def test_get_tenant_defaults_to_canonical_outside_any_request():
    assert get_tenant() == BRIGHTKIN_TENANT_ID


def test_set_tenant_scopes_and_reset_restores_default():
    token = set_tenant("tester-xyz")
    try:
        assert get_tenant() == "tester-xyz"
    finally:
        reset_tenant(token)
    assert get_tenant() == BRIGHTKIN_TENANT_ID
