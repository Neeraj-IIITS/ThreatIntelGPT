# src/extractors.py

import re
from typing import Dict, List
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# -------------------------
# IOC Regex Patterns
# -------------------------

IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.|$)){4}\b"
)

DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",
    re.IGNORECASE
)

URL_RE = re.compile(
    r"\bhttps?://[^\s\"']+",
    re.IGNORECASE
)

MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA1_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")

# -------------------------
# IOC Extraction
# -------------------------

def extract_iocs(text: str) -> Dict[str, List[str]]:
    """
    Extract Indicators of Compromise (IOCs).
    """
    if not text:
        return {
            "ips": [],
            "domains": [],
            "urls": [],
            "md5": [],
            "sha1": [],
            "sha256": []
        }

    return {
        "ips": list(set(IP_RE.findall(text))),
        "domains": list(set(DOMAIN_RE.findall(text))),
        "urls": list(set(URL_RE.findall(text))),
        "md5": list(set(MD5_RE.findall(text))),
        "sha1": list(set(SHA1_RE.findall(text))),
        "sha256": list(set(SHA256_RE.findall(text))),
    }

# -------------------------
# Named Entity Recognition (NER)
# -------------------------

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities using spaCy.
    """
    if not text:
        return {}

    doc = nlp(text)
    entities: Dict[str, List[str]] = {}

    for ent in doc.ents:
        entities.setdefault(ent.label_, []).append(ent.text)

    # Deduplicate values
    for label in entities:
        entities[label] = list(set(entities[label]))

    return entities

# -------------------------
# MITRE ATT&CK Extraction
# -------------------------

MITRE_KEYWORDS = {
    "phishing": "T1566",
    "spearphishing": "T1566.001",
    "ransomware": "T1486",
    "persistence": "T1547",
    "privilege escalation": "T1068",
    "credential dumping": "T1003",
    "lateral movement": "T1021",
    "mimikatz": "T1003.001",
    "powershell": "T1059.001",
    "sql injection": "T1190",
    "bruteforce": "T1110",
    "c2": "T1105",
    "command and control": "T1105",
    "ddos": "T1499",
    "exfiltration": "T1041",
    "tor": "T1090.003",
    "keylogging": "T1056.001",
    "malware": "T1204",
}

def extract_mitre(text: str) -> Dict[str, List[str]]:
    """
    Extract MITRE ATT&CK techniques using keyword matching.
    Returns:
        { "techniques": ["T1059", "T1486"] }
    """
    if not text:
        return {"techniques": []}

    text_l = text.lower()
    techniques = []

    for keyword, technique in MITRE_KEYWORDS.items():
        if keyword in text_l:
            techniques.append(technique)

    return {"techniques": list(set(techniques))}
