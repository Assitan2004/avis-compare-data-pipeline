import json
from pathlib import Path

from datasets import load_dataset


MAX_REVIEWS = 20_000

OUTPUT_FILE = Path(
    "data/raw/datasets/amazon_reviews_electronics.json"
)

DATA_FILE = (
    "https://huggingface.co/datasets/"
    "McAuley-Lab/Amazon-Reviews-2023/"
    "resolve/ac9d3ad3342d6f00bf6ad8caa2668a3f830e2dee/"
    "raw_review_Electronics/"
    "full-00000-of-00034.parquet"
)


def load_amazon_reviews():

    print("==============================")
    print("AMAZON REVIEWS 2023")
    print("==============================")

    print("Connexion au fichier Parquet...")

    dataset = load_dataset(
        "parquet",
        data_files=DATA_FILE,
        split="train",
        streaming=True
    )

    print("Connexion réussie.")
    print("Récupération des avis...")

    reviews = []

    for index, review in enumerate(dataset):

        reviews.append(review)

        if (index + 1) % 1000 == 0:
            print(
                f"{index + 1} avis récupérés..."
            )

        if index + 1 >= MAX_REVIEWS:
            break

    return reviews


def save_reviews(reviews):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Enregistrement du fichier...")

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            reviews,
            file,
            ensure_ascii=False,
            indent=2
        )


def main():

    try:

        reviews = load_amazon_reviews()

        save_reviews(reviews)

        print()
        print("==============================")
        print("IMPORT TERMINÉ")
        print("==============================")

        print(
            f"Nombre d'avis : {len(reviews)}"
        )

        print(
            f"Fichier créé : {OUTPUT_FILE}"
        )

    except Exception as error:

        print()
        print("==============================")
        print("ERREUR")
        print("==============================")

        print(type(error).__name__)
        print(error)


if __name__ == "__main__":
    main()