from transformers import pipeline


MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

print("==============================")
print("TEST IA - ANALYSE DE SENTIMENT")
print("==============================")

print("Chargement du modèle...")

classifier = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME
)

print("Modèle chargé.")
print()

texts = [
    "This product is amazing, I love it!",
    "The product is okay, nothing special.",
    "This is terrible, I want my money back."
]

for text in texts:
    result = classifier(text)[0]

    print("Avis :", text)
    print("Sentiment :", result["label"])
    print("Confiance :", round(result["score"], 4))
    print("------------------------------")