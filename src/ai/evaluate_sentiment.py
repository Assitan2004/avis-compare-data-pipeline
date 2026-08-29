import json
from collections import Counter
from transformers import pipeline


MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
REVIEWS_FILE = "data/processed/reviews.json"
SAMPLE_SIZE = 100


def rating_to_sentiment(rating):
    """Transforme la note Amazon en sentiment de référence."""
    rating = float(rating)

    if rating <= 2:
        return "negative"
    elif rating == 3:
        return "neutral"
    else:
        return "positive"


print("=" * 50)
print("ÉVALUATION DU MODÈLE DE SENTIMENT")
print("=" * 50)

# 1. Chargement des vrais avis
print("\nChargement des avis Amazon...")

with open(REVIEWS_FILE, "r", encoding="utf-8") as file:
    reviews = json.load(file)

print(f"Avis disponibles : {len(reviews)}")

# On limite volontairement le test
sample = reviews[:SAMPLE_SIZE]

print(f"Avis sélectionnés pour l'évaluation : {len(sample)}")


# 2. Chargement du modèle
print("\nChargement du modèle IA...")

classifier = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME
)

print("Modèle chargé.")


# 3. Évaluation
correct = 0
results = []

expected_counts = Counter()
predicted_counts = Counter()

print("\nAnalyse en cours...")

for index, review in enumerate(sample, start=1):

    rating = float(review["rating"])
    text = review["text"]

    expected = rating_to_sentiment(rating)

    # Limite la taille du texte pour le modèle
    prediction = classifier(
        text,
        truncation=True,
        max_length=512
    )[0]

    predicted = prediction["label"].lower()
    confidence = prediction["score"]

    is_correct = predicted == expected

    if is_correct:
        correct += 1

    expected_counts[expected] += 1
    predicted_counts[predicted] += 1

    results.append({
        "rating": rating,
        "expected": expected,
        "predicted": predicted,
        "confidence": round(confidence, 4),
        "correct": is_correct
    })

    print(
        f"{index}/{len(sample)} "
        f"| note={rating} "
        f"| attendu={expected} "
        f"| prédit={predicted} "
        f"| confiance={confidence:.2%}"
    )


# 4. Calcul de l'accuracy
accuracy = correct / len(sample)


# 5. Résultats
print("\n" + "=" * 50)
print("RÉSULTATS")
print("=" * 50)

print(f"Avis testés : {len(sample)}")
print(f"Prédictions correctes : {correct}")
print(f"Prédictions incorrectes : {len(sample) - correct}")
print(f"Accuracy : {accuracy:.2%}")

print("\nRépartition attendue :")
for sentiment, count in expected_counts.items():
    print(f"- {sentiment}: {count}")

print("\nRépartition prédite :")
for sentiment, count in predicted_counts.items():
    print(f"- {sentiment}: {count}")


# 6. Sauvegarde
output_file = "data/processed/sentiment_evaluation.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(results, file, ensure_ascii=False, indent=2)

print(f"\nRésultats enregistrés : {output_file}")