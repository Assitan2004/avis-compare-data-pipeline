import logging
import time

from transformers import pipeline


log = logging.getLogger("avis_compare.ai_monitoring")


# ============================================================
# CONFIGURATION DU MODELE
# ============================================================

MODEL_NAME = (
    "cardiffnlp/"
    "twitter-xlm-roberta-base-sentiment"
)


classifier = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
)


# ============================================================
# SEUILS
# ============================================================

# En dessous de 60 %, on considère que le modèle
# n'est pas suffisamment sûr de sa prédiction.
LOW_CONFIDENCE_THRESHOLD = 0.60

# Seuils d'alerte (C11) : au-delà, on journalise un avertissement
# pour signaler que le modèle se comporte anormalement.
ALERT_ERROR_RATE_THRESHOLD = 0.05          # plus de 5 % d'erreurs
ALERT_LOW_CONFIDENCE_RATE_THRESHOLD = 0.30  # plus de 30 % de prédictions incertaines
ALERT_MIN_PREDICTIONS = 20                  # ne pas alerter sur un échantillon trop petit


# ============================================================
# MONITORING
# ============================================================

monitoring = {
    "predictions": 0,
    "errors": 0,
    "total_time_seconds": 0.0,
    "last_prediction_time_seconds": 0.0,
    "low_confidence_predictions": 0,
    "rating_sentiment_conflicts": 0,
}


def check_monitoring_alerts():
    """
    Vérifie les métriques de monitoring et journalise une alerte
    (log niveau WARNING) si un seuil anormal est dépassé.

    Volontairement simple : pas de dashboard ni de notification
    externe, mais une vraie détection automatique d'anomalie,
    visible dans les logs de l'application.
    """

    predictions = monitoring["predictions"]

    if predictions < ALERT_MIN_PREDICTIONS:
        return

    error_rate = monitoring["errors"] / predictions
    low_confidence_rate = (
        monitoring["low_confidence_predictions"] / predictions
    )

    if error_rate > ALERT_ERROR_RATE_THRESHOLD:
        log.warning(
            "ALERTE monitoring IA : taux d'erreur de %.1f%% "
            "(seuil : %.0f%%) sur %d prédictions",
            error_rate * 100,
            ALERT_ERROR_RATE_THRESHOLD * 100,
            predictions,
        )

    if low_confidence_rate > ALERT_LOW_CONFIDENCE_RATE_THRESHOLD:
        log.warning(
            "ALERTE monitoring IA : taux de confiance faible de %.1f%% "
            "(seuil : %.0f%%) sur %d prédictions",
            low_confidence_rate * 100,
            ALERT_LOW_CONFIDENCE_RATE_THRESHOLD * 100,
            predictions,
        )



# ============================================================
# CONVERSION NOTE AMAZON -> SENTIMENT ATTENDU
# ============================================================

def rating_to_sentiment(rating):
    """
    Convertit une note Amazon en sentiment attendu.

    1-2 étoiles -> negative
    3 étoiles   -> neutral
    4-5 étoiles -> positive

    Cette fonction NE REMPLACE PAS
    le résultat du modèle IA.

    Elle permet uniquement de détecter
    une éventuelle incohérence entre
    la note et le texte.
    """

    try:
        rating = float(rating)

    except (TypeError, ValueError):
        return None


    if rating <= 2:
        return "negative"


    if rating < 4:
        return "neutral"


    return "positive"


# ============================================================
# GENERATION DU WARNING
# ============================================================

def build_warning(
    low_confidence,
    rating_sentiment_conflict,
):
    """
    Retourne un warning destiné au frontend.
    """

    if (
        low_confidence
        and rating_sentiment_conflict
    ):
        return {
            "code":
                "low_confidence_and_conflict",

            "label":
                "Résultat incertain et incohérent avec la note",
        }


    if low_confidence:
        return {
            "code":
                "low_confidence",

            "label":
                "Résultat incertain",
        }


    if rating_sentiment_conflict:
        return {
            "code":
                "rating_sentiment_conflict",

            "label":
                "Note et texte potentiellement incohérents",
        }


    return None


# ============================================================
# ANALYSE D'UN SEUL AVIS
# ============================================================

