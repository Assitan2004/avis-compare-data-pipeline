from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_stats():
    response = client.get("/stats")

    assert response.status_code == 200

    data = response.json()

    assert "products" in data
    assert "reviews" in data
    assert "average_rating" in data
    assert "verified_reviews" in data

    assert data["products"] >= 0
    assert data["reviews"] >= 0


def test_products():
    response = client.get(
        "/products?limit=10&offset=0"
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "limit" in data
    assert "offset" in data
    assert "products" in data

    assert data["limit"] == 10
    assert data["offset"] == 0

    assert isinstance(
        data["products"],
        list
    )

    assert len(
        data["products"]
    ) <= 10

    if data["products"]:

        product = data["products"][0]

        assert "product_id" in product
        assert "name" in product
        assert "average_rating" in product
        assert "review_count" in product


def test_products_search():
    response = client.get(
        "/products/search?q=Echo&limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list
    )

    assert len(data) <= 10

    for product in data:
        assert "product_id" in product
        assert "name" in product
        assert "review_count" in product

        # Ta route recherche ne retourne
        # que les produits avec au moins 10 avis.
        assert product["review_count"] >= 10


def test_reviews():
    response = client.get(
        "/reviews?limit=3&offset=0"
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "total_count" in data
    assert "limit" in data
    assert "offset" in data
    assert "next_offset" in data
    assert "has_more" in data
    assert "reviews" in data

    assert data["limit"] == 3
    assert data["offset"] == 0

    assert isinstance(
        data["reviews"],
        list
    )

    assert len(
        data["reviews"]
    ) <= 3

    if data["reviews"]:

        review = data["reviews"][0]

        assert "review_id" in review
        assert "product_id" in review
        assert "product_name" in review
        assert "rating" in review
        assert "text" in review

        assert "sentiment" in review
        assert "confidence" in review

        assert "low_confidence" in review
        assert "prediction_reliable" in review

        assert "expected_from_rating" in review
        assert "is_consistent" in review
        assert "rating_sentiment_conflict" in review

        assert "warning" in review


def get_existing_product_id():
    """
    Récupère automatiquement un produit existant.

    Cela évite de dépendre d'un ID codé en dur.
    """

    response = client.get(
        "/products?limit=1&offset=0"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["products"]

    return data["products"][0][
        "product_id"
    ]


def test_product_detail():
    product_id = (
        get_existing_product_id()
    )

    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id

    assert "name" in data
    assert "average_rating" in data
    assert "review_count" in data


def test_product_reviews():
    product_id = (
        get_existing_product_id()
    )

    response = client.get(
        f"/products/{product_id}/reviews?limit=5"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list
    )

    assert len(data) <= 5

    if data:

        review = data[0]

        assert "review_id" in review
        assert "rating" in review
        assert "text" in review
        assert "review_date" in review
        assert "verified_purchase" in review


def test_product_sentiment_summary():
    product_id = (
        get_existing_product_id()
    )

    response = client.get(
        f"/products/{product_id}/sentiment-summary?limit=3"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id

    assert "product_name" in data

    assert (
        "total_reviews_analyzed"
        in data
    )

    assert "counts" in data
    assert "percentages" in data

    assert "reviews" in data

    assert (
        data["total_reviews_analyzed"]
        <= 3
    )

    counts = data["counts"]

    assert "positive" in counts
    assert "neutral" in counts
    assert "negative" in counts

    percentages = data[
        "percentages"
    ]

    assert "positive" in percentages
    assert "neutral" in percentages
    assert "negative" in percentages


def test_product_not_found():
    response = client.get(
        "/products/999999999"
    )

    assert response.status_code == 404


def test_sentiment_summary_product_not_found():
    response = client.get(
        "/products/999999999/sentiment-summary"
    )

    assert response.status_code == 404


def test_products_invalid_limit():
    response = client.get(
        "/products?limit=0"
    )

    assert response.status_code == 422


def test_reviews_invalid_limit():
    response = client.get(
        "/reviews?limit=0"
    )

    assert response.status_code == 422