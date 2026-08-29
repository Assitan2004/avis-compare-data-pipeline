# Conformité RGPD — AvisCompare

## Nature des données collectées

AvisCompare collecte exclusivement des données publiques liées aux produits et à leurs avis :
- Informations produit (nom, marque, catégorie, prix, note moyenne)
- Contenu des avis (texte, note, date, statut d'achat vérifié)

## Absence de données personnelles

Le schéma de la base de données (`database/schema.sql`) ne contient **aucune donnée à caractère personnel identifiante** :
- Pas de nom d'auteur d'avis
- Pas d'adresse email
- Pas d'identifiant utilisateur
- Pas d'adresse IP ni de données de géolocalisation individuelle

Seul le contenu textuel de l'avis est traité, de façon anonyme, pour l'analyse de sentiment.

## Origine et licence des données

- **Amazon Reviews 2023** (Hugging Face, McAuley-Lab) : dataset public utilisé à des fins de recherche/éducation
- **Scraping Sandbox** : site de démonstration public dédié à l'apprentissage du web scraping, sans données réelles de clients

## Principe de minimisation

Conformément à l'article 5 du RGPD, seules les données strictement nécessaires à l'analyse de sentiment et à la comparaison de produits sont collectées et stockées.