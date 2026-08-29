import json
from pathlib import Path


INPUT_FILE = Path(
    "data/processed/amazon_reviews_clean.json"
)

OUTPUT_FILE = Path(
    "data/processed/amazon_asins.json"
)


def main():

    print("==============================")
    print("EXTRACTION DES ASIN")
    print("==============================")

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        reviews = json.load(file)

    print(f"Avis analysés : {len(reviews)}")

    # Ensemble pour supprimer automatiquement
    # les ASIN en double
    asins = {
        review["parent_asin"]
        for review in reviews
        if review.get("parent_asin")
    }

    # Transformation en liste triée
    asins = sorted(asins)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            asins,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("==============================")
    print("RÉSULTAT")
    print("==============================")

    print(f"Avis : {len(reviews)}")
    print(f"Produits uniques : {len(asins)}")
    print(f"Fichier créé : {OUTPUT_FILE}")

    print("\nExemples d'ASIN :")

    for asin in asins[:10]:
        print("-", asin)


if __name__ == "__main__":
    main()