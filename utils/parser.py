"""
utils/parser.py — Estrazione voci grezze da Excel (e PDF fallback)
"""
import pandas as pd
import re
from io import BytesIO
from typing import Optional


def _is_numeric(val) -> bool:
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str):
        val = val.replace(".", "").replace(",", ".").replace(" ", "").replace("(", "-").replace(")", "")
        try:
            float(val)
            return True
        except ValueError:
            return False
    return False


def _to_float(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        # gestisce parentesi per negativi, es. (1.234,56)
        negative = val.startswith("(") and val.endswith(")")
        val = val.replace("(", "").replace(")", "")
        # rimuove punti migliaia se ci sono virgole decimali
        if "," in val:
            val = val.replace(".", "").replace(",", ".")
        else:
            val = val.replace(",", "")
        try:
            n = float(val)
            return -n if negative else n
        except ValueError:
            return None
    return None


def parse_excel(file_bytes: bytes, sheet_name=None) -> list[dict]:
    """
    Legge un file Excel (output grezzo del gestionale del cliente)
    e restituisce una lista di dict:
        {"raw_code": str, "raw_description": str, "raw_value": float, "section_hint": str}

    Strategia adattiva:
    1. Cerca il foglio più rilevante (CE, SP, Bilancio, ecc.)
    2. Identifica le colonne: codice, descrizione, valore
    3. Filtra le righe con un valore numerico significativo
    """
    buf = BytesIO(file_bytes)

    # Carica tutti i fogli
    try:
        xl = pd.ExcelFile(buf)
    except Exception as e:
        raise ValueError(f"Impossibile leggere il file Excel: {e}")

    sheet_names = xl.sheet_names

    # Cerca il foglio migliore
    target_sheet = sheet_name or _find_best_sheet(sheet_names)

    # Legge senza header per analisi flessibile
    df_raw = xl.parse(target_sheet, header=None, dtype=str)
    df_raw = df_raw.fillna("")

    lines = _extract_lines_from_df(df_raw)

    if not lines:
        # Fallback: prova tutti i fogli
        for sh in sheet_names:
            if sh == target_sheet:
                continue
            df_raw = xl.parse(sh, header=None, dtype=str).fillna("")
            lines = _extract_lines_from_df(df_raw)
            if lines:
                break

    return lines


def _find_best_sheet(sheet_names: list[str]) -> str:
    priority_keywords = [
        "bilancio", "conto economico", "stato patrimoniale",
        "ce", "sp", "risultati", "report"
    ]
    for sh in sheet_names:
        sh_lower = sh.lower()
        for kw in priority_keywords:
            if kw in sh_lower:
                return sh
    return sheet_names[0]


def _extract_lines_from_df(df: pd.DataFrame) -> list[dict]:
    lines = []
    n_cols = df.shape[1]
    if n_cols < 2:
        return lines

    # Identifica colonne: heuristic su quante celle numeriche ci sono
    numeric_counts = []
    for col_idx in range(n_cols):
        col = df.iloc[:, col_idx]
        count = sum(1 for v in col if _is_numeric(v) and v != "")
        numeric_counts.append((col_idx, count))

    # Colonna valore = quella con più numeri (esclusa la prima se ha <3 numeri)
    numeric_counts_sorted = sorted(numeric_counts, key=lambda x: -x[1])

    # Candidate value columns (le prime 2 per numero di valori numerici)
    value_cols = [c[0] for c in numeric_counts_sorted[:2] if c[1] > 2]
    if not value_cols:
        return lines

    primary_value_col = value_cols[0]

    # Colonna descrizione: quella di testo più vicina a sinistra della value_col
    desc_col = None
    for col_idx in range(primary_value_col - 1, -1, -1):
        col = df.iloc[:, col_idx]
        text_count = sum(1 for v in col if isinstance(v, str) and len(v.strip()) > 2 and not _is_numeric(v))
        if text_count > 3:
            desc_col = col_idx
            break

    if desc_col is None:
        # Usa la colonna 0 come descrizione
        desc_col = 0

    # Colonna codice: eventuale colonna tra 0 e desc_col che sembra codici
    code_col = None
    if desc_col > 0:
        for col_idx in range(desc_col):
            col = df.iloc[:, col_idx]
            # pattern codice: breve stringa alfanumerica (es. "4110", "B.II.3")
            code_like = sum(
                1 for v in col
                if isinstance(v, str) and re.match(r'^[A-Z0-9\.\/\-]{1,15}$', v.strip())
            )
            if code_like > 3:
                code_col = col_idx
                break

    section_hint = ""
    current_section = ""

    for row_idx in range(df.shape[0]):
        desc_val = str(df.iloc[row_idx, desc_col]).strip()
        num_val_raw = str(df.iloc[row_idx, primary_value_col]).strip()
        code_val = str(df.iloc[row_idx, code_col]).strip() if code_col is not None else ""

        # Skip righe vuote o intestazioni senza valore
        if not desc_val or desc_val in ("", "nan"):
            continue

        # Aggiorna sezione corrente (CE / SP)
        desc_up = desc_val.upper()
        if any(kw in desc_up for kw in ["CONTO ECONOMICO", "STATO PATRIMONIALE"]):
            current_section = "CE" if "CONTO" in desc_up else "SP"
            continue

        num_val = _to_float(num_val_raw)
        if num_val is None:
            # Se non c'è valore, potrebbe essere un'intestazione di sezione
            continue

        # Salta righe con valore = 0 e descrizione generica (totali vuoti)
        if num_val == 0 and len(desc_val) < 5:
            continue

        lines.append({
            "raw_code": code_val,
            "raw_description": desc_val,
            "raw_value": num_val,
            "section_hint": current_section,
        })

    return lines


def get_sheet_names(file_bytes: bytes) -> list[str]:
    buf = BytesIO(file_bytes)
    xl = pd.ExcelFile(buf)
    return xl.sheet_names


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """
    Fallback per PDF — usa pdfplumber.
    Restituisce stessa struttura di parse_excel.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber non installato. Aggiungi 'pdfplumber' a requirements.txt")

    lines = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    # Cerca colonne con valori numerici
                    text_cells = [c for c in row if c and not _is_numeric(c)]
                    num_cells = [c for c in row if c and _is_numeric(c)]
                    if not text_cells or not num_cells:
                        continue
                    desc = text_cells[0].strip()
                    val = _to_float(num_cells[-1])
                    if desc and val is not None:
                        lines.append({
                            "raw_code": "",
                            "raw_description": desc,
                            "raw_value": val,
                            "section_hint": "",
                        })
    return lines
