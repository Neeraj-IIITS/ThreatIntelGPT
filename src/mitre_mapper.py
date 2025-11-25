# src/mitre_mapper.py

import json
from pathlib import Path
from typing import Dict, List

# Path to the MITRE rules JSON file
RULES_PATH = Path(__file__).resolve().parent.parent / "mitre_rules.json"

# Load rules (keyword → technique list)
with open(RULES_PATH, "r", encoding="utf-8") as f:
    MITRE_RULES = json.load(f)

def map_mitre(text: str) -> Dict[str, List[str]]:
    """
    Rule-based MITRE ATT&CK technique mapping.
    Uses MITRE_RULES JSON file for keyword → technique mapping.
    """
    if not text:
        return {
            "matched_keywords": [],
            "techniques": []
        }

    text_lower = text.lower()

    matched_keywords = []
    techniques = []

    for keyword, technique_list in MITRE_RULES.items():
        if keyword.lower() in text_lower:
            matched_keywords.append(keyword)
            techniques.extend(technique_list)

    # Deduplicate techniques
    techniques = list(dict.fromkeys(techniques))

    return {
        "matched_keywords": matched_keywords,
        "techniques": techniques
    }


# ---------------------------------------------------------
# ⭐ REQUIRED BY API: WRAPPER FUNCTION
# ---------------------------------------------------------

def map_mitre_from_text(text: str) -> Dict[str, List[str]]:
    """
    Wrapper function required by api.py.
    Internally calls map_mitre().
    """
    return map_mitre(text)
