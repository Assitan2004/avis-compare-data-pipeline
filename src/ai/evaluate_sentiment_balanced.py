import json
import random
from collections import defaultdict

from transformers import pipeline


MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
REVIEWS_FILE = "data/processed/reviews.json"

SAMPLES_PER_CLASS = 50
RANDOM_SEED = 42

LABELS = [
    "negative",
    "neutral",
    "positive"
]


# ---------------------------------------
# 1. Conversion note -> sentiment
# ---------------------------------------

def rating_to_sentiment(rating):
    """
    Transforme la note Amazon en sentiment de référence.

    1-2 étoiles -> negative
    3 étoiles   -> neutral
    4-5 étoiles -> positive
    """

    rating = float(rating)

    if rating <= 2:
        return "negative"

    elif rating == 3:
        return "neutral"

    else:
        return "positive"


# ---------------------------------------
# 2. Calcul des métriques
# ---------------------------------------

def calculate_metrics(y_true, y_pred, labels):
    """
    Calcule precision, recall et F1-score
    pour chaque classe.
    """

    metrics = {}

    for label in labels:

        # True Positive :
        # la vraie classe et la prédiction
        # correspondent à la classe étudiée
        tp = sum(
            1
            for true, pred in zip(y_true, y_pred)
            if true == label and pred == label
        )

        # False Positive :
        # le modèle prédit cette classe
        # alors que ce n'est pas la vraie classe
        fp = sum(
            1
            for true, pred in zip(y_true, y_pred)
            if true != label and pred == label
        )

        # False Negative :
        # la vraie classe est celle étudiée
        # mais le modèle prédit autre chose
        fn = sum(
            1
            for true, pred in zip(y_true, y_pred)
            if true == label and pred != label
        )

        # Precision
        if tp + fp > 0:
            precision = tp / (tp + fp)
        else:
            precision = 0

        # Recall
        if tp + fn > 0:
            recall = tp / (tp + fn)
        else:
            recall = 0

        # F1-score
        if precision + recall > 0:
            f1 = (
                2
                * precision
                * recall
                / (precision + recall)
            )
        else:
            f1 = 0

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    return metrics


# ---------------------------------------
# 3. Matrice de confusion
# ---------------------------------------

def calculate_confusion_matrix(
    y_true,
    y_pred,
    labels
):
    """
    Construit manuellement la matrice
    de confusion.
    """

    matrix = []

    for true_label in labels:

        row = []

        for predicted_label in labels:

            count = sum(
                1
                for true, pred in zip(
                    y_true,
                    y_pred
                )
                if true == true_label
                and pred == predicted_label
            )

            row.append(count)

        matrix.append(row)

    return matrix


# =======================================
# DÉBUT DU PROGRAMME
# =======================================

print("=" * 60)
print("ÉVALUATION ÉQUILIBRÉE DU MODÈLE DE SENTIMENT")
print("=" * 60)


# ---------------------------------------
# 4. Chargement des avis
# ---------------------------------------

print("\nChargement des avis...")

with open(
    REVIEWS_FILE,
    "r",
    encoding="utf-8"
) as file:

    reviews = json.load(file)


print(
    f"Avis disponibles : "
    f"{len(reviews)}"
)


# ---------------------------------------
# 5. Regroupement des avis par classe
# ---------------------------------------

groups = defaultdict(list)

for review in reviews:

    sentiment = rating_to_sentiment(
        review["rating"]
    )

    groups[sentiment].append(
        review
    )


print("\nRépartition complète :")

for sentiment in LABELS:

    print(
        f"- {sentiment}: "
        f"{len(groups[sentiment])}"
    )


# ---------------------------------------
# 6. Échantillonnage équilibré
# ---------------------------------------

random.seed(
    RANDOM_SEED
)

sample = []

for sentiment in LABELS:

    selected = random.sample(
        groups[sentiment],
        SAMPLES_PER_CLASS
    )

    sample.extend(
        selected
    )


# Mélange les 150 avis
random.shuffle(
    sample
)


print()

print(
    f"Avis sélectionnés : "
    f"{len(sample)}"
)

print(
    f"{SAMPLES_PER_CLASS} "
    f"avis par classe"
)


# ---------------------------------------
# 7. Chargement du modèle IA
# ---------------------------------------

print(
    "\nChargement du modèle IA..."
)

