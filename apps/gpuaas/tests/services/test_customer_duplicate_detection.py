from apps.gpuaas.app.services.customer_duplicate_detection import (
    DuplicateCandidate,
    CustomerDuplicateDetectionService,
)


def build_service():
    return CustomerDuplicateDetectionService()


def test_matching_email_is_duplicate_candidate():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
        },
        {
            "id": "customer-2",
            "company_name": "Acme Compute",
            "email": "HELLO@ACME.AI",
        },
    ]

    result = service.find_candidates(records)

    assert len(result) == 1

    candidate = result[0]

    assert isinstance(candidate, DuplicateCandidate)
    assert candidate.left_id == "customer-1"
    assert candidate.right_id == "customer-2"
    assert "email" in candidate.match_reasons


def test_matching_company_name_is_duplicate_candidate():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": "  Acme   AI ",
            "email": "one@acme.ai",
        },
        {
            "id": "customer-2",
            "company_name": "ACME AI",
            "email": "two@acme.ai",
        },
    ]

    result = service.find_candidates(records)

    assert len(result) == 1
    assert result[0].match_reasons == ["company_name"]


def test_email_and_company_name_can_both_match():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
        },
        {
            "id": "customer-2",
            "company_name": "ACME AI",
            "email": "HELLO@ACME.AI",
        },
    ]

    result = service.find_candidates(records)

    assert len(result) == 1
    assert set(result[0].match_reasons) == {
        "company_name",
        "email",
    }


def test_different_records_are_not_duplicate_candidates():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": "Acme AI",
            "email": "one@acme.ai",
        },
        {
            "id": "customer-2",
            "company_name": "Beta Compute",
            "email": "two@beta.com",
        },
    ]

    result = service.find_candidates(records)

    assert result == []


def test_missing_identity_fields_are_not_duplicate_candidates():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": None,
            "email": None,
        },
        {
            "id": "customer-2",
            "company_name": None,
            "email": None,
        },
    ]

    result = service.find_candidates(records)

    assert result == []


def test_same_record_is_never_compared_with_itself():
    service = build_service()

    records = [
        {
            "id": "customer-1",
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
        }
    ]

    result = service.find_candidates(records)

    assert result == []
