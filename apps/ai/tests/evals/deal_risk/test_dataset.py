from pathlib import Path

import pytest

from apps.ai.evals.deal_risk.cases import DealRiskEvalCase
from apps.ai.evals.deal_risk.dataset import load_deal_risk_dataset


DATASET = Path("apps/ai/evals/deal_risk/cases.json")


def test_dataset_exists():
    assert DATASET.exists()


def test_dataset_has_17_cases():
    cases = load_deal_risk_dataset(DATASET)

    assert len(cases) == 17


def test_case_ids_are_unique():
    cases = load_deal_risk_dataset(DATASET)

    ids = [case.case_id for case in cases]

    assert len(ids) == len(set(ids))


def test_required_categories_exist():
    cases = load_deal_risk_dataset(DATASET)

    categories = {case.category for case in cases}

    assert "healthy" in categories
    assert "stale" in categories
    assert "missing_data" in categories
    assert "contradictory_signals" in categories
    assert "build_vs_buy" in categories
    assert "external_blocker" in categories
    assert "regulatory_tailwind" in categories
    assert "price_sensitive" in categories
    assert "financial_fragility" in categories


def test_required_risk_levels_exist():
    cases = load_deal_risk_dataset(DATASET)

    levels = {
        case.expected.risk_level
        for case in cases
    }

    assert {"low", "medium", "high"} <= levels


def test_cases_have_business_context():
    cases = load_deal_risk_dataset(DATASET)

    for case in cases:
        assert isinstance(case, DealRiskEvalCase)
        assert case.case_id
        assert case.description
        assert case.category
        assert case.evidence
        assert case.expected.risk_level in {
            "low",
            "medium",
            "high",
        }
        assert 0 <= case.expected.score_min <= 100
        assert 0 <= case.expected.score_max <= 100
        assert case.expected.score_min <= case.expected.score_max
        assert case.expected.recommended_action
        assert isinstance(case.required_signals, list)
        assert isinstance(case.forbidden_conclusions, list)


def test_business_specific_cases_exist():
    cases = {
        case.case_id: case
        for case in load_deal_risk_dataset(DATASET)
    }

    assert cases["DR-013"].category == "build_vs_buy"
    assert cases["DR-014"].category == "external_blocker"
    assert cases["DR-015"].category == "regulatory_tailwind"
    assert cases["DR-016"].category == "price_sensitive"
    assert cases["DR-017"].category == "financial_fragility"
