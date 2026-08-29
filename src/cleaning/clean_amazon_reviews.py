import json
import html
import re
from datetime import datetime, timezone
from pathlib import Path


INPUT_FILE = Path(
    "data/raw/datasets/amazon_reviews_electronics.json"
)

OUTPUT_FILE = Path(
    "data/processed/amazon_reviews_clean.json"
)


def clean_text(value):
    """
    Nettoie le texte d'un avis.
    """

    if value is None:
        return None

    # Transforme les entités HTML :
    # &#34; -> "
    value = html.unescape(value)

    # Remplace les balises <br>, <br />, etc.
    value = re.sub(
        r"<br\s*/?>",
        " ",
        value,
        flags=re.IGNORECASE
    )

    # Supprime les autres balises HTML éventuelles
    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    # Remplace plusieurs espaces par un seul
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def convert_timestamp(timestamp):
    """
    Convertit le timestamp Amazon en date ISO.
    Exemple :
    1658185117948
    ->
    2022-07-18
    """

    if timestamp is None:
        return None

    try:

        date = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc
        )

        return date.strftime("%Y-%m-%d")

    except (ValueError, TypeError, OSError):

        return None


def is_valid_rating(rating):
    """
    Vérifie que la note est comprise entre 1 et 5.
    """

    try:

        rating = float(rating)

        return 1 <= rating <= 5

    except (TypeError, ValueError):

        return False


def clean_review(review):
    """
    Transforme un avis brut en avis nettoyé.
    """

    return {

        "rating": float(review["rating"]),

        "title": clean_text(
            review.get("title")
        ),

        "text": clean_text(
            review.get("text")
        ),

        "asin": review.get("asin"),

        "parent_asin": review.get(
            "parent_asin"
        ),

        "review_date": convert_timestamp(
            review.get("timestamp")
        ),

        "helpful_vote": review.get(
            "helpful_vote",
            0
        ),

        "verified_purchase": review.get(
            "verified_purchase",
            False
        ),

        "source": "amazon_reviews_2023"
    }


def main():

    print("==============================")
    print("NETTOYAGE AMAZON REVIEWS")
    print("==============================")

    # Lecture du fichier RAW
    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        reviews = json.load(file)

    print(
        f"Avis avant nettoyage : "
        f"{len(reviews)}"
    )

    cleaned_reviews = []

    removed_empty = 0
    removed_invalid_rating = 0
    removed_duplicates = 0

    seen = set()

    for review in reviews:

        # Vérification de la note
        if not is_valid_rating(
            review.get("rating")
        ):
            removed_invalid_rating += 1
            continue

        # Nettoyage du texte
        text = clean_text(
            review.get("text")
        )

        # Supprime les avis sans texte
        if not text:
            removed_empty += 1
            continue

        # Clé de déduplication
        duplicate_key = (
            review.get("asin"),
            review.get("user_id"),
            review.get("timestamp"),
            text
        )

        if duplicate_key in seen:
            removed_duplicates += 1
            continue

        seen.add(duplicate_key)

        cleaned_review = clean_review(
            review
        )

        cleaned_reviews.append(
            cleaned_review
        )

    # Création du dossier processed
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Sauvegarde
    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cleaned_reviews,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("==============================")
    print("RÉSULTAT")
    print("==============================")

    print(
        f"Avis avant : "
        f"{len(reviews)}"
    )

    print(
        f"Avis après : "
        f"{len(cleaned_reviews)}"
    )

    print(
        f"Avis vides supprimés : "
        f"{removed_empty}"
    )

    print(
        f"Notes invalides supprimées : "
        f"{removed_invalid_rating}"
    )

    print(
        f"Doublons supprimés : "
        f"{removed_duplicates}"
    )

    print(
        f"Fichier créé : "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()