# src/api.py

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

# ---- Internal modules ----
from .collector import fetch_rss_entries, fetch_page_text
from .extractors import extract_iocs, extract_entities
from .mitre_mapper import map_mitre
from .store import save_report, list_reports, get_report
from .cve_lookup import fetch_cve_details, generate_cve_explanation


# ==========================================================
# FastAPI initialization
# ==========================================================
app = FastAPI(title="ThreatIntelGPT API")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Serve frontend
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root():
    """Serve UI"""
    return FileResponse(STATIC_DIR / "index.html")


# ==========================================================
# Models
# ==========================================================
class IngestRequest(BaseModel):
    rss_url: str
    max_items: int = 5
    save: bool = True


class VoiceQuery(BaseModel):
    query: str


# ==========================================================
# INGEST RSS FEED
# ==========================================================
@app.post("/ingest")
def ingest_rss(request: IngestRequest):

    try:
        entries = fetch_rss_entries(request.rss_url, request.max_items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    processed_items = []

    for entry in entries:
        raw_text = entry.get("summary", "") or ""
        page_text = fetch_page_text(entry.get("link", ""))

        if len(raw_text) < 200 and page_text:
            raw_text += "\n" + page_text

        iocs = extract_iocs(raw_text)
        entities = extract_entities(raw_text)
        mitre = map_mitre(raw_text)
        summary = raw_text[:400] + "..."

        report_obj = {
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": entry.get("published"),
            "raw_text": raw_text,
            "summary": summary,
            "iocs": iocs,
            "entities": entities,
            "mitre": mitre
        }

        saved_id = save_report(report_obj) if request.save else None

        processed_items.append({
            "id": saved_id,
            **report_obj
        })

    return {"count": len(processed_items), "items": processed_items}


# ==========================================================
# GET ALL REPORTS
# ==========================================================
@app.get("/reports")
def get_reports():
    reports = list_reports()
    return {"count": len(reports), "items": reports}


# ==========================================================
# GET SINGLE REPORT
# ==========================================================
@app.get("/report/{report_id}")
def get_single_report(report_id: int):
    report = get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


# ==========================================================
# CVE ANALYZER
# ==========================================================
@app.get("/cve/{cve_id}")
def analyze_cve(cve_id: str):

    cve_id = cve_id.upper()
    details = fetch_cve_details(cve_id)
    ai_text = generate_cve_explanation(details)

    return {
        "cve_id": cve_id,
        "details": details,
        "ai_explanation": ai_text
    }


# ==========================================================
# VOICE ASSISTANT ENDPOINT (LEVEL 1)
# No ML, no API keys — simple intelligent rule-based NLP
# ==========================================================
@app.post("/voice_query")
def voice_query(data: VoiceQuery):

    text = data.query.strip()

    if not text:
        return {"response": "I could not understand what you said."}

    text_l = text.lower()

    # --- Rule-based mini AI ---
    if "cve" in text_l:
        return {
            "response": "To analyze a CVE, say the ID clearly. Example: 'Analyze CVE-2024-3094'."
        }

    if "ransomware" in text_l:
        return {
            "response": "Ransomware is a malware that encrypts files and demands payment. Common mitigations include offline backups, endpoint monitoring, and disabling RDP."
        }

    if "phishing" in text_l:
        return {
            "response": "Phishing attacks trick users into giving credentials. Mitigate using email filtering, MFA, and employee awareness training."
        }

    if "mitre" in text_l or "attack" in text_l:
        return {
            "response": "MITRE ATT&CK is a framework of attacker techniques and tactics used for threat intelligence and defense improvement."
        }

    if "ioc" in text_l or "indicator" in text_l:
        return {
            "response": "Indicators of Compromise (IOCs) include IPs, domains, hashes, and URLs that reveal malicious activity."
        }

    if "hello" in text_l or "hi" in text_l:
        return {"response": "Hello! How can I help with cybersecurity today?"}

    # Default fallback
    return {
        "response": (
            f"You said: '{text}'. "
            "I can answer cybersecurity questions, analyze CVEs, or explain threats."
        )
    }


# ==========================================================
# STARTUP
# ==========================================================
@app.on_event("startup")
def startup_event():
    print("ThreatIntelGPT API started successfully.")
