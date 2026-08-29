import json
from pathlib import Path


INPUT_FILE = Path(
    "data/processed/amazon_reviews_enriched.json"
)

PRODUCTS_FILE = Path(
    "data/processed/products.json"
)

REVIEWS_FILE = Path(
    "data/processed/reviews.json"
)


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def main():

    print("==============================")
    print("NORMALISATION AMAZON")
    print("==============================")

    data = load_json(INPUT_FILE)

    print(
        f"Lignes chargées : {len(data)}"
    )

    products = {}
    reviews = []

    review_id = 1

    for row in data:

        parent_asin = row.get(
            "parent_asin"
        )

        # =========================
        # PRODUITS
        # =========================

        if (
            parent_asin
            and parent_asin not in products
        ):

            products[parent_asin] = {

                "product_id": len(products) + 1,

                "parent_asin": parent_asin,

                "name": row.get(
                    "product_title"
                ),

                "brand": row.get(
                    "brand"
                ),

                "category": row.get(
                    "main_category"
                ),

                "categories": row.get(
                    "categories"
                ),

                "price": row.get(
                    "price"
                ),

                "average_rating": row.get(
                    "product_average_rating"
                ),

                "rating_number": row.get(
                    "product_rating_number"
                ),

                "source":
                    "amazon_reviews_2023"
            }

        # =========================
        # AVIS
        # =========================

        product = products.get(
            parent_asin
        )

        if product is None:
            continue

        reviews.append({

            "review_id": review_id,

            "product_id": product[
                "product_id"
            ],

            "parent_asin": parent_asin,

            "rating": row.get(
                "rating"
            ),

            "title": row.get(
                "review_title"
            ),

            "text": row.get(
                "review_text"
            ),

            "review_date": row.get(
                "review_date"
            ),

            "helpful_vote": row.get(
                "helpful_vote"
            ),

            "verified_purchase":
                row.get(
                    "verified_purchase"
                ),

            "source":
                "amazon_reviews_2023"
        })

        review_id += 1

    products_list = list(
        products.values()
    )

    PRODUCTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with PRODUCTS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products_list,
            file,
            ensure_ascii=False,
            indent=2
        )

    with REVIEWS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            reviews,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("==============================")
    print("RÉSULTAT")
    print("==============================")

    print(
        f"Produits : "
        f"{len(products_list)}"
    )

    print(
        f"Avis : "
        f"{len(reviews)}"
    )

    print(
        f"Fichier produits : "
        f"{PRODUCTS_FILE}"
    )

    print(
        f"Fichier avis : "
        f"{REVIEWS_FILE}"
    )


if __name__ == "__main__":
    main()