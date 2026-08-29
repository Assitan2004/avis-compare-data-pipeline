# Résolution d'incident — Pipeline CI/CD

## Contexte

Lors de la mise en place du pipeline d'intégration continue (`.github/workflows/ci.yml`), destiné à automatiser les tests de l'API data et du modèle IA (compétences C13/C18), plusieurs incidents se sont succédé avant d'obtenir une exécution stable. Ce document retrace leur diagnostic et leur résolution.

---

## Incident 1 — Erreur d'import du module `src`

**Symptôme**

```
ModuleNotFoundError: No module named 'src'
```

**Diagnostic**

Les fichiers de test (`tests/test_api.py`, `tests/test_ai_api.py`) importent le code applicatif avec `from src.api.main import app`. Cet import absolu nécessite que la racine du projet soit connue de Python au moment de l'exécution des tests. Le fichier `pytest.ini`, qui configure ce comportement (`pythonpath = .`), n'avait pas été inclus dans l'archive du projet transmise, et n'était donc pas présent sur le dépôt GitHub au premier lancement du pipeline.

**Résolution**

Reconstruction du fichier `pytest.ini` à la racine du projet :

```ini
[pytest]
pythonpath = .
testpaths = tests
```

---

## Incident 2 — Dépendance manquante pour le tokenizer (`sentencepiece`)

**Symptôme**

```
ValueError: `tiktoken` is required to read a `tiktoken` file.
Install it with `pip install tiktoken`.
```

précédé de :

```
SentencePieceExtractor requires the SentencePiece library but it was not found in your environment.
```

**Diagnostic**

Le modèle de sentiment (`cardiffnlp/twitter-xlm-roberta-base-sentiment`) utilise un tokenizer au format SentencePiece. La bibliothèque `transformers` tente de le lire nativement via la bibliothèque `sentencepiece` ; en son absence, elle bascule sur un extracteur `tiktoken` alternatif, qui échoue à son tour car ce format n'est pas non plus compatible avec le fichier du modèle.

**Résolution**

Ajout de `sentencepiece` à la liste des dépendances installées dans le pipeline CI.

---

## Incident 3 — Dépendance manquante pour le tokenizer (`protobuf`)

**Symptôme**

```
SentencePieceExtractor requires the protobuf library but it was not found in your environment.
```

**Diagnostic**

Une fois `sentencepiece` installé, une deuxième dépendance transitive s'est révélée nécessaire : `protobuf`, requis par `sentencepiece` pour désérialiser le fichier du modèle. Ce type de dépendance en cascade est fréquent avec les bibliothèques de traitement de modèles pré-entraînés.

**Résolution**

Ajout de `protobuf` à la liste des dépendances installées dans le pipeline CI.

---

## Incident 4 — Tests en échec faute de données (`assert []`)

**Symptôme**

```
FAILED tests/test_api.py::test_product_detail - assert []
FAILED tests/test_api.py::test_product_reviews - assert []
FAILED tests/test_api.py::test_product_sentiment_summary - assert []
3 failed, 9 passed
```

**Diagnostic**

Ces trois tests s'appuient sur une fonction utilitaire, `get_existing_product_id()`, qui interroge `/products?limit=1` et attend qu'au moins un produit soit renvoyé (`assert data["products"]`). Le pipeline CI chargeait bien le schéma de la base de données (`schema.sql`), mais ne l'alimentait avec aucune donnée réelle : la base restait vide, et cette assertion échouait systématiquement.

**Résolution**

Ajout d'une étape d'import des données réelles, exécutant `src/database/import_data.py` (qui charge `products.json` et `reviews.json`) après la création du schéma et avant le lancement des tests. Vérifié en conditions réelles : 15 977 produits et 19 995 avis importés avec succès, ce qui a permis aux trois tests de passer.

---

## Résultat final

Après ces quatre corrections successives, le pipeline s'exécute intégralement avec succès (statut vert), incluant :
- le chargement du schéma PostgreSQL,
- l'import des données réelles,
- l'exécution complète des tests de l'API data (`test_api.py`),
- l'exécution complète des tests du modèle IA (`test_ai_api.py`).

## Ce que cet incident illustre

Chaque correction a été validée une par une, dans l'ordre où les erreurs sont apparues, sans supposition — le pipeline n'a été déclaré fonctionnel qu'une fois un résultat vert obtenu, avec la preuve (logs GitHub Actions) à l'appui.