import json
from pathlib import Path


REVIEWS_FILE = Path(
    "data/processed/amazon_reviews_clean.json"
)

PRODUCTS_FILE = Path(
    "data/processed/amazon_product_metadata.json"
)

OUTPUT_FILE = Path(
    "data/processed/amazon_reviews_enriched.json"
)


def load_json(path):
    """
    Charge un fichier JSON.
    """

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def main():

    print("==============================")
    print("JOINTURE AMAZON")
    print("==============================")

    # ----------------------------
    # 1. Chargement
    # ----------------------------

    print("Chargement des avis...")

    reviews = load_json(
        REVIEWS_FILE
    )

    print(
        f"Avis chargés : {len(reviews)}"
    )

    print("Chargement des produits...")

    products = load_json(
        PRODUCTS_FILE
    )

    print(
        f"Produits chargés : {len(products)}"
    )

    # ----------------------------
    # 2. Indexation des produits
    # ----------------------------

    print(
        "\nCréation de l'index produits..."
    )

    products_by_asin = {
        product["parent_asin"]: product
        for product in products
        if product.get("parent_asin")
    }

    print(
        f"Produits indexés : "
        f"{len(products_by_asin)}"
    )

    # ----------------------------
    # 3. Jointure
    # ----------------------------

    print("\nJointure des données...")

    enriched_reviews = []

    matched = 0
    unmatched = 0

    for review in reviews:

        parent_asin = review.get(
            "parent_asin"
        )

        product = products_by_asin.get(
            parent_asin
        )

        if product is None:

            unmatched += 1
            continue

        matched += 1

        enriched_review = {

            # Produit
            "parent_asin": parent_asin,

            "product_title": product.get(
                "title"
            ),

            "brand": product.get(
                "store"
            ),

            "main_category": product.get(
                "main_category"
            ),

            "categories": product.get(
                "categories"
            ),

            "price": product.get(
                "price"
            ),

            "product_average_rating":
                product.get(
                    "average_rating"
                ),

            "product_rating_number":
                product.get(
                    "rating_number"
                ),

            # Avis
            "rating": review.get(
                "rating"
            ),

            "review_title": review.get(
                "title"
            ),

            "review_text": review.get(
                "text"
            ),

            "review_date": review.get(
                "review_date"
            ),

            "helpful_vote": review.get(
                "helpful_vote"
            ),

            "verified_purchase":
                review.get(
                    "verified_purchase"
                ),

            # Provenance
            "source":
                "amazon_reviews_2023"
        }

        enriched_reviews.append(
            enriched_review
        )

    # ----------------------------
    # 4. Sauvegarde
    # ----------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            enriched_reviews,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ----------------------------
    # 5. Rapport
    # ----------------------------

    print()
    print("==============================")
    print("RÉSULTAT DE LA JOINTURE")
    print("==============================")

    print(
        f"Avis analysés : {len(reviews)}"
    )

    print(
        f"Avis associés à un produit : "
        f"{matched}"
    )

    print(
        f"Avis sans produit : "
        f"{unmatched}"
    )

    if reviews:

        rate = (
            matched / len(reviews)
        ) * 100

        print(
            f"Taux de correspondance : "
            f"{rate:.2f}%"
        )

    print(
        f"Fichier créé : "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()