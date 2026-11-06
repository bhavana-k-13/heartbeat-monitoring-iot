"""SQLite storage layer (the starter's local stand-in for MySQL/Firebase)."""
import sqlite3
import threading
from datetime import datetime
from . import config as C

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bpm INTEGER NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_id INTEGER NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    response_action TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (reading_id) REFERENCES readings(id)
);
"""


def _conn():
    conn = sqlite3.connect(C.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_reading(bpm, status, source, alert=None):
    """Insert a reading (and an alert if given) in one transaction."""
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "INSERT INTO readings (bpm, status, source, created_at) VALUES (?,?,?,?)",
                (bpm, status, source, _now()))
            rid = cur.lastrowid
            if alert:
                conn.execute(
                    "INSERT INTO alerts (reading_id, level, message, response_action, created_at)"
                    " VALUES (?,?,?,?,?)",
                    (rid, status, alert["message"], alert["response"], _now()))
            conn.commit()
            row = conn.execute("SELECT * FROM readings WHERE id=?", (rid,)).fetchone()
            return dict(row)
        finally:
            conn.close()


def _query(sql, args=(), one=False):
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(sql, args)
            rows = cur.fetchone() if one else cur.fetchall()
        finally:
            conn.close()
    return rows


def get_readings(limit=50):
    rows = _query("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in reversed(rows)]  # oldest -> newest (good for graphs)


def get_latest():
    r = _query("SELECT * FROM readings ORDER BY id DESC LIMIT 1", one=True)
    return dict(r) if r else None


def get_alerts(limit=20):
    rows = _query(
        "SELECT a.*, r.bpm FROM alerts a JOIN readings r ON r.id=a.reading_id "
        "ORDER BY a.id DESC LIMIT ?", (limit,))
    return [dict(r) for r in rows]


def get_stats():
    s = _query("SELECT COUNT(*) n, AVG(bpm) a, MIN(bpm) lo, MAX(bpm) hi FROM readings", one=True)
    counts = _query("SELECT status, COUNT(*) n FROM readings GROUP BY status")
    alerts = _query("SELECT COUNT(*) n FROM alerts", one=True)["n"]
    by = {"NORMAL": 0, "WARNING": 0, "CRITICAL": 0}
    for r in counts:
        by[r["status"]] = r["n"]
    return {"total": s["n"], "average_bpm": round(s["a"], 1) if s["a"] is not None else None,
            "min_bpm": s["lo"], "max_bpm": s["hi"], "by_status": by, "alerts": alerts}


def clear_all():
    with _lock:
        conn = _conn()
        try:
            conn.execute("DELETE FROM alerts")
            conn.execute("DELETE FROM readings")
            conn.commit()
        finally:
            conn.close()