def analyze_sentiment(text: str):
    """
    Analyse le sentiment d'un seul texte.

    Retourne :
    - sentiment
    - confidence
    - low_confidence
    - prediction_reliable
    - processing_time_seconds
    """

    start_time = time.perf_counter()


    try:

        # ----------------------------------------------------
        # Nettoyage
        # ----------------------------------------------------

        if text is None:
            text = ""


        text = str(text).strip()


        if not text:
            raise ValueError(
                "Impossible d'analyser un avis vide."
            )


        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        result = classifier(
            text,
            truncation=True,
            max_length=512,
        )[0]


        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        sentiment = str(
            result["label"]
        ).lower().strip()


        valid_sentiments = {
            "positive",
            "neutral",
            "negative",
        }


        if sentiment not in valid_sentiments:
            raise ValueError(
                "Label de sentiment inconnu : "
                f"{sentiment}"
            )


        # ----------------------------------------------------
        # CONFIANCE
        # ----------------------------------------------------

        confidence = float(
            result["score"]
        )


        low_confidence = (
            confidence
            < LOW_CONFIDENCE_THRESHOLD
        )


        prediction_reliable = (
            not low_confidence
        )


        # ----------------------------------------------------
        # TEMPS
        # ----------------------------------------------------

        elapsed_time = (
            time.perf_counter()
            - start_time
        )


        # ----------------------------------------------------
        # MONITORING
        # ----------------------------------------------------

        monitoring["predictions"] += 1

        monitoring[
            "total_time_seconds"
        ] += elapsed_time

        monitoring[
            "last_prediction_time_seconds"
        ] = elapsed_time


        if low_confidence:
            monitoring[
                "low_confidence_predictions"
            ] += 1

        check_monitoring_alerts()


        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print("\n")
        print("=" * 70)
        print("DEBUG SENTIMENT")
        print("=" * 70)

        print("TEXTE ANALYSE :")
        print(text[:500])

        print(
            "\nRESULTAT BRUT DU MODELE :"
        )
        print(result)

        print(
            "\nLABEL :",
            sentiment
        )

        print(
            "SCORE :",
            confidence
        )

        print(
            "CONFIANCE FAIBLE :",
            low_confidence
        )

        print("=" * 70)
        print("\n")


        # ----------------------------------------------------
        # RESULTAT
        # ----------------------------------------------------

        return {
            "sentiment":
                sentiment,

            "confidence":
                round(
                    confidence,
                    4,
                ),

            "low_confidence":
                low_confidence,

            "prediction_reliable":
                prediction_reliable,

            "processing_time_seconds":
                round(
                    elapsed_time,
                    4,
                ),
        }


    except Exception as error:

        monitoring["errors"] += 1
        check_monitoring_alerts()


        print("\n")
        print("=" * 70)
        print(
            "ERREUR ANALYSE SENTIMENT"
        )
        print("=" * 70)

        print(error)

        print("=" * 70)
        print("\n")


        raise


# ============================================================
# ANALYSE DE PLUSIEURS AVIS
# ============================================================

