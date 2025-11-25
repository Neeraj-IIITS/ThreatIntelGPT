# src/store.py

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Database path
DB_PATH = Path(__file__).resolve().parent.parent / "threatintel.db"


def _get_conn():
    """Create and return a SQLite connection."""
    return sqlite3.connect(str(DB_PATH))


def init_db():
    """Initialize the database and create the table if not exists."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            published TEXT,
            raw_text TEXT,
            summary TEXT,
            iocs_json TEXT,
            entities_json TEXT,
            mitre_json TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def save_report(report: Dict[str, Any]) -> int:
    """Save a processed CTI report into the database."""
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO reports (
            title, link, published, raw_text, summary,
            iocs_json, entities_json, mitre_json, created_at
        )
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            report.get("title"),
            report.get("link"),
            report.get("published", ""),
            report.get("raw_text", ""),
            report.get("summary", ""),
            json.dumps(report.get("iocs", {})),
            json.dumps(report.get("entities", {})),
            json.dumps(report.get("mitre", {})),
            now,
        ),
    )

    conn.commit()
    report_id = cur.lastrowid
    conn.close()

    return report_id


def list_reports(limit: int = 200) -> List[Dict[str, Any]]:
    """Return list of saved reports (summary view)."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, link, published, summary, mitre_json, created_at
        FROM reports
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append(
            {
                "id": row[0],
                "title": row[1],
                "link": row[2],
                "published": row[3],
                "summary": row[4],
                "mitre": json.loads(row[5]) if row[5] else {},
                "created_at": row[6],
            }
        )

    return result


def get_report(report_id: int) -> Optional[Dict[str, Any]]:
    """Return full report by ID."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, link, published, raw_text, summary,
               iocs_json, entities_json, mitre_json, created_at
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "link": row[2],
        "published": row[3],
        "raw_text": row[4],
        "summary": row[5],
        "iocs": json.loads(row[6]),
        "entities": json.loads(row[7]),
        "mitre": json.loads(row[8]),
        "created_at": row[9],
    }


# --------------------------------------------------------------------
# ⭐⭐⭐ API-COMPATIBLE ALIASES (Fixes your FastAPI import error)
# --------------------------------------------------------------------

def get_all_reports() -> List[Dict[str, Any]]:
    """Alias for list_reports(), used by API."""
    return list_reports()

def get_report_by_id(rid: int) -> Optional[Dict[str, Any]]:
    """Alias for get_report(), used by API."""
    return get_report(rid)


# Initialize DB when module is imported
init_db()
