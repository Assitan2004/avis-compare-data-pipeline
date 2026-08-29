import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

PRODUCTS_FILE = Path("data/processed/products.json")
REVIEWS_FILE = Path("data/processed/reviews.json")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def import_products(cursor, products):
    print("Import des produits...")

    query = """
        INSERT INTO products (
            product_id,
            parent_asin,
            name,
            brand,
            category,
            price,
            average_rating,
            rating_number,
            source
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (product_id)
        DO UPDATE SET
            parent_asin = EXCLUDED.parent_asin,
            name = EXCLUDED.name,
            brand = EXCLUDED.brand,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            average_rating = EXCLUDED.average_rating,
            rating_number = EXCLUDED.rating_number,
            source = EXCLUDED.source
    """

    for index, product in enumerate(products, start=1):
        cursor.execute(
            query,
            (
                product.get("product_id"),
                product.get("parent_asin"),
                product.get("name"),
                product.get("brand"),
                product.get("category"),
                product.get("price"),
                product.get("average_rating"),
                product.get("rating_number"),
                product.get("source")
            )
        )

        if index % 1000 == 0:
            print(f"{index} produits importés...")


def import_reviews(cursor, reviews):
    print("\nImport des avis...")

    query = """
        INSERT INTO reviews (
            review_id,
            product_id,
            rating,
            title,
            review_text,
            review_date,
            helpful_vote,
            verified_purchase,
            source
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (review_id)
        DO UPDATE SET
            product_id = EXCLUDED.product_id,
            rating = EXCLUDED.rating,
            title = EXCLUDED.title,
            review_text = EXCLUDED.review_text,
            review_date = EXCLUDED.review_date,
            helpful_vote = EXCLUDED.helpful_vote,
            verified_purchase = EXCLUDED.verified_purchase,
            source = EXCLUDED.source
    """

    for index, review in enumerate(reviews, start=1):
        cursor.execute(
            query,
            (
                review.get("review_id"),
                review.get("product_id"),
                review.get("rating"),
                review.get("title"),
                review.get("text"),
                review.get("review_date"),
                review.get("helpful_vote"),
                review.get("verified_purchase"),
                review.get("source")
            )
        )

        if index % 1000 == 0:
            print(f"{index} avis importés...")


def main():
    print("==============================")
    print("IMPORT POSTGRESQL")
    print("==============================")

    products = load_json(PRODUCTS_FILE)
    reviews = load_json(REVIEWS_FILE)

    print(f"Produits à importer : {len(products)}")
    print(f"Avis à importer : {len(reviews)}")

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                import_products(cursor, products)
                import_reviews(cursor, reviews)

            connection.commit()

        print()
        print("==============================")
        print("IMPORT TERMINÉ")
        print("==============================")
        print(f"Produits importés : {len(products)}")
        print(f"Avis importés : {len(reviews)}")

    except Exception as error:
        print()
        print("==============================")
        print("ERREUR")
        print("==============================")
        print(type(error).__name__)
        print(error)


if __name__ == "__main__":
    main()