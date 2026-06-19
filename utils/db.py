"""
utils/db.py — Database SQLite per BSC Analisi Eco-Fin
"""
import sqlite3
import hashlib
import os
from datetime import datetime

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "bsc.db")
DB_PATH = os.environ.get("BSC_DB_PATH", _DEFAULT_DB)


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Utenti (admin = commercialista, client = azienda cliente)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password_h  TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'client',  -- 'admin' o 'client'
            client_name TEXT,
            email       TEXT,
            active      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # Inserisce admin di default se non esiste
    admin_pw = _hash("bsc2024!")
    c.execute("""
        INSERT OR IGNORE INTO users (username, password_h, role, client_name, email)
        VALUES (?, ?, 'admin', 'Studio BSC', 'studiopietroforte@gmail.com')
    """, ("admin", admin_pw))

    # Invii da parte dei clienti
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER NOT NULL REFERENCES users(id),
            period      TEXT NOT NULL,   -- es. "2024-05" (anno-mese)
            submitted_at TEXT DEFAULT (datetime('now')),
            status      TEXT DEFAULT 'pending',  -- pending / in_progress / done
            notes       TEXT,
            filename    TEXT
        )
    """)

    # Righe grezze estratte dal file cliente
    c.execute("""
        CREATE TABLE IF NOT EXISTS submission_lines (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id   INTEGER NOT NULL REFERENCES submissions(id),
            raw_code        TEXT,
            raw_description TEXT,
            raw_value       REAL,
            section_hint    TEXT   -- 'CE' o 'SP' se ricavabile dal layout
        )
    """)

    # Aggiustamenti extracontabili
    c.execute("""
        CREATE TABLE IF NOT EXISTS adjustments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id   INTEGER NOT NULL REFERENCES submissions(id),
            description     TEXT,
            category        TEXT,   -- codice categoria schema
            value           REAL,
            notes           TEXT
        )
    """)

    # Mapping appreso per cliente (pattern → categoria)
    c.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER NOT NULL REFERENCES users(id),
            raw_description TEXT NOT NULL,
            mapped_category TEXT NOT NULL,
            mapped_section  TEXT NOT NULL,   -- CE_VA, CE_CV, SP_FIN, SP_FUN, ESCLUDI
            confidence      REAL DEFAULT 1.0,
            last_used       TEXT DEFAULT (datetime('now')),
            UNIQUE(client_id, raw_description)
        )
    """)

    # Risultati dell'analisi (JSON serializzato)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id   INTEGER UNIQUE REFERENCES submissions(id),
            result_json     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ─── Auth ──────────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def authenticate(username: str, password: str):
    """Restituisce Row utente o None."""
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_h=? AND active=1",
        (username, _hash(password))
    ).fetchone()
    conn.close()
    return user


def get_user(user_id: int):
    conn = get_conn()
    u = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return u


def list_clients():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM users WHERE role='client' ORDER BY client_name"
    ).fetchall()
    conn.close()
    return rows


def create_user(username, password, role, client_name, email):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username,password_h,role,client_name,email) VALUES (?,?,?,?,?)",
            (username, _hash(password), role, client_name, email)
        )
        conn.commit()
        return True, "Utente creato"
    except sqlite3.IntegrityError:
        return False, "Username gi à esistente"
    finally:
        conn.close()


def update_user_password(user_id, new_password):
    conn = get_conn()
    conn.execute("UPDATE users SET password_h=? WHERE id=?", (_hash(new_password), user_id))
    conn.commit()
    conn.close()


# ─── Submissions ─────────────────────────────────────────────────────────────

def create_submission(client_id, period, notes="", filename=""):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO submissions (client_id,period,notes,filename) VALUES (?,?,?,?)",
        (client_id, period, notes, filename)
    )
    sub_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sub_id


def get_submission(sub_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT s.*, u.client_name, u.email, u.username
        FROM submissions s JOIN users u ON s.client_id=u.id
        WHERE s.id=?
    """, (sub_id,)).fetchone()
    conn.close()
    return row


def list_submissions(client_id=None, status=None):
    conn = get_conn()
    q = """
        SELECT s.*, u.client_name, u.username
        FROM submissions s JOIN users u ON s.client_id=u.id
    """
    params = []
    where = []
    if client_id:
        where.append("s.client_id=?")
        params.append(client_id)
    if status:
        where.append("s.status=?")
        params.append(status)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY s.submitted_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def update_submission_status(sub_id, status):
    conn = get_conn()
    conn.execute("UPDATE submissions SET status=? WHERE id=?", (status, sub_id))
    conn.commit()
    conn.close()


# ─── Lines ───────────────────────────────────────────────────────────────────

def save_lines(sub_id, lines: list[dict]):
    """lines = [{"raw_code":"", "raw_description":"", "raw_value":0.0, "section_hint":""}]"""
    conn = get_conn()
    conn.execute("DELETE FROM submission_lines WHERE submission_id=?", (sub_id,))
    conn.executemany(
        "INSERT INTO submission_lines (submission_id,raw_code,raw_description,raw_value,section_hint) VALUES (?,?,?,?,?)",
        [(sub_id, l.get("raw_code",""), l["raw_description"], l["raw_value"], l.get("section_hint","")) for l in lines]
    )
    conn.commit()
    conn.close()


def get_lines(sub_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM submission_lines WHERE submission_id=? ORDER BY id",
        (sub_id,)
    ).fetchall()
    conn.close()
    return rows


# ─── Adjustments ─────────────────────────────────────────────────────────────

def save_adjustments(sub_id, adjustments: list[dict]):
    conn = get_conn()
    conn.execute("DELETE FROM adjustments WHERE submission_id=?", (sub_id,))
    conn.executemany(
        "INSERT INTO adjustments (submission_id,description,category,value,notes) VALUES (?,?,?,?,?)",
        [(sub_id, a["description"], a.get("category",""), a["value"], a.get("notes","")) for a in adjustments]
    )
    conn.commit()
    conn.close()


def get_adjustments(sub_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM adjustments WHERE submission_id=?", (sub_id,)
    ).fetchall()
    conn.close()
    return rows


# ─── Mappings ────────────────────────────────────────────────────────────────

def get_mapping(client_id, raw_description):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM mappings WHERE client_id=? AND raw_description=?",
        (client_id, raw_description)
    ).fetchone()
    conn.close()
    return row


def save_mapping(client_id, raw_description, mapped_category, mapped_section, confidence=1.0):
    conn = get_conn()
    conn.execute("""
        INSERT INTO mappings (client_id,raw_description,mapped_category,mapped_section,confidence,last_used)
        VALUES (?,?,?,?,?,datetime('now'))
        ON CONFLICT(client_id,raw_description) DO UPDATE SET
            mapped_category=excluded.mapped_category,
            mapped_section=excluded.mapped_section,
            confidence=excluded.confidence,
            last_used=datetime('now')
    """, (client_id, raw_description, mapped_category, mapped_section, confidence))
    conn.commit()
    conn.close()


def get_all_mappings(client_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM mappings WHERE client_id=? ORDER BY raw_description",
        (client_id,)
    ).fetchall()
    conn.close()
    return rows


# ─── Analysis Results ────────────────────────────────────────────────────────

def save_result(sub_id, result_json: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO analysis_results (submission_id, result_json)
        VALUES (?,?)
        ON CONFLICT(submission_id) DO UPDATE SET
            result_json=excluded.result_json,
            updated_at=datetime('now')
    """, (sub_id, result_json))
    conn.commit()
    conn.close()


def get_result(sub_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM analysis_results WHERE submission_id=?", (s