"""
Extraction depuis un service web (API tierce).

Ce script appelle une API REST publique (exchangerate-api.com / open.er-api.com)
pour récupérer le taux de change USD -> EUR en temps réel, puis convertit
les prix des produits AvisCompare (collectés en dollars, source Amazon US)
afin d'afficher un prix en euros dans l'application.

C'est une vraie extraction depuis un service web, distincte du scraping
(page web) et du dataset (fichier statique) déjà couverts par le projet.

Entrée :
    data/processed/products.json

Sortie :
    data/processed/products_eur.json
"""

import json
import logging
from pathlib import Path

import requests


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PRODUCTS_FILE = Path("data/processed/products.json")
OUTPUT_FILE = Path("data/processed/products_eur.json")

# API publique, sans clé, taux de change mis à jour quotidiennement
EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"


def fetch_usd_to_eur_rate() -> float:
    """
    Appelle l'API de taux de change et retourne le taux USD -> EUR.
    """

    log.info(f"Appel du service web : {EXCHANGE_API_URL}")

    response = requests.get(EXCHANGE_API_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    if data.get("result") != "success":
        raise RuntimeError(f"Réponse inattendue de l'API : {data}")

    rate = data["rates"]["EUR"]
    log.info(f"Taux récupéré : 1 USD = {rate} EUR")

    return rate


def convert_products(rate: float):
    """
    Charge les produits, convertit les prix USD -> EUR, sauvegarde le résultat.
    """

    with PRODUCTS_FILE.open("r", encoding="utf-8") as f:
        products = json.load(f)

    n_converted = 0

    for product in products:
        price_usd = product.get("price")
        if price_usd is not None:
            product["price_eur"] = round(price_usd * rate, 2)
            n_converted += 1
        else:
            product["price_eur"] = None

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    log.info(f"Produits convertis : {n_converted} / {len(products)}")
    log.info(f"Fichier écrit : {OUTPUT_FILE}")


def main():
    rate = fetch_usd_to_eur_rate()
    convert_products(rate)


if __name__ == "__main__":
    main()