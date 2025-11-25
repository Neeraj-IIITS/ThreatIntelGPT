import re
import spacy
from typing import Dict, List

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    # If the model is not installed, create a blank pipeline so API doesn’t crash
    nlp = spacy.blank("en")


# --------------------------------------------------------
#  IOC Extraction (IP, Domain, URL, Hashes)
# --------------------------------------------------------
def extract_iocs(text: str) -> Dict[str, List[str]]:
    """
    Extract Indicators of Compromise from text.
    Returns a dict: ips, domains, urls, md5, sha1, sha256
    """

    if not text:
        return {
            "ips": [], "domains": [], "urls": [],
            "md5": [], "sha1": [], "sha256": []
        }

    # Regex patterns
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.(?:com|net|org|io|gov|edu|in|co)\b'
    url_pattern = r'https?://[^\s"]+'
    md5_pattern = r'\b[a-fA-F0-9]{32}\b'
    sha1_pattern = r'\b[a-fA-F0-9]{40}\b'
    sha256_pattern = r'\b[a-fA-F0-9]{64}\b'

    iocs = {
        "ips": re.findall(ip_pattern, text),
        "domains": re.findall(domain_pattern, text),
        "urls": re.findall(url_pattern, text),
        "md5": re.findall(md5_pattern, text),
        "sha1": re.findall(sha1_pattern, text),
        "sha256": re.findall(sha256_pattern, text)
    }

    return iocs


# --------------------------------------------------------
#  Named Entity Extraction using spaCy
# --------------------------------------------------------
def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities: ORG, PERSON, PRODUCT, GPE, etc.
    """

    if not text:
        return {}

    doc = nlp(text)

    ents = {}
    for ent in doc.ents:
        ents.setdefault(ent.label_, []).append(ent.text)

    return ents


# --------------------------------------------------------
#  Optional basic NLP utilities
# --------------------------------------------------------
def basic_tokenize(text: str) -> List[str]:
    """Simple whitespace tokenizer."""
    return text.split()


def lemmatize_tokens(text: str) -> List[str]:
    try:
        doc = nlp(text)
        return [token.lemma_ for token in doc]
    except Exception:
        return basic_tokenize(text)
