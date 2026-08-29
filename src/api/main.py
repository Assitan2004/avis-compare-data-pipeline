import os

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ai.sentiment_service import (
    analyze_sentiment,
    analyze_reviews,
    get_monitoring_stats,
)


# =========================================================
# VARIABLES D'ENVIRONNEMENT
# =========================================================

load_dotenv()


# =========================================================
# APPLICATION FASTAPI
# =========================================================

app = FastAPI(
    title="AvisCompare API",
    description="API REST du projet AvisCompare",
    version="1.0.0",
)


# =========================================================
# CORS - AUTORISER LE FRONTEND VUE
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MODELES
# =========================================================

class SentimentRequest(BaseModel):
    text: str


# =========================================================
# CONNEXION POSTGRESQL
# =========================================================

def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# =========================================================
# ACCUEIL
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Bienvenue sur l'API AvisCompare"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    try:

        with get_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    "SELECT 1;"
                )

                cursor.fetchone()


        return {
            "status": "ok",
            "database": "connected",
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================================================
# LISTE DES PRODUITS
# =========================================================

@app.get("/products")
def get_products(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating,
                    p.rating_number,
                    p.source,
                    COUNT(r.review_id) AS review_count

                FROM products p

                LEFT JOIN reviews r
                    ON r.product_id = p.product_id

                GROUP BY
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating,
                    p.rating_number,
                    p.source

                ORDER BY
                    COUNT(r.review_id) DESC,
                    p.product_id

                LIMIT %s
                OFFSET %s;
                """,
                (
                    limit,
                    offset,
                ),
            )

            rows = cursor.fetchall()


    products = []


    for row in rows:

        products.append(
            {
                "product_id": row[0],

                "parent_asin": row[1],

                "name": row[2],

                "brand": row[3],

                "category": row[4],

                "price": (
                    float(row[5])
                    if row[5] is not None
                    else None
                ),

                "average_rating": (
                    float(row[6])
                    if row[6] is not None
                    else None
                ),

                "rating_number": row[7],

                "source": row[8],

                "review_count": row[9],
            }
        )


    return {
        "count": len(products),
        "limit": limit,
        "offset": offset,
        "products": products,
    }


# =========================================================
# RECHERCHE PRODUITS
# PRODUITS AVEC AU MOINS 10 AVIS
# =========================================================

@app.get("/products/search")
def search_products(
    q: str = Query(
        min_length=2,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating,
                    COUNT(r.review_id) AS review_count

                FROM products p

                INNER JOIN reviews r
                    ON r.product_id = p.product_id

                WHERE
                    (
                        p.name ILIKE %s
                        OR p.brand ILIKE %s
                    )

                GROUP BY
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating

                HAVING COUNT(r.review_id) >= 10

                ORDER BY
                    COUNT(r.review_id) DESC,
                    p.average_rating DESC NULLS LAST

                LIMIT %s;
                """,
                (
                    f"%{q}%",
                    f"%{q}%",
                    limit,
                ),
            )

            rows = cursor.fetchall()


    return [
        {
            "product_id": row[0],

            "parent_asin": row[1],

            "name": row[2],

            "brand": row[3],

            "category": row[4],

            "price": (
                float(row[5])
                if row[5] is not None
                else None
            ),

            "average_rating": (
                float(row[6])
                if row[6] is not None
                else None
            ),

            "review_count": row[7],
        }

        for row in rows
    ]


# =========================================================
# AVIS GLOBAUX
# =========================================================

@app.get("/reviews")
def get_reviews(
    limit: int = Query(
        default=20,
        ge=1,
        le=50,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Retourne les avis les plus récents avec :

    - informations produit
    - sentiment détecté
    - confiance du modèle
    - fiabilité de la prédiction
    - cohérence entre note et sentiment
    - avertissement éventuel

    Cette route est utilisée par
    la page globale "Avis clients".
    """

    try:

        # =====================================================
        # RECUPERATION DES DONNEES
        # =====================================================

        with get_connection() as connection:

            with connection.cursor() as cursor:

                # -------------------------------------------------
                # Nombre total d'avis textuels
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM reviews

                    WHERE
                        review_text IS NOT NULL
                        AND TRIM(review_text) <> '';
                    """
                )

                total_count = (
                    cursor.fetchone()[0]
                )


                # -------------------------------------------------
                # Avis de la page actuelle
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        r.review_id,
                        r.product_id,
                        p.name,
                        p.brand,
                        r.rating,
                        r.title,
                        r.review_text,
                        r.review_date,
                        r.helpful_vote,
                        r.verified_purchase,
                        r.source

                    FROM reviews r

                    INNER JOIN products p
                        ON p.product_id = r.product_id

                    WHERE
                        r.review_text IS NOT NULL
                        AND TRIM(r.review_text) <> ''

                    ORDER BY
                        r.review_date DESC NULLS LAST,
                        r.review_id DESC

                    LIMIT %s
                    OFFSET %s;
                    """,
                    (
                        limit,
                        offset,
                    ),
                )

                rows = cursor.fetchall()


        # =====================================================
        # PREPARATION DES AVIS POUR L'IA
        # =====================================================

        reviews_for_ai = []

        metadata = {}


        for row in rows:

            review_id = row[0]


            rating = (
                float(row[4])
                if row[4] is not None
                else None
            )


            text = str(
                row[6]
            ).strip()


            reviews_for_ai.append(
                {
                    "review_id":
                        review_id,

                    "rating":
                        rating,

                    "text":
                        text,
                }
            )


            metadata[review_id] = {

                "product_id":
                    row[1],

                "product_name":
                    row[2],

                "product_brand":
                    row[3],

                "title":
                    row[5],

                "review_date": (
                    row[7].isoformat()
                    if row[7] is not None
                    else None
                ),

                "helpful_vote":
                    row[8],

                "verified_purchase":
                    row[9],

                "source":
                    row[10],
            }


        # =====================================================
        # ANALYSE IA
        # =====================================================

        if reviews_for_ai:

            analysis = analyze_reviews(
                reviews_for_ai
            )

            analyzed_reviews = (
                analysis["reviews"]
            )


        else:

            analyzed_reviews = []


        # =====================================================
        # CONSTRUCTION DES AVIS
        # =====================================================

        reviews = []


        for review in analyzed_reviews:

            review_id = review[
                "review_id"
            ]


            meta = metadata.get(
                review_id,
                {},
            )


            reviews.append(
                {
                    # -----------------------------------------
                    # IDENTIFIANTS
                    # -----------------------------------------

                    "review_id":
                        review_id,

                    "product_id":
                        meta.get(
                            "product_id"
                        ),

                    # -----------------------------------------
                    # PRODUIT
                    # -----------------------------------------

                    "product_name":
                        meta.get(
                            "product_name"
                        ),

                    "product_brand":
                        meta.get(
                            "product_brand"
                        ),

                    # -----------------------------------------
                    # AVIS
                    # -----------------------------------------

                    "rating":
                        review.get(
                            "rating"
                        ),

                    "title":
                        meta.get(
                            "title"
                        ),

                    "text":
                        review.get(
                            "text"
                        ),

                    "review_date":
                        meta.get(
                            "review_date"
                        ),

                    "helpful_vote":
                        meta.get(
                            "helpful_vote"
                        ),

                    "verified_purchase":
                        meta.get(
                            "verified_purchase"
                        ),

                    "source":
                        meta.get(
                            "source"
                        ),

                    # -----------------------------------------
                    # RESULTAT IA
                    # -----------------------------------------

                    "sentiment":
                        review.get(
                            "sentiment"
                        ),

                    "confidence":
                        review.get(
                            "confidence"
                        ),

                    "processing_time_seconds":
                        review.get(
                            "processing_time_seconds"
                        ),

                    # -----------------------------------------
                    # FIABILITE IA
                    # -----------------------------------------

                    "low_confidence":
                        review.get(
                            "low_confidence",
                            False,
                        ),

                    "prediction_reliable":
                        review.get(
                            "prediction_reliable",
                            True,
                        ),

                    # -----------------------------------------
                    # COHERENCE NOTE / SENTIMENT
                    # -----------------------------------------

                    "expected_from_rating":
                        review.get(
                            "expected_from_rating"
                        ),

                    "is_consistent":
                        review.get(
                            "is_consistent"
                        ),

                    "rating_sentiment_conflict":
                        review.get(
                            "rating_sentiment_conflict",
                            False,
                        ),

                    # -----------------------------------------
                    # AVERTISSEMENT
                    # -----------------------------------------

                    "warning":
                        review.get(
                            "warning"
                        ),
                }
            )


        # =====================================================
        # PAGINATION
        # =====================================================

        next_offset = (
            offset
            + len(reviews)
        )


        has_more = (
            next_offset
            < total_count
        )


        # =====================================================
        # REPONSE
        # =====================================================

        return {
            "count":
                len(reviews),

            "total_count":
                total_count,

            "limit":
                limit,

            "offset":
                offset,

            "next_offset": (
                next_offset
                if has_more
                else None
            ),

            "has_more":
                has_more,

            "reviews":
                reviews,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors du chargement "
                f"des avis : {error}"
            ),
        )


# =========================================================
# DETAIL D'UN PRODUIT
# IMPORTANT :
# cette route reste APRES /products/search
# =========================================================

@app.get("/products/{product_id}")
def get_product(
    product_id: int,
):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating,
                    p.rating_number,
                    p.source,
                    COUNT(r.review_id) AS review_count

                FROM products p

                LEFT JOIN reviews r
                    ON r.product_id = p.product_id

                WHERE
                    p.product_id = %s

                GROUP BY
                    p.product_id,
                    p.parent_asin,
                    p.name,
                    p.brand,
                    p.category,
                    p.price,
                    p.average_rating,
                    p.rating_number,
                    p.source;
                """,
                (
                    product_id,
                ),
            )

            row = cursor.fetchone()


    if row is None:

        raise HTTPException(
            status_code=404,
            detail="Produit introuvable",
        )


    return {
        "product_id": row[0],

        "parent_asin": row[1],

        "name": row[2],

        "brand": row[3],

        "category": row[4],

        "price": (
            float(row[5])
            if row[5] is not None
            else None
        ),

        "average_rating": (
            float(row[6])
            if row[6] is not None
            else None
        ),

        "rating_number": row[7],

        "source": row[8],

        "review_count": row[9],
    }


# =========================================================
# AVIS D'UN PRODUIT
# =========================================================

@app.get("/products/{product_id}/reviews")
def get_product_reviews(
    product_id: int,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    review_id,
                    rating,
                    title,
                    review_text,
                    review_date,
                    helpful_vote,
                    verified_purchase,
                    source

                FROM reviews

                WHERE
                    product_id = %s

                ORDER BY
                    review_date DESC NULLS LAST

                LIMIT %s;
                """,
                (
                    product_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()


    return [
        {
            "review_id":
                row[0],

            "rating": (
                float(row[1])
                if row[1] is not None
                else None
            ),

            "title":
                row[2],

            "text":
                row[3],

            "review_date": (
                row[4].isoformat()
                if row[4] is not None
                else None
            ),

            "helpful_vote":
                row[5],

            "verified_purchase":
                row[6],

            "source":
                row[7],
        }

        for row in rows
    ]


# =========================================================
# STATISTIQUES
# =========================================================

@app.get("/stats")
def get_stats():

    try:

        with get_connection() as connection:

            with connection.cursor() as cursor:

                # -------------------------------------------------
                # Nombre de produits
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM products;
                    """
                )

                products_count = (
                    cursor.fetchone()[0]
                )


                # -------------------------------------------------
                # Nombre d'avis
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM reviews;
                    """
                )

                reviews_count = (
                    cursor.fetchone()[0]
                )


                # -------------------------------------------------
                # Note moyenne
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        ROUND(
                            AVG(rating),
                            2
                        )

                    FROM reviews;
                    """
                )

                average_rating = (
                    cursor.fetchone()[0]
                )


                # -------------------------------------------------
                # Avis vérifiés
                # -------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM reviews

                    WHERE
                        verified_purchase = TRUE;
                    """
                )

                verified_count = (
                    cursor.fetchone()[0]
                )


        return {
            "products":
                products_count,

            "reviews":
                reviews_count,

            "average_rating": (
                float(average_rating)
                if average_rating is not None
                else None
            ),

            "verified_reviews":
                verified_count,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors du chargement "
                f"des statistiques : {error}"
            ),
        )


# =========================================================
# IA - ANALYSE D'UN SENTIMENT
# =========================================================

@app.post("/ai/sentiment")
def sentiment_analysis(
    request: SentimentRequest,
):

    if not request.text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Le texte ne peut pas être vide"
            ),
        )


    try:

        result = analyze_sentiment(
            request.text
        )


        return {
            "text":
                request.text,

            "sentiment":
                result["sentiment"],

            "confidence":
                result["confidence"],

            "low_confidence":
                result[
                    "low_confidence"
                ],

            "prediction_reliable":
                result[
                    "prediction_reliable"
                ],

            "processing_time_seconds":
                result[
                    "processing_time_seconds"
                ],
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors de l'analyse IA : "
                f"{error}"
            ),
        )


# =========================================================
# IA - RESUME SENTIMENT D'UN PRODUIT
# =========================================================

@app.get(
    "/products/{product_id}/sentiment-summary"
)
def get_product_sentiment_summary(
    product_id: int,
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
    ),
):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            # -------------------------------------------------
            # Vérifier que le produit existe
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    product_id,
                    name

                FROM products

                WHERE
                    product_id = %s;
                """,
                (
                    product_id,
                ),
            )

            product = cursor.fetchone()


            if product is None:

                raise HTTPException(
                    status_code=404,
                    detail="Produit introuvable",
                )


            # -------------------------------------------------
            # Récupération des derniers avis
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    review_id,
                    rating,
                    review_text

                FROM reviews

                WHERE
                    product_id = %s
                    AND review_text IS NOT NULL
                    AND TRIM(review_text) <> ''

                ORDER BY
                    review_date DESC NULLS LAST,
                    review_id DESC

                LIMIT %s;
                """,
                (
                    product_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()


    # =====================================================
    # AUCUN AVIS
    # =====================================================

    if not rows:

        return {
            "product_id":
                product_id,

            "product_name":
                product[1],

            "message":
                "Aucun avis disponible",

            "total_reviews_analyzed":
                0,

            "counts": {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            },

            "percentages": {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            },

            "dominant_sentiment":
                None,

            "inconsistent_reviews":
                0,

            "inconsistency_rate":
                0,

            "low_confidence_reviews":
                0,

            "low_confidence_rate":
                0,

            "reliable_predictions":
                0,

            "reliable_prediction_rate":
                0,

            "sample_reliability":
                "none",

            "can_draw_global_conclusion":
                False,

            "analysis_quality":
                "none",

            "reviews":
                [],
        }


    # =====================================================
    # PREPARATION DES AVIS
    # =====================================================

    reviews = []


    for row in rows:

        if (
            row[2] is None
            or not str(row[2]).strip()
        ):
            continue


        reviews.append(
            {
                "review_id":
                    row[0],

                "rating": (
                    float(row[1])
                    if row[1] is not None
                    else None
                ),

                "text":
                    str(row[2]).strip(),
            }
        )


    # =====================================================
    # AUCUN TEXTE UTILISABLE
    # =====================================================

    if not reviews:

        return {
            "product_id":
                product_id,

            "product_name":
                product[1],

            "message":
                "Aucun avis textuel disponible",

            "total_reviews_analyzed":
                0,

            "counts": {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            },

            "percentages": {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            },

            "dominant_sentiment":
                None,

            "inconsistent_reviews":
                0,

            "inconsistency_rate":
                0,

            "low_confidence_reviews":
                0,

            "low_confidence_rate":
                0,

            "reliable_predictions":
                0,

            "reliable_prediction_rate":
                0,

            "sample_reliability":
                "none",

            "can_draw_global_conclusion":
                False,

            "analysis_quality":
                "none",

            "reviews":
                [],
        }


    # =====================================================
    # ANALYSE IA
    # =====================================================

    try:

        analysis = analyze_reviews(
            reviews
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors de l'analyse "
                f"des avis : {error}"
            ),
        )


    # =====================================================
    # RESULTAT
    # =====================================================

    return {
        "product_id":
            product_id,

        "product_name":
            product[1],

        **analysis,
    }


# =========================================================
# IA - MONITORING
# =========================================================

@app.get("/ai/monitoring")
def ai_monitoring():

    return get_monitoring_stats()