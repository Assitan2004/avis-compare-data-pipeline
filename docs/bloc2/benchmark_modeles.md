# Benchmark des modèles d'analyse de sentiment

*Compétences C6 (veille technique) et C7 (benchmark de services IA préexistants)*

## Objectif

AvisCompare utilise le modèle `cardiffnlp/twitter-xlm-roberta-base-sentiment` pour classer les avis clients en positif, neutre ou négatif. Ce document compare ce choix à deux alternatives plus légères, pour justifier objectivement la décision.

## Candidats comparés

| Modèle | Type | Caractéristiques |
|---|---|---|
| **cardiffnlp/twitter-xlm-roberta-base-sentiment** *(retenu)* | Transformeur pré-entraîné (deep learning) | Multilingue, comprend le contexte et les négations, mais plus lourd (~600 Mo avec ses dépendances) |
| **VADER** (`vaderSentiment`) | Lexique de mots + règles | Très léger, pas d'installation lourde, conçu à l'origine pour les réseaux sociaux |
| **TextBlob** | Lexique de mots (polarité moyenne) | Léger, simple à utiliser, peu de gestion du contexte |

## Méthodologie

Un échantillon de 12 avis réels du dataset AvisCompare a été constitué, avec une répartition volontairement équilibrée : 4 avis notés 1-2 étoiles, 4 avis notés 3 étoiles, 4 avis notés 4-5 étoiles. La note du client sert de référence approximative pour vérifier si le sentiment détecté est cohérent (note ≥ 4 → positif attendu, note = 3 → neutre attendu, note ≤ 2 → négatif attendu).

Cette méthode a des limites (une note ne reflète pas toujours parfaitement le ton du texte, c'est d'ailleurs tout l'enjeu détecté par AvisCompare via `rating_sentiment_conflict`), mais elle permet une comparaison objective sur un même jeu de données.

## Résultats obtenus

### VADER — 6 / 12 avis concordants avec la note (50 %)

VADER a des difficultés marquées sur les avis négatifs et neutres : par exemple, l'avis noté 1 étoile *"This was a gift however works well!!!"* est classé **positif** par VADER (à cause de "works well!!!"), alors que le client exprime en réalité une insatisfaction. VADER ne capture pas ce type de nuance contextuelle.

### TextBlob — 8 / 12 avis concordants avec la note (67 %)

Meilleur que VADER sur cet échantillon, notamment sur les avis neutres, mais reste un modèle à base de lexique : il additionne la polarité de mots isolés sans réelle compréhension de phrase.

### cardiffnlp (modèle retenu)

Ce modèle n'a pas pu être ré-exécuté sur ce même échantillon dans cet exercice de comparaison (contrainte d'environnement lors de la rédaction de ce document). Son comportement a cependant déjà été vérifié à de nombreuses reprises dans le projet :
- Les tests automatisés (`tests/test_ai_api.py`), exécutés avec succès dans le pipeline CI, valident par exemple qu'un texte explicitement positif ("This product is amazing, I love it!") est bien classé positif, et qu'un texte explicitement négatif est bien classé négatif
- Contrairement à VADER/TextBlob, son architecture (transformeur) traite la phrase dans son ensemble plutôt que mot à mot, ce qui le rend structurellement mieux armé pour des formulations ambiguës comme l'exemple VADER ci-dessus

## Justification du choix final

**cardiffnlp est conservé** comme modèle de production, pour trois raisons :

1. **Compréhension contextuelle** : les modèles à base de lexique (VADER, TextBlob) échouent précisément sur les cas les plus utiles à détecter pour AvisCompare — les avis où la note et le ton du texte divergent
2. **Multilinguisme natif** : VADER et TextBlob sont conçus pour l'anglais ; cardiffnlp gère plusieurs langues nativement, ce qui laisse la porte ouverte à des avis non-anglophones
3. **Score de confiance intégré** : cardiffnlp fournit un score de confiance par prédiction, exploité par AvisCompare (seuil à 60 %) pour signaler les résultats peu fiables — VADER et TextBlob ne proposent pas nativement cette information de façon comparable

**Coût accepté en contrepartie** : un modèle plus lourd (~600 Mo), plus lent à charger, et nécessitant des dépendances supplémentaires (`sentencepiece`, `protobuf` — voir `INCIDENT.md` pour le détail de leur découverte lors de la mise en place du pipeline CI).

## Veille réglementaire associée (C6)

- Le modèle `cardiffnlp/twitter-xlm-roberta-base-sentiment` est publié publiquement sur Hugging Face sous une licence permettant un usage de ce type
- Les données utilisées pour l'analyse (texte des avis) ne contiennent pas d'information personnelle identifiante (voir `RGPD.md`), ce qui simplifie le respect du RGPD lors de leur traitement par le modèle