def analyze_reviews(reviews):
    """
    Analyse plusieurs avis.

    Le sentiment reste toujours celui
    prédit par le modèle.

    La note sert uniquement à :
    - contrôler la cohérence ;
    - générer un avertissement éventuel.
    """

    counts = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
    }


    analyzed_reviews = []


    inconsistent_reviews = 0
    low_confidence_reviews = 0
    reliable_predictions = 0


    # ========================================================
    # ANALYSE DE CHAQUE AVIS
    # ========================================================

    for review in reviews:

        text = review.get(
            "text",
            "",
        )


        rating = review.get(
            "rating"
        )


        # ----------------------------------------------------
        # IA
        # ----------------------------------------------------

        result = analyze_sentiment(
            text
        )


        sentiment = result[
            "sentiment"
        ]


        confidence = result[
            "confidence"
        ]


        low_confidence = result[
            "low_confidence"
        ]


        # ----------------------------------------------------
        # SENTIMENT ATTENDU SELON LA NOTE
        # ----------------------------------------------------

        expected_from_rating = (
            rating_to_sentiment(
                rating
            )
        )


        # ----------------------------------------------------
        # COHERENCE NOTE / TEXTE
        # ----------------------------------------------------

        if expected_from_rating is None:

            is_consistent = None

            rating_sentiment_conflict = False


        else:

            is_consistent = (
                sentiment
                == expected_from_rating
            )


            rating_sentiment_conflict = (
                not is_consistent
            )


        # ----------------------------------------------------
        # COMPTEURS
        # ----------------------------------------------------

        if rating_sentiment_conflict:

            inconsistent_reviews += 1

            monitoring[
                "rating_sentiment_conflicts"
            ] += 1


        if low_confidence:

            low_confidence_reviews += 1


        else:

            reliable_predictions += 1


        # ----------------------------------------------------
        # SENTIMENT IA
        # ----------------------------------------------------

        counts[
            sentiment
        ] += 1


        # ----------------------------------------------------
        # WARNING FRONTEND
        # ----------------------------------------------------

        warning = build_warning(
            low_confidence=
                low_confidence,

            rating_sentiment_conflict=
                rating_sentiment_conflict,
        )


        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print("-" * 70)

        print(
            "REVIEW ID :",
            review.get(
                "review_id"
            ),
        )

        print(
            "NOTE :",
            rating,
        )

        print(
            "SENTIMENT IA :",
            sentiment,
        )

        print(
            "CONFIANCE :",
            confidence,
        )

        print(
            "CONFIANCE FAIBLE :",
            low_confidence,
        )

        print(
            "SENTIMENT ATTENDU SELON NOTE :",
            expected_from_rating,
        )

        print(
            "COHERENT :",
            is_consistent,
        )

        print(
            "WARNING :",
            warning,
        )


        if rating_sentiment_conflict:
            print(
                "ATTENTION : contradiction "
                "entre la note et le texte."
            )


        if low_confidence:
            print(
                "ATTENTION : prediction "
                "avec faible confiance."
            )


        print("-" * 70)


        # ----------------------------------------------------
        # RESULTAT PAR AVIS
        # ----------------------------------------------------

        analyzed_reviews.append(
            {
                "review_id":
                    review.get(
                        "review_id"
                    ),

                "rating":
                    rating,

                "text":
                    text,

                # Résultat IA
                "sentiment":
                    sentiment,

                "confidence":
                    confidence,

                "processing_time_seconds":
                    result[
                        "processing_time_seconds"
                    ],

                # Fiabilité IA
                "low_confidence":
                    low_confidence,

                "prediction_reliable":
                    not low_confidence,

                # Contrôle via étoiles
                "expected_from_rating":
                    expected_from_rating,

                "is_consistent":
                    is_consistent,

                "rating_sentiment_conflict":
                    rating_sentiment_conflict,

                # Message utilisable directement
                # par le frontend
                "warning":
                    warning,
            }
        )


    # ========================================================
    # TOTAL
    # ========================================================

    total = len(
        analyzed_reviews
    )


    # ========================================================
    # POURCENTAGES DE SENTIMENT
    # ========================================================

    percentages = {}


    for sentiment, count in counts.items():

        if total > 0:

            percentages[
                sentiment
            ] = round(
                count / total * 100,
                2,
            )

        else:

            percentages[
                sentiment
            ] = 0


    # ========================================================
    # TAUX D'INCOHERENCE
    # ========================================================

    if total > 0:

        inconsistency_rate = round(
            inconsistent_reviews
            / total
            * 100,
            2,
        )


        low_confidence_rate = round(
            low_confidence_reviews
            / total
            * 100,
            2,
        )


        reliable_prediction_rate = round(
            reliable_predictions
            / total
            * 100,
            2,
        )


    else:

        inconsistency_rate = 0

        low_confidence_rate = 0

        reliable_prediction_rate = 0


    # ========================================================
    # FIABILITE DE L'ECHANTILLON
    # ========================================================

    if total == 0:

        sample_reliability = "none"


    elif total < 5:

        sample_reliability = (
            "very_low"
        )


    elif total < 10:

        sample_reliability = "low"


    elif total < 20:

        sample_reliability = "medium"


    else:

        sample_reliability = "good"


    # ========================================================
    # CONCLUSION GLOBALE
    # ========================================================

    can_draw_global_conclusion = (
        total >= 5
    )


    # ========================================================
    # SENTIMENT DOMINANT
    # ========================================================

    if total > 0:

        dominant_sentiment = max(
            counts,
            key=counts.get,
        )


    else:

        dominant_sentiment = None


    # ========================================================
    # QUALITE GLOBALE DE L'ANALYSE
    # ========================================================

    if total == 0:

        analysis_quality = "none"


    elif total < 5:

        analysis_quality = "very_low"


    elif (
        low_confidence_rate >= 50
        or inconsistency_rate >= 50
    ):

        analysis_quality = "low"


    elif (
        low_confidence_rate >= 25
        or inconsistency_rate >= 25
    ):

        analysis_quality = "medium"


    else:

        analysis_quality = "good"


    # ========================================================
    # DEBUG RESUME
    # ========================================================

    print("\n")
    print("=" * 70)
    print("RESUME ANALYSE")
    print("=" * 70)


    print(
        "Nombre d'avis analyses :",
        total,
    )


    print(
        "Comptage IA :",
        counts,
    )


    print(
        "Pourcentages :",
        percentages,
    )


    print(
        "Sentiment dominant :",
        dominant_sentiment,
    )


    print(
        "Avis incoherents note/texte :",
        inconsistent_reviews,
    )


    print(
        "Taux d'incoherence :",
        f"{inconsistency_rate}%",
    )


    print(
        "Predictions faible confiance :",
        low_confidence_reviews,
    )


    print(
        "Taux faible confiance :",
        f"{low_confidence_rate}%",
    )


    print(
        "Predictions fiables :",
        reliable_predictions,
    )


    print(
        "Taux predictions fiables :",
        f"{reliable_prediction_rate}%",
    )


    print(
        "Fiabilite echantillon :",
        sample_reliability,
    )


    print(
        "Qualite globale analyse :",
        analysis_quality,
    )


    print(
        "Conclusion globale autorisee :",
        can_draw_global_conclusion,
    )


    print("=" * 70)
    print("\n")


    # ========================================================
    # RESULTAT FINAL
    # ========================================================

    return {
        "total_reviews_analyzed":
            total,

        "counts":
            counts,

        "percentages":
            percentages,

        "dominant_sentiment":
            dominant_sentiment,

        # --------------------------------------------
        # Cohérence note / sentiment
        # --------------------------------------------

        "inconsistent_reviews":
            inconsistent_reviews,

        "inconsistency_rate":
            inconsistency_rate,

        # --------------------------------------------
        # Confiance du modèle
        # --------------------------------------------

        "low_confidence_reviews":
            low_confidence_reviews,

        "low_confidence_rate":
            low_confidence_rate,

        "reliable_predictions":
            reliable_predictions,

        "reliable_prediction_rate":
            reliable_prediction_rate,

        # --------------------------------------------
        # Fiabilité de l'échantillon
        # --------------------------------------------

        "sample_reliability":
            sample_reliability,

        "can_draw_global_conclusion":
            can_draw_global_conclusion,

        # --------------------------------------------
        # Qualité globale
        # --------------------------------------------

        "analysis_quality":
            analysis_quality,

        # --------------------------------------------
        # Avis
        # --------------------------------------------

        "reviews":
            analyzed_reviews,
    }


