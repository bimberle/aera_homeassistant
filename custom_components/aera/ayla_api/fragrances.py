"""
Aera Fragrance Constants and API.

This module provides:
1. A static fallback list of known fragrances
2. A function to fetch the latest fragrances from Contentful

The fragrance ID is a 3-letter code used by the aeraMini's set_fragrance_identifier property.
"""

import aiohttp
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# Contentful API credentials (from APK decompilation)
CONTENTFUL_SPACE_ID = "bsswjwaepi0w"
CONTENTFUL_ACCESS_TOKEN = "UC4IVgBwitvaugwTZQLSvO28UcUdUumEvpOy4MejPUg"
CONTENTFUL_API_URL = f"https://cdn.contentful.com/spaces/{CONTENTFUL_SPACE_ID}/entries"

# Static fallback mapping of fragrance ID to fragrance name
# This is used if the Contentful API is unavailable
FRAGRANCES = {
    "APC": "Alpine Cedar",
    "AMC": "Amalfi Coast",
    "ABS": "Amber Skies",
    "APO": "Apple Orchard",
    "BBY": "Baby",
    "BSM": "Balsam",
    "BJD": "Bamboo Jardin",
    "BCH": "Beach House",
    "BTO": "Bitter Orange",
    "BLS": "Bliss",
    "LBB": "Blushed Bergamot",
    "ABB": "Brooklyn Brownstone",
    "CDL": "Christmas Delight",
    "CTS": "Citrus",
    "CTG": "Citrus Grove",
    "HCS": "Citrus and Sage",
    "CLS": "Classic",
    "CCP": "Coconut Paradise",
    "CTY": "Curiosity",
    "DST": "De-Stress Mind",
    "AEC": "English Cottage",
    "FDB": "Feu de Bois",
    "FSH": "Flower Shop",
    "FST": "Forest Therapy",
    "GRB": "GOOD Riddance Bathroom Odor",
    "GRC": "GOOD Riddance Cooking Odor",
    "GRM": "GOOD Riddance Musty Odor",
    "GRP": "GOOD Riddance Pet Odor",
    "GRS": "GOOD Riddance Smoke Odor",
    "HHG": "Geranium",
    "GRG": "Green Gardens",
    "HTJ": "Tea Tree and Juniper",
    "HBR": "Havana Breeze",
    "HAI": "Hawai'i",
    "HSP": "Holiday Spice",
    "IBL": "In Bloom",
    "IDG": "Indigo",
    "KTH": "Kyoto Teahouse",
    "LVR": "Lavender",
    "HLB": "Lavender and Bergamot",
    "LTM": "Lavender and the Moon",
    "LMN": "Lemon Neroli",
    "LAC": "Lilac Daydream",
    "LTS": "Lime Twist",
    "LIN": "Linen",
    "HLL": "Linen and Lemon",
    "LFL": "L'Avant Collective Fresh Linen",
    "MJF": "Majestic Fir",
    "MJS": "Mediterranean Jasmine",
    "HME": "Mint and Eucalyptus",
    "MLC": "Monique Lhuillier Citrus Lily",
    "MLD": "Monique Lhuillier Dolce",
    "MLL": "Monique Lhuillier Limone",
    "MDN": "Moondance",
    "TEN": "No. 10",
    "247": "No. 247",
    "723": "No. 723",
    "OBZ": "Ocean Breeze",
    "PCS": "Pacific Surf",
    "PDC": "Paddock Club",
    "PSO": "Palo Santo",
    "PRS": "Paris",
    "PBR": "Pear Brulée",
    "PCB": "Pink Cherry Blossom",
    "PTY": "Poetry",
    "PKS": "Pumpkin Spice",
    "RBM": "Rainbow Mist",
    "RVE": "Revive",
    "ROS": "Rose",
    "SDL": "Sandalwood",
    "CSS": "Signature Scent",
    "SCC": "Skylar Coconut Cove",
    "SLS": "Skylar Lime Sands",
    "SVS": "Skylar Vanilla Sky",
    "SFL": "Snowfall",
    "SFP": "Soft Pants",
    "SSM": "Soft Sunday",
    "SPF": "Spring Fresh",
    "SPB": "Support Breathe",
    "ESM": "The Emerald Spring",
    "TRS": "Tropical Sunrise",
    "ATV": "Tuscan Villa",
    "UCS": "Under the Citrus Sun",
    "VAN": "Vanilla",
    "VTW": "Velvet Woods",
    "VBR": "Vibrance",
    "WPM": "White Peppermint",
    "WHT": "White Tea",
    "WBB": "Wild Bluebells",
    "WRR": "Wildrose Rains",
    "ZPR": "Zephyr",
}

# Reverse mapping: name to ID
FRAGRANCE_IDS = {name: fid for fid, name in FRAGRANCES.items()}

# Cache for dynamically fetched fragrances
_cached_fragrances: Optional[dict[str, str]] = None


async def fetch_fragrances(session: Optional[aiohttp.ClientSession] = None) -> dict[str, str]:
    """
    Fetch the latest fragrance list from Contentful.
    
    This queries the Aera content management system for the current list
    of available fragrances. Results are cached for subsequent calls.
    
    Args:
        session: Optional aiohttp session to reuse
        
    Returns:
        Dict mapping fragrance ID (e.g., "IDG") to name (e.g., "Indigo")
    """
    global _cached_fragrances
    
    if _cached_fragrances is not None:
        return _cached_fragrances
    
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
    
    try:
        params = {
            "content_type": "fragrance",
            "access_token": CONTENTFUL_ACCESS_TOKEN,
            "limit": 1000,
        }
        
        async with session.get(CONTENTFUL_API_URL, params=params) as resp:
            if resp.status != 200:
                _LOGGER.warning(f"Failed to fetch fragrances from Contentful: {resp.status}")
                return FRAGRANCES  # Return static fallback
            
            data = await resp.json()
        
        fragrances = {}
        for item in data.get("items", []):
            fields = item.get("fields", {})
            fid = fields.get("fragranceId")
            name = fields.get("fragranceName")
            if fid and name:
                fragrances[fid] = name
        
        if fragrances:
            _cached_fragrances = fragrances
            _LOGGER.info(f"Fetched {len(fragrances)} fragrances from Contentful")
            return fragrances
        else:
            _LOGGER.warning("No fragrances found in Contentful, using static fallback")
            return FRAGRANCES
            
    except Exception as e:
        _LOGGER.warning(f"Error fetching fragrances: {e}, using static fallback")
        return FRAGRANCES
    finally:
        if close_session:
            await session.close()


def clear_fragrance_cache():
    """Clear the cached fragrances to force a refresh on next fetch."""
    global _cached_fragrances
    _cached_fragrances = None


def get_fragrance_name(fragrance_id: str) -> str | None:
    """Get the fragrance name for a given ID."""
    return FRAGRANCES.get(fragrance_id.upper())


def get_fragrance_id(fragrance_name: str) -> str | None:
    """Get the fragrance ID for a given name."""
    return FRAGRANCE_IDS.get(fragrance_name)
