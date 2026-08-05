"""Shop identity for Marché Akwa Viviane (Akwa, Douala).

Keep this module aligned with ``seed.sql``. Counter nicknames map to ledger
display names used in credit, supplier, and stock asks.
"""

from __future__ import annotations

SHOP_NAME = "Marché Akwa Viviane"
FIXTURE_ID = "marche_akwa"
DEFAULT_DB_FILENAME = "marche_akwa.sqlite"

# Default product when staff say "crates on credit" without naming an item.
DEFAULT_CREDIT_SKU = "Caisse boisson malt 300ml"

# Full display names plus short forms staff use at the counter.
KNOWN_CUSTOMERS = [
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
]

KNOWN_SUPPLIERS = [
    "SOCA Distribution Douala",
    "SOCA Distribution",
    "SOCA",
    "Grosserie Portuaire Bonaberi",
    "Grosserie Portuaire",
    "Portuaire",
    "Bonaberi",
]

KNOWN_SKUS = [
    "Caisse boisson malt 300ml",
    "Sac riz 25kg",
    "Bidon huile palme 5L",
    "soda",
    "malt",
    "boisson",
    "rice",
    "riz",
    "oil",
    "huile",
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
}

_SUPPLIER_ALIASES = {
    "soca distribution douala": "SOCA Distribution Douala",
    "soca distribution": "SOCA Distribution Douala",
    "soca": "SOCA Distribution Douala",
    "grosserie portuaire bonaberi": "Grosserie Portuaire Bonaberi",
    "grosserie portuaire": "Grosserie Portuaire Bonaberi",
    "portuaire": "Grosserie Portuaire Bonaberi",
    "bonaberi": "Grosserie Portuaire Bonaberi",
}

_SKU_ALIASES = {
    "caisse boisson malt 300ml": "Caisse boisson malt 300ml",
    "soda": "Caisse boisson malt 300ml",
    "malt": "Caisse boisson malt 300ml",
    "boisson": "Caisse boisson malt 300ml",
    "sac riz 25kg": "Sac riz 25kg",
    "rice": "Sac riz 25kg",
    "riz": "Sac riz 25kg",
    "bidon huile palme 5l": "Bidon huile palme 5L",
    "oil": "Bidon huile palme 5L",
    "huile": "Bidon huile palme 5L",
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
