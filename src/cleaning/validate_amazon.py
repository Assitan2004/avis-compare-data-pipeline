import json
import re
from pathlib import Path
from datetime import datetime


INPUT_FILE = Path(
    "data/processed/amazon_reviews_clean.json"
)


def is_valid_date(value):
    """Vérifie que la date respecte YYYY-MM-DD."""

    if not value:
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def main():

    print("==============================")
    print("VALIDATION AMAZON REVIEWS")
    print("==============================")

    # Chargement du fichier nettoyé
    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        reviews = json.load(file)

    print(f"\nNombre d'avis : {len(reviews)}")

    empty_text = 0
    invalid_rating = 0
    missing_asin = 0
    invalid_date = 0
    html_remaining = 0
    invalid_helpful_vote = 0
    invalid_verified_purchase = 0

    duplicate_count = 0
    seen = set()

    for review in reviews:

        # 1. Texte obligatoire
        text = review.get("text")

        if not text or not text.strip():
            empty_text += 1

        # 2. Note entre 1 et 5
        rating = review.get("rating")

        if (
            not isinstance(rating, (int, float))
            or isinstance(rating, bool)
            or not 1 <= rating <= 5
        ):
            invalid_rating += 1

        # 3. ASIN obligatoire
        asin = review.get("asin")

        if not asin:
            missing_asin += 1

        # 4. Date correcte
        review_date = review.get("review_date")

        if not is_valid_date(review_date):
            invalid_date += 1

        # 5. Vérification HTML
        if text and re.search(r"<[^>]+>", text):
            html_remaining += 1

        # 6. helpful_vote
        helpful_vote = review.get("helpful_vote")

        if (
            not isinstance(helpful_vote, int)
            or isinstance(helpful_vote, bool)
            or helpful_vote < 0
        ):
            invalid_helpful_vote += 1

        # 7. verified_purchase doit être booléen
        if not isinstance(
            review.get("verified_purchase"),
            bool
        ):
            invalid_verified_purchase += 1

        # 8. Recherche de doublons
        duplicate_key = (
            asin,
            review_date,
            review.get("title"),
            text
        )

        if duplicate_key in seen:
            duplicate_count += 1
        else:
            seen.add(duplicate_key)

    print("\n==============================")
    print("RAPPORT QUALITÉ")
    print("==============================")

    print(f"Textes vides : {empty_text}")
    print(f"Notes invalides : {invalid_rating}")
    print(f"ASIN manquants : {missing_asin}")
    print(f"Dates invalides : {invalid_date}")
    print(f"HTML restant : {html_remaining}")
    print(f"helpful_vote invalides : {invalid_helpful_vote}")
    print(
        "verified_purchase invalides : "
        f"{invalid_verified_purchase}"
    )
    print(f"Doublons : {duplicate_count}")

    total_errors = (
        empty_text
        + invalid_rating
        + missing_asin
        + invalid_date
        + html_remaining
        + invalid_helpful_vote
        + invalid_verified_purchase
        + duplicate_count
    )

    print("\n==============================")

    if total_errors == 0:
        print("DATASET VALIDÉ")
        print("Tous les contrôles qualité sont OK.")
    else:
        print("DATASET À CORRIGER")
        print(f"Anomalies détectées : {total_errors}")

    print("==============================")


if __name__ == "__main__":
    main()