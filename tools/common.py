"""Shared helpers for the JKL Trekker data tools."""

# Survey of India / NRSC Lambert Conformal Conic used by the
# "Administrative Boundary Database" district shapefile.
SOI_LCC = (
    "+proj=lcc +lat_1=12.472944 +lat_2=35.172806 +lat_0=24 +lon_0=80 "
    "+x_0=4000000 +y_0=4000000 +datum=WGS84 +units=m +no_defs"
)

# States/UTs the app covers (decoded names, upper case).
TARGET_STATES = {"JAMMU AND KASHMIR", "LADAKH"}

# The SOI shapefile stores long vowels with a special font:
# '>' = A-macron, '|' = I-macron, '@' = U-macron.
_SOI_CHARS = str.maketrans({">": "A", "|": "I", "@": "U"})

# Common spellings for districts whose plain decoding reads oddly.
_COMMON_SPELLING = {
    "BARAMULA": "Baramulla",
    "PUNCH": "Poonch",
    "SHUPIYAN": "Shopian",
    "BADGAM": "Budgam",
    "BANDIPURA": "Bandipora",
    "LAHUL & SPITI": "Lahaul & Spiti",
}


def decode_soi(name):
    """Turn an SOI-encoded upper-case name into a readable one.

    'SR|NAGAR' -> 'Srinagar', 'B>RAM@LA' -> 'Baramulla'
    """
    if name is None:
        return None
    plain = str(name).translate(_SOI_CHARS).strip()
    if plain.upper() in _COMMON_SPELLING:
        return _COMMON_SPELLING[plain.upper()]
    return " ".join(w if w == "&" else w.capitalize() for w in plain.split())


def state_of(name):
    """Decoded, upper-case state name ('LAD>KH' -> 'LADAKH')."""
    return str(name).translate(_SOI_CHARS).strip().upper() if name else ""
