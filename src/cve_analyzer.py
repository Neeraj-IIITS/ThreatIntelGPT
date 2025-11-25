# src/cve_analyzer.py

import requests
from gpt4all import GPT4All
from .cve_analyzer import fetch_cve_details, explain_cve_ai


# Load Phi-2 model (ensure you have the model file: phi-2.gguf)
model = GPT4All("phi-2.Q4_K_M.gguf")  # You can change model name as needed

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cve/2.0/"

def fetch_cve_details(cve_id: str):
    """Fetch CVE details from NVD public API"""
    url = f"{NVD_BASE_URL}{cve_id}"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json()

    try:
        cve = data['vulnerabilities'][0]['cve']
        return {
            "id": cve_id,
            "description": cve['descriptions'][0]['value'],
            "severity": cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity'),
            "score": cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore'),
            "vector": cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('vectorString'),
            "published": cve.get('published'),
            "updated": cve.get('lastModified')
        }
    except:
        return None


def explain_cve_ai(cve_data):
    """AI-based explanation using Phi-2"""
    prompt = f"""
You are a cybersecurity expert. Explain this CVE in simple professional language.

CVE ID: {cve_data['id']}
Description: {cve_data['description']}
Severity: {cve_data['severity']}
CVSS Score: {cve_data['score']}
Vector: {cve_data['vector']}

Explain:
1. What is the vulnerability?
2. How dangerous is it?
3. What systems it impacts?
4. How it could be exploited?
5. Simple mitigation steps.

Make the explanation clear and short.
"""

    response = model.generate(prompt, max_tokens=350)
    return response

@app.get("/cve/{cve_id}")
async def analyze_cve(cve_id: str):
    details = fetch_cve_details(cve_id)
    if not details:
        raise HTTPException(status_code=404, detail="CVE not found")

    explanation = explain_cve_ai(details)

    return {
        "cve_id": cve_id,
        "details": details,
        "ai_explanation": explanation
    }
