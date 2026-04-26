"""Pytest suite for review workflows with in-memory DB and API filters."""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database.review import ReviewRepository
from app.models import Review, ReviewCreate
from app.service.review import ReviewService
from app.utils.enums import ReviewClassification
from tests.conftest import FakeReviewClassifier


def _patch_classifier(monkeypatch, fake_classifier: FakeReviewClassifier) -> None:
    monkeypatch.setattr(
        "app.service.review.get_review_classifier",
        lambda: fake_classifier,
    )


def _create_review_payload(review: dict[str, str]) -> dict[str, str]:
    return {
        "customer_name": review["customer_name"],
        "review_date": review["review_date"],
        "review_text": review["review_text"],
    }


def test_service_create_review_persists_data(
    session: Session,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    repository = ReviewRepository(session)
    service = ReviewService(repository)
    payload = ReviewCreate(
        customer_name="Teste",
        review_date=datetime.fromisoformat("2026-04-25T09:00:00"),
        review_text="Produto excelente e entrega rapida.",
    )

    created = service.create_review(payload)

    assert created.id is not None
    assert created.classification == ReviewClassification.positiva

    saved = session.get(Review, created.id)
    assert saved is not None
    assert saved.classification == ReviewClassification.positiva
    assert saved.customer_name == "Teste"


def test_api_list_reviews_with_date_filters(
    client: TestClient,
    seed_reviews: list[dict[str, str]],
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    for review in seed_reviews:
        response = client.post("/reviews", json=_create_review_payload(review))
        assert response.status_code == 201

    target_date = seed_reviews[1]["review_date"][:10]
    expected_count = sum(
        1 for review in seed_reviews if review["review_date"][:10] == target_date
    )
    response = client.get(
        "/reviews",
        params={
            "start_date": f"{target_date}T00:00:00",
            "end_date": f"{target_date}T23:59:59",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == expected_count
    pg = data["pagination"]
    assert pg["total"] == expected_count
    assert pg["page"] == 1
    assert pg["itens"] == expected_count
    assert pg["last_page"] == (0 if expected_count == 0 else 1)


def test_api_report_groups_by_classification(
    client: TestClient,
    seed_reviews: list[dict[str, str]],
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    for review in seed_reviews:
        response = client.post("/reviews", json=_create_review_payload(review))
        assert response.status_code == 201

    date_values = [
        datetime.fromisoformat(review["review_date"]) for review in seed_reviews
    ]
    start_date = min(date_values).strftime("%Y-%m-%dT00:00:00")
    end_date = max(date_values).strftime("%Y-%m-%dT23:59:59")
    response = client.get(
        "/reviews/report",
        params={
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    assert response.status_code == 200
    report = response.json()
    assert report["total_reviews"] == len(seed_reviews)

    grouped = {
        item["classification"]: item["total"] for item in report["by_classification"]
    }
    expected_grouped = {
        ReviewClassification.positiva.value: 0,
        ReviewClassification.neutra.value: 0,
        ReviewClassification.negativa.value: 0,
    }
    for review in seed_reviews:
        expected_grouped[fake_classifier.classify(review["review_text"])] += 1

    assert (
        grouped.get(ReviewClassification.positiva.value, 0)
        == expected_grouped[ReviewClassification.positiva.value]
    )
    assert (
        grouped.get(ReviewClassification.neutra.value, 0)
        == expected_grouped[ReviewClassification.neutra.value]
    )
    assert (
        grouped.get(ReviewClassification.negativa.value, 0)
        == expected_grouped[ReviewClassification.negativa.value]
    )


def test_api_create_review_rejects_empty_review_text(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    payload = {
        "customer_name": "Cliente sem texto",
        "review_date": "2026-04-25T10:00:00",
        "review_text": "",
    }

    response = client.post("/reviews", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == "review_text" for error in errors)


def test_api_list_reviews_rejects_invalid_date_range(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get(
        "/reviews",
        params={
            "start_date": "2026-04-30T23:59:59",
            "end_date": "2026-04-01T00:00:00",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "start_date must be less than or equal to end_date."
    )


def test_api_get_review_by_id_returns_404_when_not_found(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews/999999")

    assert response.status_code == 404
    assert "Review not found" in response.json()["detail"]


def test_api_create_review_rejects_whitespace_only_review_text(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    payload = {
        "customer_name": "Cliente sem conteudo",
        "review_date": "2026-04-25T10:00:00",
        "review_text": "   ",
    }

    response = client.post("/reviews", json=payload)

    assert response.status_code == 422
    assert any(error["loc"][-1] == "review_text" for error in response.json()["detail"])


def test_api_create_review_rejects_whitespace_only_customer_name(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    payload = {
        "customer_name": "   ",
        "review_date": "2026-04-25T10:00:00",
        "review_text": "Texto valido",
    }

    response = client.post("/reviews", json=payload)

    assert response.status_code == 422
    assert any(
        error["loc"][-1] == "customer_name" for error in response.json()["detail"]
    )


def test_api_list_reviews_empty_database_has_zero_last_page(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    pg = body["pagination"]
    assert pg["total"] == 0
    assert pg["itens"] == 0
    assert pg["last_page"] == 0
    assert pg["page"] == 1


def test_api_list_reviews_pagination_two_pages(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    total_rows = 60
    for i in range(total_rows):
        response = client.post(
            "/reviews",
            json={
                "customer_name": f"Cliente {i}",
                "review_date": "2026-06-01T12:00:00",
                "review_text": f"Produto excelente pacote {i}.",
            },
        )
        assert response.status_code == 201

    first = client.get("/reviews", params={"page": 1, "limit": 50})
    assert first.status_code == 200
    body1 = first.json()
    assert len(body1["items"]) == 50
    assert body1["pagination"]["total"] == total_rows
    assert body1["pagination"]["last_page"] == 2
    assert body1["pagination"]["itens"] == 50
    assert body1["pagination"]["page"] == 1

    second = client.get("/reviews", params={"page": 2, "limit": 50})
    assert second.status_code == 200
    body2 = second.json()
    assert len(body2["items"]) == 10
    assert body2["pagination"]["itens"] == 10
    assert body2["pagination"]["page"] == 2
    assert body2["pagination"]["total"] == total_rows

    beyond = client.get("/reviews", params={"page": 3, "limit": 50})
    assert beyond.status_code == 200
    body3 = beyond.json()
    assert body3["items"] == []
    assert body3["pagination"]["page"] == 3
    assert body3["pagination"]["itens"] == 0
    assert body3["pagination"]["total"] == total_rows
    assert body3["pagination"]["last_page"] == 2


def test_api_list_reviews_rejects_limit_below_min(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews", params={"limit": 49, "page": 1})
    assert response.status_code == 422
    detail = response.json()["detail"]
    detail_text = (
        detail
        if isinstance(detail, str)
        else " ".join(str(d.get("msg", d)) for d in detail)
    ).lower()
    assert "50" in detail_text or "greater" in detail_text


def test_api_list_reviews_rejects_limit_above_max(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews", params={"limit": 201, "page": 1})
    assert response.status_code == 422


def test_api_list_reviews_rejects_page_zero(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews", params={"page": 0, "limit": 50})
    assert response.status_code == 422


def test_api_list_reviews_rejects_malformed_start_date(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get(
        "/reviews",
        params={
            "start_date": "not-a-date",
            "end_date": "2026-04-01T00:00:00",
        },
    )

    assert response.status_code == 422


def test_api_report_rejects_invalid_date_range(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get(
        "/reviews/report",
        params={
            "start_date": "2026-05-10T00:00:00",
            "end_date": "2026-05-01T00:00:00",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "start_date must be less than or equal to end_date."
    )


def test_api_get_review_by_id_returns_404_when_filtered_out_by_period(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    create_payload = {
        "customer_name": "Cliente filtro",
        "review_date": "2026-04-10T08:00:00",
        "review_text": "Atendimento excelente.",
    }
    created = client.post("/reviews", json=create_payload)
    assert created.status_code == 201
    review_id = created.json()["id"]

    response = client.get(
        f"/reviews/{review_id}",
        params={
            "start_date": "2026-04-11T00:00:00",
            "end_date": "2026-04-12T23:59:59",
        },
    )

    assert response.status_code == 404
    assert "Review not found" in response.json()["detail"]


def test_api_get_review_by_id_returns_200(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    create_payload = {
        "customer_name": "Cliente API",
        "review_date": "2026-04-15T14:30:00",
        "review_text": "Entrega rapida, produto excelente.",
    }
    create_response = client.post("/reviews", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    review_id = created["id"]

    get_api = f"/reviews/{review_id}"
    get_response = client.get(get_api)
    assert get_response.status_code == 200, get_api

    body = get_response.json()
    assert body["id"] == review_id
    assert body["customer_name"] == create_payload["customer_name"]
    assert body["review_text"] == create_payload["review_text"]
    assert body["classification"] == "positiva"
    assert "2026-04-15" in body["review_date"]


def test_api_list_reviews_order_by_id_without_date_filter(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    for label in ("c", "a", "b"):
        response = client.post(
            "/reviews",
            json={
                "customer_name": label,
                "review_date": "2026-08-10T10:00:00",
                "review_text": f"Texto excelente {label} para o teste de ordem.",
            },
        )
        assert response.status_code == 201

    res = client.get("/reviews", params={"limit": 50, "page": 1})
    assert res.status_code == 200
    items = res.json()["items"]
    ids = [row["id"] for row in items]
    assert ids == sorted(ids)
    assert [row["customer_name"] for row in items] == ["c", "a", "b"]


def test_api_list_reviews_order_by_date_when_date_params_present(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    client.post(
        "/reviews",
        json={
            "customer_name": "Mais recente",
            "review_date": "2026-09-20T10:00:00",
            "review_text": "Nao gostei, veio com defeito no segundo.",
        },
    )
    client.post(
        "/reviews",
        json={
            "customer_name": "Mais antigo",
            "review_date": "2026-09-10T10:00:00",
            "review_text": "Defeito no primeiro lote, nao gostei.",
        },
    )

    res = client.get(
        "/reviews",
        params={
            "start_date": "2026-09-01T00:00:00",
            "end_date": "2026-09-30T23:59:59",
            "limit": 50,
            "page": 1,
        },
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    assert items[0]["customer_name"] == "Mais antigo"
    assert items[1]["customer_name"] == "Mais recente"
    dates = [r["review_date"] for r in items]
    assert dates == sorted(dates)


def test_api_list_reviews_with_classification_filter(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    positiva = {
        "customer_name": "P1",
        "review_date": "2026-11-10T10:00:00",
        "review_text": "Tudo excelente, recomendo a loja toda.",
    }
    outra = {
        "customer_name": "N1",
        "review_date": "2026-11-11T10:00:00",
        "review_text": "Nao gostei do material com defeito.",
    }
    assert client.post("/reviews", json=positiva).status_code == 201
    assert client.post("/reviews", json=positiva).status_code == 201
    assert client.post("/reviews", json=outra).status_code == 201

    response = client.get(
        "/reviews",
        params={"classification": "positiva", "limit": 50, "page": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert all(item["classification"] == "positiva" for item in body["items"])
    assert body["pagination"]["total"] == 2


def test_api_get_review_by_id_404_for_classification_mismatch(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    create = client.post(
        "/reviews",
        json={
            "customer_name": "Positivo",
            "review_date": "2026-10-01T10:00:00",
            "review_text": "Tudo excelente, entrega rapida.",
        },
    )
    assert create.status_code == 201
    rid = create.json()["id"]
    response = client.get(f"/reviews/{rid}", params={"classification": "negativa"})
    assert response.status_code == 404
    assert "Review not found" in response.json()["detail"]


def test_api_report_respects_classification_filter(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    start = "2026-10-01T00:00:00"
    end = "2026-10-31T23:59:59"
    for label, text in (
        ("A", "Resultado mediano, nem bom nem ruim."),
        ("B", "A experiencia foi mediana, poderia ser melhor."),
        ("C", "Produto excelente, entrega rapida."),
    ):
        r = client.post(
            "/reviews",
            json={
                "customer_name": label,
                "review_date": "2026-10-15T10:00:00",
                "review_text": text,
            },
        )
        assert r.status_code == 201

    r_all = client.get(
        "/reviews/report", params={"start_date": start, "end_date": end}
    )
    r_one = client.get(
        "/reviews/report",
        params={
            "start_date": start,
            "end_date": end,
            "classification": "neutra",
        },
    )
    assert r_all.status_code == 200
    assert r_one.status_code == 200
    full = r_all.json()
    narrow = r_one.json()
    assert full["total_reviews"] == 3
    assert narrow["total_reviews"] == 2
    assert len(narrow["by_classification"]) == 1
    assert narrow["by_classification"][0]["classification"] == "neutra"
    assert narrow["by_classification"][0]["total"] == 2


def test_api_rejects_invalid_classification_value(
    client: TestClient,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    response = client.get("/reviews", params={"classification": "mista"})
    assert response.status_code == 422
