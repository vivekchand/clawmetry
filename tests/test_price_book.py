"""Price book contract, Azure OpenAI aliases, Bedrock ids, effective dates (#5936).

REQ-OBS-CEA-024, "Price Book: negotiated rates, deployment aliases and effective
dates" (Software Factory). Criteria and the tests that hold them:

AC-OBS-CEA-024.1  test_accepts_exact_prefix_pattern_rates_and_discount
AC-OBS-CEA-024.2  test_rejects_each_bad_entry_with_a_reason_and_keeps_the_rest, test_overlapping_duplicates_are_both_rejected, test_conflicting_aliases_are_both_rejected, test_book_level_problems_make_the_book_unusable_not_a_crash, test_malformed_token_counts_never_crash_either_endpoint, test_malformed_token_counts_price_nothing_rather_than_an_undercount, test_odd_values_in_every_field_never_crash_the_api
AC-OBS-CEA-024.3  test_equal_precedence_is_ambiguous_and_chooses_nothing, test_channel_scoped_entry_outranks_a_generic_exact_one
AC-OBS-CEA-024.4  test_effective_date_boundary_is_half_open, test_record_without_observed_time_matches_no_dated_rate
AC-OBS-CEA-024.5  test_azure_deployment_resolves_through_resource_scoped_alias, test_alias_is_preferred_over_the_reported_model, test_alias_for_another_resource_does_not_apply, test_interceptor_captures_azure_openai_with_its_deployment
AC-OBS-CEA-024.6  test_bedrock_ids_resolve_to_the_entry_model, test_version_suffix_is_only_stripped_from_bedrock_ids
AC-OBS-CEA-024.7  test_editing_the_book_changes_the_version_and_old_versions_still_resolve, test_an_altered_version_file_is_refused
AC-OBS-CEA-024.8  test_no_published_rate_is_unknown_not_the_generic_default, test_provider_stand_in_is_labelled_default, test_figures_carry_the_shared_cost_basis_vocabulary
AC-OBS-CEA-024.9  test_valuations_without_their_basis_are_withheld, test_valuation_problems_contract, test_valuations_without_an_engine_says_unavailable_not_upgrade
AC-OBS-CEA-024.10 test_cache_convention_is_stated_per_source, test_hand_calculated_list_values_match
AC-OBS-CEA-024.11 test_no_off_machine_path_reads_the_price_book
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from clawmetry import price_book as pb
from clawmetry import providers_pricing as pp


@pytest.fixture(autouse=True)
def _scratch_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / "cm"))
    monkeypatch.setenv("CLAWMETRY_PRICE_BOOK", str(tmp_path / "cm" / "pricing.json"))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return tmp_path


def _book(entries=(), aliases=()):
    book = pb.parse_price_book({"schema": pb.SCHEMA, "entries": list(entries), "aliases": list(aliases)})
    book["present"] = True
    return book


def _rates(i, o, **extra):
    r = {"input_per_1m": i, "output_per_1m": o}
    r.update(extra)
    return r


BEDROCK_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
AZURE_URL = "https://contoso-east.openai.azure.com/openai/deployments/prod-chat/chat/completions?api-version=2024-10-21"


# ── AC-OBS-CEA-024.1 / .2: parsing and validation ──────────────────────────


def test_accepts_exact_prefix_pattern_rates_and_discount():
    book = _book([
        {"id": "exact", "model": "claude-sonnet-4-5", "effective_from": "2026-01-01", "rates": _rates(2.4, 12)},
        {"id": "prefix", "model_prefix": "gpt-4o", "effective_from": "2026-01-01T00:00:00Z", "discount_pct": 20},
        {"id": "pattern", "model_regex": r"gemini-2\.5-.*", "effective_from": "2026-01-01",
         "currency": "EUR", "rates": _rates(1, 2, cache_read_per_1m=0.1)},
    ])
    assert book["errors"] == [] and book["rejected"] == []
    assert [e["id"] for e in book["entries"]] == ["exact", "prefix", "pattern"]
    public = pb.public_book(book)
    assert public["entries"][1]["discount_pct"] == 20.0
    assert public["entries"][2]["rates"]["cache_read_per_1m"] == 0.1
    assert public["entries"][0]["effective_from"] == "2026-01-01T00:00:00Z"
    assert re.match(r"^pb1-[0-9a-f]{20}$", book["version"])


def test_rejects_each_bad_entry_with_a_reason_and_keeps_the_rest():
    book = _book([
        {"id": "good", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2, 8)},
        {"id": "typo", "model": "gpt-4o-mini", "effective_from": "2026-01-01", "rates": {"input": 1, "output_per_1m": 2}},
        {"id": "no-date", "model": "gpt-5", "rates": _rates(1, 1)},
        {"id": "naive", "model": "gpt-5", "effective_from": "2026-01-01T09:00:00", "rates": _rates(1, 1)},
        {"id": "both", "model": "gpt-5", "effective_from": "2026-01-01", "rates": _rates(1, 1), "discount_pct": 5},
        {"id": "two-kinds", "model": "a", "model_prefix": "b", "effective_from": "2026-01-01", "rates": _rates(1, 1)},
        {"id": "regex", "model_regex": "gpt-(", "effective_from": "2026-01-01", "rates": _rates(1, 1)},
        {"id": "neg", "model": "gpt-5", "effective_from": "2026-01-01", "rates": _rates(-1, 1)},
        {"id": "backwards", "model": "gpt-5", "effective_from": "2026-02-01", "effective_to": "2026-01-01", "rates": _rates(1, 1)},
        {"id": "eur-discount", "model": "gpt-5", "effective_from": "2026-01-01", "currency": "EUR", "discount_pct": 5},
        "not an object",
    ])
    assert [e["id"] for e in book["entries"]] == ["good"]
    by_id = {r["id"]: " ".join(r["problems"]) for r in book["rejected"]}
    assert "unknown rate field(s): input" in by_id["typo"]
    assert "effective_from is required" in by_id["no-date"]
    assert "no timezone" in by_id["naive"]
    assert "exactly one of rates or discount_pct" in by_id["both"]
    assert "exactly one of model, model_prefix, model_regex" in by_id["two-kinds"]
    assert "does not compile" in by_id["regex"]
    assert "at least 0" in by_id["neg"]
    assert "after effective_from" in by_id["backwards"]
    assert "currency must be USD" in by_id["eur-discount"]
    assert any(r["id"] is None and r["index"] == 10 for r in book["rejected"])


def test_overlapping_duplicates_are_both_rejected():
    book = _book([
        {"id": "a", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2, 8)},
        {"id": "b", "model": "GPT-4o", "effective_from": "2026-06-01", "rates": _rates(1, 4)},
        # Same model, adjacent (non-overlapping) window: fine.
        {"id": "c", "model": "claude-opus-4-8", "effective_from": "2026-01-01", "effective_to": "2026-07-01", "rates": _rates(4, 20)},
        {"id": "d", "model": "claude-opus-4-8", "effective_from": "2026-07-01", "rates": _rates(3, 15)},
        # Same model, different channel: fine.
        {"id": "e", "model": "gpt-4o", "channel": "azure-openai", "effective_from": "2026-01-01", "rates": _rates(2, 8)},
    ])
    assert sorted(e["id"] for e in book["entries"]) == ["c", "d", "e"]
    reasons = {r["id"]: r["problems"][0] for r in book["rejected"]}
    assert "overlaps entry 'b'" in reasons["a"] and "overlaps entry 'a'" in reasons["b"]


def test_conflicting_aliases_are_both_rejected():
    book = _book(aliases=[
        {"deployment": "prod-chat", "model": "gpt-4o", "resource": "contoso-east.openai.azure.com"},
        {"deployment": "Prod-Chat", "model": "gpt-4.1", "resource": "contoso-east.openai.azure.com"},
        {"deployment": "prod-chat", "model": "gpt-4o"},
        {"deployment": "", "model": "gpt-4o"},
    ])
    assert [a["deployment"] for a in book["aliases"]] == ["prod-chat"]
    assert book["aliases"][0]["resource"] is None
    kinds = [(r["kind"], r["index"]) for r in book["rejected"]]
    assert ("alias", 0) in kinds and ("alias", 1) in kinds and ("alias", 3) in kinds


def test_book_level_problems_make_the_book_unusable_not_a_crash(tmp_path):
    assert pb.parse_price_book([])["errors"]
    assert pb.parse_price_book({"entries": []})["errors"]
    assert pb.parse_price_book({"schema": pb.SCHEMA, "rates": []})["errors"]
    path = tmp_path / "cm" / "pricing.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not json")
    book = pb.load_price_book()
    assert book["present"] is True and book["version"] is None
    assert "not valid JSON" in book["errors"][0]
    # Nothing from the decoder's exception reaches a caller.
    assert "Expecting" not in book["errors"][0] and "char" not in book["errors"][0]
    r = pb.resolve_usage({"model": "gpt-4o", "observed_at": "2026-03-01"}, book)
    assert r["contract"]["status"] == "no_book" and "could not be used" in r["contract"]["reason"]
    assert r["book_version"] is None


def test_absent_book_is_a_normal_state():
    book = pb.load_price_book()
    assert book["present"] is False and book["errors"] == []
    r = pb.resolve_usage({"model": "gpt-4o", "observed_at": "2026-03-01"}, book)
    assert r["contract"]["status"] == "no_book"
    assert r["list"]["priced_from"] == "list"


# ── AC-OBS-CEA-024.3 / .4: selection ───────────────────────────────────────


def test_equal_precedence_is_ambiguous_and_chooses_nothing():
    book = _book([
        {"id": "rx1", "model_regex": r"gpt-5.*", "effective_from": "2026-01-01", "rates": _rates(1, 1)},
        {"id": "rx2", "model_regex": r"gpt-5\..*", "effective_from": "2026-01-01", "rates": _rates(2, 2)},
    ])
    r = pb.resolve_usage({"model": "gpt-5.1", "observed_at": "2026-03-01"}, book)
    assert r["contract"]["status"] == "ambiguous"
    assert r["contract"]["entry"] is None
    assert r["contract"]["candidates"] == ["rx1", "rx2"]


def test_channel_scoped_entry_outranks_a_generic_exact_one():
    book = _book([
        {"id": "generic", "model": "claude-sonnet-4-5", "effective_from": "2026-01-01", "rates": _rates(3, 15)},
        {"id": "bedrock", "model_prefix": "claude-", "channel": "aws-bedrock", "effective_from": "2026-01-01", "rates": _rates(2, 10)},
        {"id": "snapshot", "model": "claude-sonnet-4-5-20250929", "effective_from": "2026-01-01", "rates": _rates(2.9, 14)},
    ])
    assert pb.resolve_usage({"model": BEDROCK_ID, "observed_at": "2026-03-01"}, book)["contract"]["entry"]["id"] == "bedrock"
    # Direct Anthropic traffic: the dated snapshot entry beats the undated name.
    direct = pb.resolve_usage({"model": "claude-sonnet-4-5-20250929", "observed_at": "2026-03-01"}, book)
    assert direct["channel"] is None and direct["contract"]["entry"]["id"] == "snapshot"
    other = pb.resolve_usage({"model": "claude-sonnet-4-5-20251101", "observed_at": "2026-03-01"}, book)
    assert other["contract"]["entry"]["id"] == "generic"


def test_effective_date_boundary_is_half_open():
    book = _book([
        {"id": "h1", "model": "claude-sonnet-4-5", "channel": "aws-bedrock",
         "effective_from": "2026-01-01", "effective_to": "2026-07-01", "rates": _rates(2.4, 12)},
        {"id": "h2", "model": "claude-sonnet-4-5", "channel": "aws-bedrock",
         "effective_from": "2026-07-01", "rates": _rates(2.0, 10)},
    ])

    def entry_at(ts):
        r = pb.resolve_usage({"model": BEDROCK_ID, "observed_at": ts}, book)
        return r["contract"]["entry"]["id"] if r["contract"]["entry"] else r["contract"]["status"]

    assert entry_at("2025-12-31T23:59:59Z") == "no_entry"
    assert entry_at("2026-01-01T00:00:00Z") == "h1"
    assert entry_at("2026-06-30T23:59:59.999Z") == "h1"
    assert entry_at("2026-07-01T00:00:00Z") == "h2"
    assert entry_at("2026-07-01T02:00:00+02:00") == "h2"   # the same instant
    assert entry_at("2026-07-01T01:59:59+02:00") == "h1"
    assert entry_at(1782864000) == "h2"          # epoch seconds for 2026-07-01Z
    assert entry_at(1782863999000) == "h1"       # epoch milliseconds, one second before


def test_record_without_observed_time_matches_no_dated_rate():
    book = _book([{"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2, 8)}])
    r = pb.resolve_usage({"model": "gpt-4o"}, book)
    assert r["contract"]["status"] == "no_timestamp" and r["contract"]["entry"] is None


def test_discount_without_a_published_rate_is_not_priceable():
    book = _book([{"id": "d", "model_prefix": "mystery", "effective_from": "2026-01-01", "discount_pct": 10}])
    r = pb.resolve_usage({"model": "mystery-model-9", "provider": "acme", "observed_at": "2026-03-01"}, book)
    assert r["contract"]["status"] == "not_priceable"


# ── AC-OBS-CEA-024.5 / .6: Azure aliases and Bedrock ids ───────────────────


def _azure_book():
    return _book(
        [{"id": "az-4o", "model_prefix": "gpt-4o", "channel": "azure-openai", "effective_from": "2026-01-01", "discount_pct": 20}],
        [{"id": "east-prod", "deployment": "prod-chat", "model": "gpt-4o", "resource": "contoso-east.openai.azure.com"}],
    )


def test_azure_deployment_resolves_through_resource_scoped_alias():
    r = pb.resolve_usage({"url": AZURE_URL, "observed_at": "2026-03-01"}, _azure_book())
    assert r["channel"] == "azure-openai"
    assert r["model"]["deployment"] == "prod-chat"
    assert r["model"]["resource"] == "contoso-east.openai.azure.com"
    assert r["model"]["resolved"] == "gpt-4o" and r["model"]["via"] == "alias"
    assert r["model"]["alias_id"] == "east-prod"
    assert r["contract"]["status"] == "matched" and r["contract"]["entry"]["id"] == "az-4o"


def test_alias_is_preferred_over_the_reported_model():
    r = pb.resolve_usage({"url": AZURE_URL, "model": "gpt-4.1-2025-04-14", "observed_at": "2026-03-01"}, _azure_book())
    assert r["model"]["resolved"] == "gpt-4o" and r["model"]["via"] == "alias"
    assert "gpt-4.1-2025-04-14" in r["model"]["note"]
    # A dated snapshot of the alias model is not a conflict.
    same = pb.resolve_usage({"url": AZURE_URL, "model": "gpt-4o-2024-08-06", "observed_at": "2026-03-01"}, _azure_book())
    assert same["model"]["note"] is None


def test_alias_for_another_resource_does_not_apply():
    other = AZURE_URL.replace("contoso-east", "contoso-west")
    r = pb.resolve_usage({"url": other, "observed_at": "2026-03-01"}, _azure_book())
    assert r["model"]["via"] == "none" and r["contract"]["status"] == "no_model"
    assert r["list"]["priced_from"] == "unknown" and r["list"]["cost_usd"] is None
    # With the model reported by the response, it is used, labelled as such.
    r2 = pb.resolve_usage({"url": other, "model": "gpt-4o-2024-08-06", "observed_at": "2026-03-01"}, _azure_book())
    assert r2["model"]["via"] == "reported" and r2["contract"]["entry"]["id"] == "az-4o"


def test_bedrock_ids_resolve_to_the_entry_model():
    book = _book([{"id": "bed", "model": "claude-sonnet-4-5", "channel": "aws-bedrock", "effective_from": "2026-01-01", "rates": _rates(2.4, 12)}])
    for model in (
        BEDROCK_ID,
        "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    ):
        r = pb.resolve_usage({"model": model, "observed_at": "2026-03-01"}, book)
        assert r["channel"] == "aws-bedrock", model
        assert r["contract"]["entry"]["id"] == "bed", model
    assert pb.resolve_usage({"model": BEDROCK_ID, "observed_at": "2026-03-01"}, book)["region"] == "us"


def test_version_suffix_is_only_stripped_from_bedrock_ids():
    assert pb.canonical_model(BEDROCK_ID) == "claude-sonnet-4-5-20250929"
    assert pb.canonical_model("deepseek-v4") == "deepseek-v4"
    assert pb.canonical_model("moonshot-v1-8k") == "moonshot-v1-8k"
    assert pb.canonical_model("openrouter/anthropic/claude-opus-4-8") == "claude-opus-4-8"
    assert pb.canonical_model("meta.llama3-70b-instruct-v1") == "llama3-70b-instruct"


def test_azure_url_parser():
    assert pp.parse_azure_openai_url(AZURE_URL) == {"resource": "contoso-east.openai.azure.com", "deployment": "prod-chat"}
    v1 = pp.parse_azure_openai_url("https://r.openai.azure.com/openai/v1/chat/completions")
    assert v1 == {"resource": "r.openai.azure.com", "deployment": None}
    assert pp.parse_azure_openai_url("https://r.cognitiveservices.azure.com/speechtotext/v3.1/x") is None
    assert pp.parse_azure_openai_url("https://evil.example/openai/deployments/x") is None
    assert pp.parse_azure_openai_url("https://api.openai.com/v1/chat/completions") is None
    assert pp.parse_azure_openai_url(None) is None


def test_interceptor_captures_azure_openai_with_its_deployment():
    from clawmetry import interceptor as ci

    assert ci._is_llm_url(AZURE_URL) is True
    assert ci._is_llm_url("https://r.cognitiveservices.azure.com/vision/v3.2/analyze") is False
    assert ci._detect_provider(AZURE_URL) == "azure-openai"
    body = json.dumps({"model": "gpt-4o-2024-08-06", "usage": {"prompt_tokens": 1000, "completion_tokens": 50}}).encode()
    tokens = ci._extract_tokens_from_response(body, "azure-openai")
    assert (tokens["input_tokens"], tokens["output_tokens"]) == (1000, 50)
    ev = ci._build_event("azure-openai", AZURE_URL, "gpt-4o-2024-08-06", 1000, 50, 12.0, 200, "httpx")
    assert ev["deployment"] == "prod-chat" and ev["endpoint_host"] == "contoso-east.openai.azure.com"
    assert ev["cost_usd"] > 0
    # No model reported: the deployment name alone is not a price.
    bare = ci._build_event("azure-openai", AZURE_URL, None, 1000, 50, 12.0, 200, "httpx")
    assert "cost_usd" not in bare and bare["deployment"] == "prod-chat"


# ── AC-OBS-CEA-024.7: versions ─────────────────────────────────────────────


def _write_book(tmp_path, entries):
    path = tmp_path / "cm" / "pricing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": pb.SCHEMA, "entries": entries}))


def test_editing_the_book_changes_the_version_and_old_versions_still_resolve(tmp_path):
    fact = {"model": "gpt-4o", "observed_at": "2026-03-01"}
    _write_book(tmp_path, [{"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2.0, 8.0)}])
    v1_book = pb.load_price_book()
    assert pb.record_version(v1_book)
    v1 = v1_book["version"]

    _write_book(tmp_path, [{"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(1.5, 6.0)}])
    v2_book = pb.load_price_book()
    assert v2_book["version"] != v1
    assert pb.record_version(v2_book)

    old = pb.resolve_usage(fact, pb.load_version(v1))
    new = pb.resolve_usage(fact, pb.load_version(v2_book["version"]))
    assert old["contract"]["entry"]["rates"]["input_per_1m"] == 2.0 and old["book_version"] == v1
    assert new["contract"]["entry"]["rates"]["input_per_1m"] == 1.5
    assert pb.recorded_versions() == [v1, v2_book["version"]] or set(pb.recorded_versions()) == {v1, v2_book["version"]}
    # Recording again never rewrites the stored file.
    path = os.path.join(pb.versions_dir(), v1 + ".json")
    before = os.stat(path).st_mtime_ns
    assert pb.record_version(v1_book)
    assert os.stat(path).st_mtime_ns == before


def test_an_altered_version_file_is_refused(tmp_path):
    _write_book(tmp_path, [{"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2.0, 8.0)}])
    book = pb.load_price_book()
    pb.record_version(book)
    path = os.path.join(pb.versions_dir(), book["version"] + ".json")
    altered = {"schema": pb.SCHEMA, "entries": [
        {"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(0.5, 8.0)}]}
    with open(path, "w") as fh:
        fh.write(json.dumps(altered))
    assert pb.load_version(book["version"]) is None
    assert pb.load_version("../../etc/passwd") is None


# ── AC-OBS-CEA-024.8 / .10: list basis and cache convention ────────────────


def test_no_published_rate_is_unknown_not_the_generic_default():
    assert pp.rate_basis("", "mystery-model") == (1.0, 3.0, "unknown_default")
    r = pb.resolve_usage({"model": "mystery-model", "observed_at": "2026-03-01", "input_tokens": 1000}, _book())
    assert r["list"]["priced_from"] == "unknown"
    assert r["list"]["cost_usd"] is None and r["list"]["input_per_1m"] is None


def test_provider_stand_in_is_labelled_default():
    assert pp.rate_basis("anthropic", "claude-future-9")[2] == "provider_baseline"
    r = pb.resolve_usage({"model": "claude-future-9", "input_tokens": 1000}, _book())
    assert r["list"]["priced_from"] == "default" and r["list"]["rate_source"] == "provider_baseline"
    assert r["list"]["reason"]


def test_figures_carry_the_shared_cost_basis_vocabulary():
    # One vocabulary for "what kind of money is this" (clawmetry/cost_basis.py):
    # a list figure is published-rate money, no amount is unknown, and a
    # contract figure without its rate version cannot claim to be contract.
    from clawmetry import cost_basis as cb

    priced = pb.resolve_usage({"model": "gpt-4o", "observed_at": "2026-03-01", "input_tokens": 1000}, _book())
    assert priced["list"]["cost_usd"] is not None
    assert priced["list"]["cost_basis"] == cb.PUBLISHED_RATE
    assert priced["list"]["cost_basis_label"] == cb.COST_BASIS_LABEL[cb.PUBLISHED_RATE]
    unpriced = pb.resolve_usage({"model": "mystery-model", "input_tokens": 1000}, _book())
    assert unpriced["list"]["cost_basis"] == cb.UNKNOWN
    assert pb.financial_basis("contract", 1.0, "pb1-" + "a" * 20)["cost_basis"] == cb.CONTRACT
    assert pb.financial_basis("contract", 1.0, None)["cost_basis"] == cb.UNKNOWN
    assert pb.financial_basis("vendor_reported", 1.0, None)["cost_basis"] == cb.PUBLISHED_RATE
    assert pb.financial_basis("list", None, pb.LIST_RATE_VERSION)["cost_basis"] == cb.UNKNOWN
    assert pb.financial_basis("guess", 1.0)["cost_basis"] == cb.UNKNOWN
    assert set(pb._COST_BASIS_FOR) == set(pb.PRICED_FROM)


def test_rate_basis_keeps_the_published_rates():
    assert pp._get_rates("anthropic", "claude-opus-4-8") == (5.00, 25.00)
    assert pp.rate_basis("anthropic", "claude-opus-4-8") == (5.00, 25.00, "model")
    assert pp.rate_basis("openai", "gpt-4o") == (2.50, 10.00, "model")
    assert pp.rate_basis("azure-openai", "gpt-4o") == (2.50, 10.00, "model")
    assert pp.rate_basis("ollama", "llama3") == (0.0, 0.0, "local")
    assert pp.rate_basis("mistral", "mistral-tiny-x") == (2.00, 6.00, "provider_baseline")


def test_cache_convention_is_stated_per_source():
    assert pb.resolve_usage({"model": BEDROCK_ID}, _book())["cache_tokens_in_input"] is False
    assert pb.resolve_usage({"model": "claude-opus-4-8"}, _book())["cache_tokens_in_input"] is False
    assert pb.resolve_usage({"url": AZURE_URL, "model": "gpt-4o"}, _book())["cache_tokens_in_input"] is True
    assert pb.resolve_usage({"model": "gpt-4o"}, _book())["cache_tokens_in_input"] is True
    assert pb.resolve_usage({"model": "mystery-model"}, _book())["cache_tokens_in_input"] is None


def test_hand_calculated_list_values_match():
    # Claude Sonnet 4.5 on Bedrock at Anthropic's published rate (Bedrock's own
    # list can differ): cache reads are ADDITIONAL to input.
    #   1,000,000 input x $3.00 + 100,000 output x $15.00 + 400,000 cache read x $0.30
    #   = 3.00 + 1.50 + 0.12 = $4.62
    bed = pb.resolve_usage({"model": BEDROCK_ID, "input_tokens": 1_000_000, "output_tokens": 100_000,
                            "cache_read_tokens": 400_000}, _book())
    assert bed["list"]["cost_usd"] == pytest.approx(4.62)
    assert "Bedrock" in bed["list"]["reason"]
    # gpt-4o behind an Azure deployment alias, list: cached tokens are INSIDE input.
    #   600,000 uncached x $2.50 + 400,000 cached x $1.25 + 100,000 output x $10.00
    #   = 1.50 + 0.50 + 1.00 = $3.00
    az = pb.resolve_usage({"url": AZURE_URL, "observed_at": "2026-03-01", "input_tokens": 1_000_000,
                           "output_tokens": 100_000, "cache_read_tokens": 400_000}, _azure_book())
    assert az["list"]["cost_usd"] == pytest.approx(3.00)
    assert "Azure" in az["list"]["reason"]


# ── AC-OBS-CEA-024.9: the API and the valuation contract ───────────────────


@pytest.fixture()
def client():
    from flask import Flask

    from routes.pricing import bp_pricing

    app = Flask(__name__)
    app.register_blueprint(bp_pricing)
    return app.test_client()


def _good_valuation(**over):
    rec = {"priced_from": "contract", "amount": 1.25, "currency": "USD", "rate_version": "pb1-" + "a" * 20,
           "effective_from": "2026-01-01T00:00:00Z", "effective_to": None, "restated": False}
    rec.update(over)
    return rec


def test_valuation_problems_contract():
    assert pb.valuation_problems(_good_valuation()) == []
    assert pb.valuation_problems(_good_valuation(priced_from="unknown", amount=None, rate_version=None,
                                                 effective_from=None, currency=None)) == []
    assert any("amount" in p for p in pb.valuation_problems(_good_valuation(priced_from="unknown")))
    assert any("priced_from" in p for p in pb.valuation_problems(_good_valuation(priced_from="guess")))
    assert any("effective_from" in p for p in pb.valuation_problems(_good_valuation(effective_from=None)))
    assert any("restatement_of" in p for p in pb.valuation_problems(_good_valuation(restated=True)))
    assert pb.valuation_problems(_good_valuation(restated=True, restatement_of="val-1",
                                                 original_rate_version="pb1-" + "b" * 20)) == []
    missing = _good_valuation()
    del missing["rate_version"]
    assert "rate_version is missing" in pb.valuation_problems(missing)
    assert pb.valuation_problems("nope")


def test_valuations_without_their_basis_are_withheld(client):
    from clawmetry import extensions

    seen = {}

    def engine(payload):
        seen.update(payload)
        return {"valuations": [_good_valuation(), {"amount": 9.99}]}

    extensions.register(pb.VALUE_USAGE_EVENT, engine)
    try:
        resp = client.post("/api/pricing/valuations", json={"facts": [{"model": "gpt-4o", "observed_at": "2026-03-01"}]})
    finally:
        extensions.unregister(pb.VALUE_USAGE_EVENT, engine)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["valuations"] == [dict(_good_valuation(), cost_basis="contract", cost_basis_label="contract rate")]
    assert body["withheld"][0]["index"] == 1 and "priced_from is missing" in body["withheld"][0]["problems"]
    assert seen["resolutions"][0]["model"]["resolved"] == "gpt-4o"
    assert resp.headers["Cache-Control"] == "no-store"


def test_valuations_without_an_engine_says_unavailable_not_upgrade(client):
    # No build ships a valuation engine yet, so "upgrade" would sell a plan
    # that does not contain one, and tell a Pro user to buy what they have.
    resp = client.post("/api/pricing/valuations", json={"facts": [{"model": "gpt-4o"}]})
    assert resp.status_code == 501
    body = resp.get_json()
    assert body["error"] == "valuation_engine_unavailable"
    assert "required_tier" not in body and "upgrade" not in json.dumps(body).lower()
    assert "/api/pricing/resolve" in body["message"]
    assert resp.headers["Cache-Control"] == "no-store"


_BAD_TOKEN_VALUES = ['"abc"', "Infinity", "-Infinity", "NaN", "1e400", "-5", "true", "[]", "{}", '"12"']


@pytest.mark.parametrize("path", ["/api/pricing/resolve", "/api/pricing/valuations"])
@pytest.mark.parametrize("raw", _BAD_TOKEN_VALUES)
def test_malformed_token_counts_never_crash_either_endpoint(client, path, raw):
    # Raw JSON on purpose: Python's decoder accepts Infinity, NaN and 1e400.
    data = '{"facts": [{"model": "gpt-4o", "observed_at": "2026-03-01", "input_tokens": 5, "output_tokens": %s}]}' % raw
    resp = client.post(path, data=data, content_type="application/json")
    assert resp.status_code in (200, 501), resp.data[:300]
    body = resp.get_json()
    assert isinstance(body, dict)
    if path.endswith("/resolve"):
        listed = body["resolutions"][0]["list"]
        assert listed["cost_usd"] is None
        assert "output_tokens" in listed["reason"]


def test_malformed_token_counts_price_nothing_rather_than_an_undercount():
    ok = pb.resolve_usage({"model": "gpt-4o", "input_tokens": 1_000_000, "output_tokens": 0})
    assert ok["list"]["cost_usd"] == pytest.approx(2.50)
    for bad in ("abc", float("inf"), float("nan"), -1, True, [1], {"n": 1}, "1000000"):
        res = pb.resolve_usage({"model": "gpt-4o", "input_tokens": 1_000_000, "output_tokens": bad})
        assert res["list"]["cost_usd"] is None, bad
        assert "output_tokens" in res["list"]["reason"], bad
    # A field that is simply absent or null is not malformed.
    assert pb.resolve_usage({"model": "gpt-4o", "input_tokens": 1_000_000,
                             "output_tokens": None})["list"]["cost_usd"] == pytest.approx(2.50)


def test_odd_values_in_every_field_never_crash_the_api(client):
    odd = [None, True, -1, 1e308, [], {}, "", "x" * 300, "Infinity"]
    fields = ["request_id", "observed_at", "provider", "model", "deployment", "resource", "url",
              "channel", "region", "input_tokens", "output_tokens", "cache_read_tokens",
              "cache_write_tokens", "vendor_reported_cost_usd"]
    facts = [{f: v, "model": "gpt-4o"} if f != "model" else {f: v} for f in fields for v in odd]
    facts.append("not an object")
    for path in ("/api/pricing/resolve", "/api/pricing/valuations"):
        resp = client.post(path, json={"facts": facts})
        assert resp.status_code in (200, 501), (path, resp.data[:300])
    for key in ("book_version", "restate_against"):
        for v in ([], {}, 7, True, "../../etc/passwd"):
            resp = client.post("/api/pricing/valuations", json={"facts": [{"model": "gpt-4o"}], key: v})
            assert resp.status_code in (404, 501), (key, v, resp.data[:300])


def test_book_and_resolve_endpoints(client, tmp_path):
    empty = client.get("/api/pricing/book").get_json()
    assert empty["present"] is False and empty["entries"] == [] and empty["versions"] == []

    _write_book(tmp_path, [
        {"id": "x", "model": "gpt-4o", "effective_from": "2026-01-01", "rates": _rates(2.0, 8.0)},
        {"id": "bad", "model": "gpt-4o-mini", "rates": _rates(1, 1)},
    ])
    book = client.get("/api/pricing/book").get_json()
    assert book["present"] is True and [e["id"] for e in book["entries"]] == ["x"]
    assert book["rejected"][0]["id"] == "bad"

    resp = client.post("/api/pricing/resolve", json={"facts": [{"model": "gpt-4o", "observed_at": "2026-03-01"}]})
    assert resp.status_code == 200
    out = resp.get_json()
    assert out["book_version"] == book["version"]
    assert out["resolutions"][0]["contract"]["entry"]["id"] == "x"
    assert client.get("/api/pricing/book").get_json()["versions"] == [book["version"]]

    missing = client.post("/api/pricing/resolve", json={"facts": [{}], "book_version": "pb1-" + "0" * 20})
    assert missing.status_code == 404 and missing.get_json()["error"] == "unknown_book_version"
    assert client.post("/api/pricing/resolve", json={"facts": []}).status_code == 400
    assert client.post("/api/pricing/resolve", data="x", content_type="text/plain").status_code == 400
    too_many = client.post("/api/pricing/resolve", json={"facts": [{}] * 1001})
    assert too_many.status_code == 400


def test_routes_are_gated_on_the_price_book_feature():
    from clawmetry import entitlements as ent

    assert "price_book" in ent.PRO_ONLY_FEATURES
    assert ent.FEATURE_LABELS["price_book"] == "Price book"
    with open(os.path.join(_REPO, "routes", "pricing.py"), encoding="utf-8") as fh:
        src = fh.read()
    assert src.count('@gate("price_book")') == 4
    assert len(re.findall(r"@bp_pricing\.route\(", src)) == 4


# ── AC-OBS-CEA-024.11: the customer boundary ───────────────────────────────


def test_no_off_machine_path_reads_the_price_book():
    """Every module that ships data off the machine, or serves the cloud relay,
    must not touch the price book or its version store."""
    off_machine = [
        "clawmetry/sync.py", "clawmetry/telemetry.py", "clawmetry/otel_exporter.py",
        "clawmetry/local_server.py", "clawmetry/local_store.py", "routes/otel_export.py",
        "routes/local_query.py", "routes/heartbeat.py", "routes/meta.py",
    ]
    offenders = []
    for rel in off_machine:
        path = os.path.join(_REPO, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        if re.search(r"price_book|pricing\.json|pricing_versions|/api/pricing/", src):
            offenders.append(rel)
    assert offenders == [], offenders
