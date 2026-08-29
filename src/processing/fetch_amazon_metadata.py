import json
from pathlib import Path

from datasets import load_dataset


ASINS_FILE = Path(
    "data/processed/amazon_asins.json"
)

OUTPUT_FILE = Path(
    "data/processed/amazon_product_metadata.json"
)


BASE_URL = (
    "https://huggingface.co/datasets/"
    "McAuley-Lab/Amazon-Reviews-2023/"
    "resolve/main/"
    "raw_meta_Electronics/"
)

DATA_FILES = [
    BASE_URL + f"full-{i:05d}-of-00010.parquet"
    for i in range(10)
]


def load_target_asins():
    """
    Charge les parent_asin présents
    dans nos 19 995 avis nettoyés.
    """

    with ASINS_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return set(
            json.load(file)
        )


def clean_price(value):
    """
    Convertit le prix en float si possible.
    """

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def simplify_product(product):
    """
    Ne conserve que les champs utiles
    pour AvisCompare.
    """

    return {
        "parent_asin": product.get(
            "parent_asin"
        ),

        "title": product.get(
            "title"
        ),

        "main_category": product.get(
            "main_category"
        ),

        "store": product.get(
            "store"
        ),

        "average_rating": product.get(
            "average_rating"
        ),

        "rating_number": product.get(
            "rating_number"
        ),

        "price": clean_price(
            product.get("price")
        ),

        "categories": product.get(
            "categories"
        ),

        "features": product.get(
            "features"
        ),

        "description": product.get(
            "description"
        ),

        "details": product.get(
            "details"
        ),

        "source": "amazon_reviews_2023"
    }


def main():

    print("==============================")
    print("MÉTADONNÉES AMAZON")
    print("==============================")

    target_asins = load_target_asins()

    print(
        f"ASIN recherchés : "
        f"{len(target_asins)}"
    )

    dataset = load_dataset(
        "parquet",
        data_files=DATA_FILES,
        split="train",
        streaming=True
    )

    found_products = {}

    scanned = 0

    for product in dataset:

        scanned += 1

        parent_asin = product.get(
            "parent_asin"
        )

        if parent_asin in target_asins:

            found_products[
                parent_asin
            ] = simplify_product(
                product
            )

        # Affichage progression
        if scanned % 50_000 == 0:

            print(
                f"{scanned} métadonnées parcourues "
                f"- {len(found_products)} produits trouvés"
            )

        # Si tous les produits sont trouvés,
        # inutile de continuer
        if (
            len(found_products)
            == len(target_asins)
        ):
            break

    products = list(
        found_products.values()
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("==============================")
    print("RÉSULTAT")
    print("==============================")

    print(
        f"Métadonnées parcourues : "
        f"{scanned}"
    )

    print(
        f"ASIN recherchés : "
        f"{len(target_asins)}"
    )

    print(
        f"Produits trouvés : "
        f"{len(products)}"
    )

    print(
        f"Produits non trouvés : "
        f"{len(target_asins) - len(products)}"
    )

    print(
        f"Fichier créé : "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()