from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_sentiment_positive():
    response = client.post(
        "/ai/sentiment",
        json={
            "text": "This product is amazing, I love it!"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sentiment"] == "positive"
    assert 0 <= data["confidence"] <= 1


def test_sentiment_negative():
    response = client.post(
        "/ai/sentiment",
        json={
            "text": "This product is terrible and completely useless."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sentiment"] == "negative"
    assert 0 <= data["confidence"] <= 1


def test_sentiment_empty_text():
    response = client.post(
        "/ai/sentiment",
        json={
            "text": ""
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Le texte ne peut pas être vide"