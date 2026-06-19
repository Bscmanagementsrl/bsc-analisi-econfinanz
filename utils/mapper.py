"""
utils/mapper.py â€” Mapping AI-assistito con Claude API
"""
import json
import os
from schema import (
    DEFAULT_MAPPING_HINTS, SECTION_OPTIONS, CATEGORY_LABEL_MAP,
    CE_VA_CATEGORIES, CE_CV_CATEGORIES, SP_FIN_ATTIVO, SP_FIN_PASSIVO, SP_FUN_CATEGORIES
)


def suggest_mapping_heuristic(raw_description: str) -> tuple[str, str]:
    """
    Suggerisce (mapped_category, section) basandosi su keyword matching.
    Ritorna ("escludi","DA ESCLUDERE") se nessun match.
    """
    desc_lower = raw_description.lower()
    best_match = None
    best_len = 0

    for pattern, category in DEFAULT_MAPPING_HINTS.items():
        if pattern in desc_lower and len(pattern) > best_len:
            best_match = category
            best_len = len(pattern)

    if best_match:
        section = _category_to_section(best_match)
        return best_match, section

    return "escludi", "DA ESCLUDERE"


def _category_to_section(cat_code: str) -> str:
    for c in CE_VA_CATEGORIES:
        if c[0] == cat_code:
            return "CE_VA"
    for c in CE_CV_CATEGORIES:
        if c[0] == cat_code:
            return "CE_CV"
    for c in SP_FIN_ATTIVO:
        if c[0] == cat_code:
            return "SP_FIN"
    for c in SP_FIN_PASSIVO:
        if c[0] == cat_code:
            return "SP_FIN"
    for c in SP_FUN_CATEGORIES:
        if c[0] == cat_code:
            return "SP_FUN"
    return "DA ESCLUDERE"


def suggest_mapping_ai(raw_description: str, raw_value: float,
                        raw_code: str = "", section_hint: str = "") -> dict:
    """
    Usa Claude API per suggerire il mapping.
    Richiede ANTHROPIC_API_KEY nelle secrets di Streamlit.
    Ritorna {"category": str, "section": str, "confidence": float, "reasoning": str}
    """
    try:
        import anthropic
        api_key = _get_api_key()
        if not api_key:
            # Fallback euristico
            cat, sec = suggest_mapping_heuristic(raw_description)
            return {"category": cat, "section": sec, "confidence": 0.6, "reasoning": "Euristica keyword"}

        client = anthropic.Anthropic(api_key=api_key)

        categories_text = _build_categories_prompt()

        prompt = f"""Sei un esperto di analisi finanziaria italiana (commercialista).
Devi classificare la seguente voce di bilancio nella categoria corretta di riclassificazione.

VOCE DA CLASSIFICARE:
- Codice conto: {raw_code or 'N/D'}
- Descrizione: {raw_description}
- Valore: {raw_value:,.2f} â‚¬
- Sezione (hint dal file): {section_hint or 'N/D'}

CATEGORIE DISPONIBILI:
{categories_text}

Rispondi SOLO con un JSON valido:
{{
  "category": "<codice_categoria>",
  "section": "<CE_VA|CE_CV|SP_FIN|SP_FUN|DA_ESCLUDERE>",
  "confidence": <0.0-1.0>,
  "reasoning": "<spiegazione breve in italiano>"
}}

Se la voce Ã¨ un totale/subtotale (es. "Totale attivo", "Totale ricavi"), usa "escludi" come category e "DA ESCLUDERE" come section.
"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        # Estrae JSON dalla risposta
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response_text[start:end])
            return result

    except Exception as e:
        pass  # Fallback silenzioso all'euristica

    cat, sec = suggest_mapping_heuristic(raw_description)
    return {"category": cat, "section": sec, "confidence": 0.5, "reasoning": "Fallback euristico"}


def _get_api_key() -> str:
    """Legge la chiave API dalle secrets di Streamlit o da variabile d'ambiente."""
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")


def _build_categories_prompt() -> str:
    lines = []
    lines.append("=== CE A VALORE AGGIUNTO (section: CE_VA) ===")
    for code, label, _, _ in CE_VA_CATEGORIES:
        lines.append(f"  {code}: {label}")
    lines.append("\n=== CE A COSTO DEL VENDUTO (section: CE_CV) ===")
    for code, label, _, _ in CE_CV_CATEGORIES:
        lines.append(f"  {code}: {label}")
    lines.append("\n=== SP FIMANY2AT¢Ï, ATTIX¯ (section: SP_FIN) ===")
    for code, label, _, _ in SP_FIN_ATTIVO:
        lines.append(f"  {code}: {label}")
    lines.append("\n=== SP FINANZIARIO PASSIVO (section: SP_FIN) ===")
    for code, label, _, _ in SP_FIN_PASSIVO:
        lines.append(f"  {code}: {label}")
    lines.append("\n=== SP FUNZIONALE (section: SP_FUN) ===")
    for code, label, _, _ in SP_FUN_CATEGORIES:
        lines.append(f"  {code}: {label}")
    return "\n".join(lines)


def auto_map_lines(lines: list[dict], client_id: int,
                   use_ai: bool = True) -> list[dict]:
    """
    Data una lista di voci grezze, propone il mapping per ciascuna.
    Prima cerca nel DB del cliente, poi usa euristica/AI.
    Ritorna lista arricchita con chiavi "suggested_category", "suggested_section", "confidence".
    """
    from utils.db import get_mapping

    result = []
    for line in lines:
        desc = line["raw_description"]
        # 1. Cerca nel mapping storico del cliente
        saved = get_mapping(client_id, desc)
        if saved:
            line["suggested_category"] = saved["mapped_category"]
            line["suggested_section"] = saved["mapped_section"]
            line["confidence"] = saved["confidence"]
            line["source"] = "storico"
        elif use_ai:
            # 2. AI mapping
            sugg = suggest_mapping_ai(
                desc, line["raw_value"],
                line.get("raw_code", ""), line.get("section_hint", "")
            )
            line["suggested_category"] = sugg["category"]
            line["suggested_section"] = sugg["section"]
            line["confidence"] = sugg["confidence"]
            line["source"] = "AI"
        else:
            # 3. Solo euristica
            cat, sec = suggest_mapping_heuristic(desc)
            line["suggested_category"] = cat
            line["suggested_section"] = sec
            line["confidence"] = 0.6
            line["source"] = "euristica"

        result.append(line)

    return result
