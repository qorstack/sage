"""Tests for cognition packs."""

from knowai.packs.builtin import get_pack, get_packs_for_domains, BUILTIN_PACKS


def test_all_packs_have_required_fields():
    for domain, pack in BUILTIN_PACKS.items():
        assert pack.business_rules, f"{domain} pack missing business_rules"
        assert pack.common_requirements, f"{domain} pack missing common_requirements"
        assert pack.risk_flags, f"{domain} pack missing risk_flags"
        assert pack.required_workflow, f"{domain} pack missing required_workflow"


def test_get_payment_pack():
    pack = get_pack("payment")
    assert pack is not None
    assert pack.domain == "payment"
    assert any("idempotent" in r.lower() for r in pack.business_rules)
    assert "webhook" in pack.related_domains


def test_get_auth_pack():
    pack = get_pack("auth")
    assert pack is not None
    assert any("rate" in r.lower() for r in pack.business_rules)


def test_get_unknown_pack():
    assert get_pack("nonexistent_domain") is None


def test_get_packs_for_domains():
    packs = get_packs_for_domains(["payment", "webhook", "unknown_domain"])
    assert len(packs) == 2
    domains = {p.domain for p in packs}
    assert "payment" in domains
    assert "webhook" in domains


def test_no_duplicate_packs():
    packs = get_packs_for_domains(["payment", "payment", "auth"])
    assert len(packs) == 2