classifier = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME
)

print(
    "Modèle chargé."
)


# ---------------------------------------
# 8. Prédictions
# ---------------------------------------

y_true = []
y_pred = []

results = []


print(
    "\nAnalyse en cours..."
)


for index, review in enumerate(
    sample,
    start=1
):

    # Texte réel de l'avis
    text = review["text"]

    # Sentiment attendu à partir
    # de la note Amazon
    expected = rating_to_sentiment(
        review["rating"]
    )

    # Prédiction du modèle IA
    prediction = classifier(
        text,
        truncation=True,
        max_length=512
    )[0]

    predicted = (
        prediction["label"]
        .lower()
    )

    confidence = (
        prediction["score"]
    )

    # Stockage pour les métriques
    y_true.append(
        expected
    )

    y_pred.append(
        predicted
    )

    # Sauvegarde détaillée
    results.append({

        "review_id":
            review["review_id"],

        "rating":
            review["rating"],

        "expected":
            expected,

        "predicted":
            predicted,

        "confidence":
            round(
                confidence,
                4
            ),

        "correct":
            expected == predicted
    })

    # Affichage de progression
    print(
        f"{index}/{len(sample)} "
        f"| note={review['rating']} "
        f"| attendu={expected} "
        f"| prédit={predicted} "
        f"| confiance={confidence:.2%}"
    )


# ---------------------------------------
# 9. Calcul de l'accuracy
# ---------------------------------------

correct = sum(
    1
    for true, pred in zip(
        y_true,
        y_pred
    )
    if true == pred
)

incorrect = (
    len(y_true) - correct
)

accuracy = (
    correct / len(y_true)
)


# ---------------------------------------
# 10. Calcul Precision / Recall / F1
# ---------------------------------------

metrics = calculate_metrics(
    y_true,
    y_pred,
    LABELS
)


# ---------------------------------------
# 11. Calcul matrice de confusion
# ---------------------------------------

matrix = calculate_confusion_matrix(
    y_true,
    y_pred,
    LABELS
)


# ---------------------------------------
# 12. Affichage des résultats
# ---------------------------------------

print()

print("=" * 60)
print("RÉSULTATS")
print("=" * 60)


print(
    f"Avis testés : "
    f"{len(y_true)}"
)

print(
    f"Prédictions correctes : "
    f"{correct}"
)

print(
    f"Prédictions incorrectes : "
    f"{incorrect}"
)

print(
    f"Accuracy : "
    f"{accuracy:.2%}"
)


# ---------------------------------------
# 13. Rapport de classification
# ---------------------------------------

print()

print(
    "RAPPORT DE CLASSIFICATION"
)

print(
    "-" * 60
)

print(
    f"{'Classe':<12}"
    f"{'Precision':>12}"
    f"{'Recall':>12}"
    f"{'F1-score':>12}"
)

for label in LABELS:

    values = metrics[
        label
    ]

    print(
        f"{label:<12}"
        f"{values['precision']:>12.3f}"
        f"{values['recall']:>12.3f}"
        f"{values['f1']:>12.3f}"
    )


# ---------------------------------------
# 14. Moyenne des F1
# ---------------------------------------

macro_f1 = sum(
    metrics[label]["f1"]
    for label in LABELS
) / len(LABELS)


print(
    "-" * 60
)

print(
    f"{'Macro F1':<12}"
    f"{'':>12}"
    f"{'':>12}"
    f"{macro_f1:>12.3f}"
)


# ---------------------------------------
# 15. Matrice de confusion
# ---------------------------------------

print()

print(
    "MATRICE DE CONFUSION"
)

print(
    "-" * 60
)

print(
    "              "
    "PRED_NEG "
    "PRED_NEU "
    "PRED_POS"
)


for label, row in zip(
    LABELS,
    matrix
):

    print(
        f"{label:>8} : "
        f"{row[0]:>8} "
        f"{row[1]:>8} "
        f"{row[2]:>8}"
    )


# ---------------------------------------
# 16. Sauvegarde JSON
# ---------------------------------------

OUTPUT_FILE = (
    "data/processed/"
    "sentiment_evaluation_balanced.json"
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        results,
        file,
        ensure_ascii=False,
        indent=2
    )


print()

print(
    f"Résultats enregistrés : "
    f"{OUTPUT_FILE}"
)

print("=" * 60)