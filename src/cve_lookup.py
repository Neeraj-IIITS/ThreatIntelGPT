# src/cve_lookup.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_API_TOKEN")

# We keep rule-based AI for now
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


# ==========================================================
# Fetch CVE details from NEW NVD API 2.0 (works reliably)
# ==========================================================
def fetch_cve_details(cve_id: str) -> dict:
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return empty_response(cve_id)

        cve = vulns[0]["cve"]

        # --- Description ---
        descriptions = cve.get("descriptions", [])
        if descriptions:
            description = descriptions[0].get("value", "")
        else:
            description = "No description available."

        # --- CVSS ---
        metrics = cve.get("metrics", {})
        score = "N/A"
        vector = "N/A"
        severity = "N/A"

        # CVSS v3.1 preferred
        if "cvssMetricV31" in metrics:
            m = metrics["cvssMetricV31"][0]
            score = m["cvssData"]["baseScore"]
            vector = m["cvssData"]["vectorString"]
            severity = m["cvssData"]["baseSeverity"]

        elif "cvssMetricV30" in metrics:
            m = metrics["cvssMetricV30"][0]
            score = m["cvssData"]["baseScore"]
            vector = m["cvssData"]["vectorString"]
            severity = m["cvssData"]["baseSeverity"]

        elif "cvssMetricV2" in metrics:
            m = metrics["cvssMetricV2"][0]
            score = m["cvssData"]["baseScore"]
            vector = m["cvssData"]["vectorString"]
            severity = cvss_to_severity(score)

        # --- Dates ---
        published = cve.get("published", "N/A")
        updated = cve.get("lastModified", "N/A")

        return {
            "id": cve_id,
            "description": description,
            "severity": severity,
            "score": score,
            "vector": vector,
            "published": published,
            "updated": updated,
        }

    except Exception:
        return empty_response(cve_id)


# ==========================================================
# Fallback helpers
# ==========================================================
def empty_response(cve_id):
    return {
        "id": cve_id,
        "description": "No description available.",
        "severity": "N/A",
        "score": "N/A",
        "vector": "N/A",
        "published": "N/A",
        "updated": "N/A",
    }


def cvss_to_severity(score):
    try:
        s = float(score)
        if s >= 9:
            return "Critical"
        elif s >= 7:
            return "High"
        elif s >= 4:
            return "Medium"
        else:
            return "Low"
    except:
        return "N/A"


# ==========================================================
# Rule-based AI Explanation (no API needed)
# ==========================================================
def generate_cve_explanation(details: dict) -> str:

    desc = details.get("description", "")
    severity = details.get("severity", "N/A")
    score = details.get("score", "N/A")
    vector = details.get("vector", "N/A")

    text = (
        f"Severity: {severity} (CVSS {score})\n"
        f"Attack Vector: {vector}\n"
        f"Description: {desc}\n\n"
    )

    # If description contains known patterns → classify it
    lower = desc.lower()

    if "remote code" in lower or "execute arbitrary code" in lower:
        text += (
            "• This is a Remote Code Execution (RCE) vulnerability.\n"
            "• Attackers can run malicious code on the target system.\n"
            "• Immediate patching is recommended.\n"
        )

    elif "bypass" in lower:
        text += (
            "• This is an authentication bypass vulnerability.\n"
            "• Attackers can access systems without credentials.\n"
            "• Enforce MFA and patch immediately.\n"
        )

    elif "overflow" in lower:
        text += (
            "• This is a buffer overflow vulnerability.\n"
            "• Attackers may crash or take control of the program.\n"
            "• Strongly recommended to update software.\n"
        )

    else:
        # Generic fallback
        text += (
            "• This vulnerability may impact system security.\n"
            "• Attackers could exploit it depending on context.\n"
            "• Apply patches and monitor logs.\n"
        )

    return text
