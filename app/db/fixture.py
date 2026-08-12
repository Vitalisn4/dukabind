"""Shop identities for the two ledger fixtures.

* Marché Akwa Viviane (Akwa, Douala), the primary demo shop (``seed.sql``).
* Marché Nkolmébé (Yaoundé), the second fixture (``seed_duka_b.sql``) used by
  the held-out eval to prove answers bind to the live ledger and cannot be
  memorized from the first shop.

Keep this module aligned with both seed files. Counter nicknames map to ledger
display names used in credit, supplier, and stock asks. All names and aliases
between the two shops are disjoint on purpose.
"""

from __future__ import annotations

SHOP_NAME = "Marché Akwa Viviane"
FIXTURE_ID = "marche_akwa"
DEFAULT_DB_FILENAME = "marche_akwa.sqlite"

SHOP_NAME_B = "Marché Nkolmébé"
FIXTURE_ID_B = "duka_b"
DEFAULT_DB_FILENAME_B = "duka_b.sqlite"

DEFAULT_CREDIT_SKU = "Caisse boisson malt 300ml"

KNOWN_CUSTOMERS = [
    # Marché Akwa Viviane (Douala).
    "Marie-Claire Fotso",
    "Marie-Claire",
    "Marie Claire",
    "Fotso",
    "Marie",
    "Ibrahim Njoya",
    "Ibrahim",
    "Njoya",
    "Esther Tchamba",
    "Esther",
    "Tchamba",
    # Marché Nkolmébé (Yaoundé), second fixture, disjoint names.
    "Amina Bello",
    "Amina",
    "Bello",
    "Chidi Okafor",
    "Chidi",
    "Okafor",
    "Maman Rachel",
    "Maman",
    "Rachel",
]

KNOWN_SUPPLIERS = [
    # Marché Akwa Viviane (Douala).
    "SOCA Distribution Douala",
    "SOCA Distribution",
    "SOCA",
    "Grosserie Portuaire Bonaberi",
    "Grosserie Portuaire",
    "Portuaire",
    "Bonaberi",
    # Marché Nkolmébé (Yaoundé), second fixture, disjoint names.
    "Sanaga Épicerie",
    "Sanaga",
    "Épicerie",
    # ASCII variants; cashiers often skip accents when typing.
    "Sanaga Epicerie",
    "Epicerie",
    "Ciment du Cameroun",
    "Ciment",
]

KNOWN_SKUS = [
    # Marché Akwa Viviane (Douala).
    "Caisse boisson malt 300ml",
    "Sac riz 25kg",
    "Bidon huile palme 5L",
    "soda",
    "sodas",
    "malt",
    "boisson",
    "rice",
    "riz",
    "oil",
    "huile",
    # Marché Nkolmébé (Yaoundé), second fixture, disjoint names.
    "Sucre 25kg",
    "sugar",
    "sucre",
    "Savon carton 24",
    "soap",
    "savon",
    "Farine 50kg",
    "flour",
    "farine",
    # Swahili product words; stock asks in Swahili bind to the same SKUs.
    "sukari",  # sugar
    "unga",  # flour
    "mchele",  # rice
    "mafuta",  # oil
    "sabuni",  # soap
]

_CUSTOMER_ALIASES = {
    "marie-claire fotso": "Marie-Claire Fotso",
    "marie claire": "Marie-Claire Fotso",
    "marie-claire": "Marie-Claire Fotso",
    "marie": "Marie-Claire Fotso",
    "fotso": "Marie-Claire Fotso",
    "ibrahim njoya": "Ibrahim Njoya",
    "ibrahim": "Ibrahim Njoya",
    "njoya": "Ibrahim Njoya",
    "esther tchamba": "Esther Tchamba",
    "esther": "Esther Tchamba",
    "tchamba": "Esther Tchamba",
    "amina bello": "Amina Bello",
    "amina": "Amina Bello",
    "bello": "Amina Bello",
    "chidi okafor": "Chidi Okafor",
    "chidi": "Chidi Okafor",
    "okafor": "Chidi Okafor",
    "maman rachel": "Maman Rachel",
    "maman": "Maman Rachel",
    "rachel": "Maman Rachel",
}

_SUPPLIER_ALIASES = {
    "soca distribution douala": "SOCA Distribution Douala",
    "soca distribution": "SOCA Distribution Douala",
    "soca": "SOCA Distribution Douala",
    "grosserie portuaire bonaberi": "Grosserie Portuaire Bonaberi",
    "grosserie portuaire": "Grosserie Portuaire Bonaberi",
    "portuaire": "Grosserie Portuaire Bonaberi",
    "bonaberi": "Grosserie Portuaire Bonaberi",
    "sanaga epicerie": "Sanaga Épicerie",
    "sanaga": "Sanaga Épicerie",
    "epicerie": "Sanaga Épicerie",
    "sanaga épicerie": "Sanaga Épicerie",
    "épicerie": "Sanaga Épicerie",
    "ciment du cameroun": "Ciment du Cameroun",
    "ciment": "Ciment du Cameroun",
}

_SKU_ALIASES = {
    "caisse boisson malt 300ml": "Caisse boisson malt 300ml",
    "soda": "Caisse boisson malt 300ml",
    "sodas": "Caisse boisson malt 300ml",
    "malt": "Caisse boisson malt 300ml",
    "boisson": "Caisse boisson malt 300ml",
    "sac riz 25kg": "Sac riz 25kg",
    "rice": "Sac riz 25kg",
    "riz": "Sac riz 25kg",
    "bidon huile palme 5l": "Bidon huile palme 5L",
    "oil": "Bidon huile palme 5L",
    "huile": "Bidon huile palme 5L",
    "sucre 25kg": "Sucre 25kg",
    "sugar": "Sucre 25kg",
    "sucre": "Sucre 25kg",
    "savon carton 24": "Savon carton 24",
    "soap": "Savon carton 24",
    "savon": "Savon carton 24",
    "farine 50kg": "Farine 50kg",
    "flour": "Farine 50kg",
    "farine": "Farine 50kg",
    # Swahili product words.
    "sukari": "Sucre 25kg",
    "unga": "Farine 50kg",
    "mchele": "Sac riz 25kg",
    "mafuta": "Bidon huile palme 5L",
    "sabuni": "Savon carton 24",
}


def normalize_customer(raw: str | None) -> str | None:
    """Map a counter nickname to the ledger display name."""
    if not raw:
        return None
    return _CUSTOMER_ALIASES.get(raw.lower(), raw)


def normalize_supplier(raw: str | None) -> str | None:
    """Map a short supplier label to the ledger display name."""
    if not raw:
        return None
    return _SUPPLIER_ALIASES.get(raw.lower(), raw)


def normalize_sku(raw: str | None) -> str | None:
    """Map a product nickname to the ledger SKU name."""
    if not raw:
        return None
    return _SKU_ALIASES.get(raw.lower(), raw)
