# Architecture technique — AvisCompare

## Vue d'ensemble

```
Sources de données (scraping + dataset + API taux de change)
        ↓
Nettoyage & normalisation (Python)
        ↓
Base de données PostgreSQL
        ↓
API REST unique — FastAPI (données + IA)
        ↓
Front-end — Vue 3
```

Le détail de chaque étape est décrit dans `AvisCompare_Comprendre_le_projet.md`. Ce document se concentre sur le **pourquoi** de chaque choix technique structurant.

---

## Pourquoi FastAPI pour l'API

- **Validation automatique des données** : les modèles Pydantic valident chaque requête/réponse sans code de vérification manuel
- **Documentation générée automatiquement** : l'interface Swagger (`/docs`) permet de tester chaque endpoint sans outil externe, ce qui a servi de preuve tout au long du projet
- **Écosystème Python cohérent** avec le reste du pipeline (collecte, nettoyage, modèle IA), évitant de mélanger plusieurs langages

## Pourquoi PostgreSQL

- Les données d'AvisCompare sont **fortement relationnelles** (un produit a plusieurs avis, un avis appartient à un seul produit) : un modèle relationnel avec clés étrangères garantit l'intégrité de ces liens, ce qu'un simple stockage fichier ne permettrait pas
- Les contraintes de type strictes (`NUMERIC(2,1)` pour les notes, `CHECK` sur les plages de valeurs) évitent les erreurs d'arrondi et les données invalides dès l'insertion
- PostgreSQL est open source, largement documenté, et suffisant pour le volume actuel du projet (~36 000 lignes) sans complexité d'infrastructure supplémentaire

## Pourquoi une seule API, plutôt que deux séparées (données / IA)

Contrairement à une architecture qui séparerait l'exposition des données et celle du modèle IA en deux services distincts, AvisCompare centralise les deux dans `main.py`.

**Avantage** : simplicité de déploiement et de maintenance pour un projet de cette taille, un seul point d'entrée à documenter et à sécuriser.

**Limite assumée** : cela crée un couplage fort — comme découvert lors de la mise en place du pipeline CI (voir `INCIDENT.md`), impossible de tester les endpoints de données sans charger aussi le modèle IA, puisque `sentiment_service.py` est importé dès le chargement de `main.py`. Une évolution future pourrait séparer les deux pour gagner en légèreté et en rapidité de test.

## Pourquoi réutiliser un modèle IA pré-entraîné plutôt qu'en entraîner un

- Entraîner un modèle de classification de sentiment demanderait un **jeu de données labellisé** (avis annotés positif/neutre/négatif), qu'AvisCompare ne possède pas
- Le modèle `cardiffnlp/twitter-xlm-roberta-base-sentiment` est public, déjà entraîné, multilingue, et directement exploitable via la bibliothèque `transformers`
- Ce choix évite un travail d'entraînement et d'évaluation hors de portée du périmètre du projet, au prix d'une dépendance à un modèle non ajusté spécifiquement aux avis produits

## Pourquoi pas de cache sur l'analyse de sentiment

Chaque avis est ré-analysé à chaque consultation plutôt que stocké une fois pour toutes. Ce choix privilégie une donnée **toujours à jour** (si le modèle évolue, les résultats suivent) au prix d'un temps de réponse plus long. Pour un usage à plus grande échelle, la mise en cache des résultats par avis serait une optimisation à envisager.

## Pourquoi un vocabulaire de sentiment unique (positif / neutre / négatif)

Fixer ces trois labels comme seul vocabulaire possible dans tout le projet (base de données, API, front-end) évite les incohérences entre les différentes couches de l'application — un même résultat ne peut jamais être nommé différemment selon l'endroit où il est affiché.