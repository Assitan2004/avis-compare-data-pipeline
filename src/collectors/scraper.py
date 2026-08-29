import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "https://scrapingsandbox.com/"

OUTPUT_FILE = Path(
    "data/raw/scraping/electronics_products.json"
)


def extract_product_data(text):

    # SKU
    sku_match = re.search(
        r"(SKU-[A-Z]+-\d+)",
        text
    )

    # Prix
    prices = re.findall(
        r"\$\s*(\d+(?:\.\d{1,2})?)",
        text
    )

    # Note
    rating_match = re.search(
        r"\b([1-5](?:\.\d)?)\b",
        text
    )

    # Disponibilité
    if "Out of Stock" in text:
        availability = "Out of Stock"

    elif "In Stock" in text:
        availability = "In Stock"

    else:
        availability = None

    price = (
        float(prices[0])
        if len(prices) >= 1
        else None
    )

    old_price = (
        float(prices[1])
        if len(prices) >= 2
        else None
    )

    return {
        "raw_text": text,

        "rating": (
            float(rating_match.group(1))
            if rating_match
            else None
        ),

        "price": price,

        "old_price": old_price,

        "sku": (
            sku_match.group(1)
            if sku_match
            else None
        ),

        "availability": availability,

        "category": "Electronics",

        "source": "scrapingsandbox.com",

        "collected_at": datetime.now(
            timezone.utc
        ).isoformat()
    }


def extract_electronics_from_page(page):

    products = []

    # On examine les éléments contenant du texte
    elements = page.locator("a")

    count = elements.count()

    for i in range(count):

        try:

            text = elements.nth(i).inner_text().strip()

        except Exception:
            continue

        if "Electronics" not in text:
            continue

        if "SKU-ELE-" not in text:
            continue

        product = extract_product_data(text)

        products.append(product)

    return products


def remove_duplicates(products):

    unique = {}

    for product in products:

        sku = product["sku"]

        if sku:
            unique[sku] = product

    return list(unique.values())


def save_products(products):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2
        )


def main():

    print("==============================")
    print("DÉBUT DU SCRAPING")
    print("==============================")

    all_products = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print("Ouverture du site...")

        page.goto(
            URL,
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(2000)

        # Le site contient 21 pages
        for page_number in range(1, 22):

            print()
            print(
                f"--- PAGE {page_number} ---"
            )

            products = (
                extract_electronics_from_page(page)
            )

            print(
                f"{len(products)} produits "
                f"Electronics trouvés"
            )

            all_products.extend(products)

            # Dernière page
            if page_number == 21:
                break

            next_page = page_number + 1

            try:

                # Cherche le bouton portant
                # exactement le numéro suivant.
                button = page.get_by_role(
                    "button",
                    name=str(next_page),
                    exact=True
                )

                button.wait_for(
                    state="visible",
                    timeout=5000
                )

                button.click()

                # Attend que les produits changent
                page.wait_for_timeout(1500)

            except Exception as error:

                print(
                    f"Impossible d'accéder "
                    f"à la page {next_page}"
                )

                print(error)

                break

        browser.close()

    print()
    print("==============================")

    print(
        f"Produits collectés : "
        f"{len(all_products)}"
    )

    products_unique = remove_duplicates(
        all_products
    )

    print(
        f"Produits uniques : "
        f"{len(products_unique)}"
    )

    save_products(
        products_unique
    )

    print(
        f"Fichier créé : {OUTPUT_FILE}"
    )

    print("==============================")
    print("SCRAPING TERMINÉ")
    print("==============================")


if __name__ == "__main__":
    main()