# ============================================================
# MONITORING
# ============================================================

def get_monitoring_stats():
    """
    Retourne les statistiques globales
    du modèle depuis le démarrage de l'API.
    """

    predictions = monitoring[
        "predictions"
    ]


    if predictions > 0:

        average_time = (
            monitoring[
                "total_time_seconds"
            ]
            / predictions
        )


        low_confidence_rate = round(
            monitoring[
                "low_confidence_predictions"
            ]
            / predictions
            * 100,
            2,
        )


        conflict_rate = round(
            monitoring[
                "rating_sentiment_conflicts"
            ]
            / predictions
            * 100,
            2,
        )


    else:

        average_time = 0
        low_confidence_rate = 0
        conflict_rate = 0


    return {
        "model":
            MODEL_NAME,

        "confidence_threshold":
            LOW_CONFIDENCE_THRESHOLD,

        "predictions":
            predictions,

        "errors":
            monitoring[
                "errors"
            ],

        "low_confidence_predictions":
            monitoring[
                "low_confidence_predictions"
            ],

        "low_confidence_rate":
            low_confidence_rate,

        "rating_sentiment_conflicts":
            monitoring[
                "rating_sentiment_conflicts"
            ],

        "rating_sentiment_conflict_rate":
            conflict_rate,

        "last_prediction_time_seconds":
            round(
                monitoring[
                    "last_prediction_time_seconds"
                ],
                4,
            ),

        "average_prediction_time_seconds":
            round(
                average_time,
                4,
            ),
    }