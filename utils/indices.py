"""
utils/indices.py — Calcolo indici finanziari
"""
from schema import INDICES_DEFINITION


def compute_indices(kpis: dict[str, float]) -> list[dict]:
    results = []
    def safe_div(a, b, default=None):
        if b is None or b == 0: return default
        return a / b
    k = kpis
    formulas = {
        "indip_finanziaria": safe_div(k.get("PN",0), k.get("TOTALE_PASSIVO_PN",0)),
        "copertura_imm_I": safe_div(k.get("PN",0), k.get("AF",0)),
        "copertura_imm_II": safe_div(k.get("PN",0) + k.get("PML",0), k.get("AF",0)),
        "leverage": safe_div(k.get("TOTALE_PASSIVO_PN",0), k.get("PN",0)),
        "debt_equity": safe_div(k.get("PC_fin",0) + k.get("PM_fin",0), k.get("PN",0)),
        "current_ratio": safe_div(k.get("AC",0), k.get("PC",0)),
        "quick_ratio": safe_div(k.get("AC",0) - k.get("RIMANENZE",0), k.get("PC",0)),
        "cash_ratio": safe_div(k.get("LIQ_IMM",0), k.get("PC",0)),
        "pfn_ebitda": safe_div(k.get("PFN",0), k.get("EBITDA",0)),
        "roe": safe_div(k.get("RISULTATO_NETTO",0), k.get("PN",0)),
        "roi": safe_div(k.get("EBIT",0), k.get("CIN",0)),
        "ros": safe_div(k.get("EBIT",0), k.get("RICAVI",0)),
        "ebitda_margin": safe_div(k.get("EBITDA",0), k.get("RICAVI",0)),
        "roa": safe_div(k.get("EBIT",0), k.get("TOTALE_ATTIVO",0)),
        "gg_crediti": safe_div(k.get("CREDITI_COMM",0), k.get("RICAVI",0),0)*365 if k.get("RICAVI",0) else None,
        "gg_fornitori": safe_div(k.get("DEB_COMM",0), k.get("COSTI_ACQ",0),0)*365 if k.get("COSTI_ACQ",0) else None,
        "gg_magazzino": safe_div(k.get("RIMANENZE",0), k.get("COSTI_ACQ",0),0)*365 if k.get("COSTI_ACQ",0) else None,
    }
    for idx_code, defn in INDICES_DEFINITION.items():
        value = formulas.get(idx_code)
        if value is None: continue
        status = _compute_status(idx_code, value, defn)
        formatted = _format_value(value, defn["format"])
        results.append({"code":idx_code,"label":defn["label"],"group":defn["group"],"value":value,"formatted":formatted,"status":status})
    return results

def _compute_status(idx_code, value, defn):
    gi = defn.get("good_if","context")
    if gi=="context": return "info"
    if gi=="high":
        if defn.get("warn_below") and value<defn["warn_below"]: return "red"
        if defn.get("ok_above") and value>=defn["ok_above"]: return "green"
        return "yellow"
    if gi=="low':
        if defn.get("warn_above") and value>defn["warn_above"]: return "red"
        if defn.get("ok_below") and value<=defn["ok_below"]: return "green"
        return "yellow"
    return "info"

def _format_value(value, fmt):
    if value is None: return "N/D"
    if fmt=="pct": return f"{value*100:.1f}%"
    if fmt=="ratio": return f"{value:.2f}x"
    if fmt=="days": return f"{value:.0f} gg"
    return f"{value:.2f}"
