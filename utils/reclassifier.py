"""
utils/reclassifier.py — Motore di riclassificazione CE e SP
"""
from schema import (
    CE_VA_CATEGORIES, CE_VA_SUBTOTALS,
    CE_CV_CATEGORIES, CE_CV_SUBTOTALS,
    SP_FIN_ATTIVO, SP_FIN_PASSIVO,
    SP_FIN_SUBTOTALS_ATTIVO, SP_FIN_SUBTOTALS_PASSIVO,
    SP_FUN_CATEGORIES, SP_FUN_SUBTOTALS,
)


def _build_values(categories: list, mapping: dict[str, float]) -> dict[str, float]:
    """Costruisce dict codice→valore sommando tutte le righe mappate su quella categoria."""
    result = {}
    for cat_code, *_ in categories:
        result[cat_code] = mapping.get(cat_code, 0.0)
    return result


def _compute_subtotal(cat_values: dict, items: list | None, all_vals: dict) -> float:
    if items is None:
        # Somma di tutti i valori (risultato netto)
        return sum(v * s for (c, _, s, _) in _schema_for(cat_values) for v in [cat_values.get(c, 0)])
    return sum(cat_values.get(c, 0.0) for c in items)


def _schema_for(cat_values: dict):
    # Restituisce schema CE_VA se le chiavi corrispondono, altrimenti CE_CV
    keys = set(cat_values.keys())
    ce_va_keys = {c[0] for c in CE_VA_CATEGORIES}
    if keys & ce_va_keys:
        return CE_VA_CATEGORIES
    return CE_CV_CATEGORIES


def _signed_val(cat_code: str, raw_val: float, schema: list) -> float:
    """Applica il segno contabile (costi negativi nel conto economico)."""
    for code, label, sign, _ in schema:
        if code == cat_code:
            return raw_val * sign  # sign = +1 ricavi, -1 costi
    return raw_val


# ─────────────────────────────────────────────────────────────────────────────
#  Aggregazione mapping → valori per categoria
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_by_category(lines: list[dict], adjustments: list[dict]) -> dict[str, float]:
    """
    Prende le righe grezze (con "mapped_category" confermato) e gli aggiustamenti,
    restituisce dict {categoria: valore_totale}.
    """
    totals = {}

    for line in lines:
        cat = line.get("mapped_category") or line.get("suggested_category", "escludi")
        if cat == "escludi":
            continue
        val = float(line.get("raw_value", 0))
        totals[cat] = totals.get(cat, 0.0) + val

    for adj in adjustments:
        cat = adj.get("category", "escludi")
        if cat == "escludi":
            continue
        val = float(adj.get("value", 0))
        totals[cat] = totals.get(cat, 0.0) + val

    return totals


# ─────────────────────────────────────────────────────────────────────────────
#  RICLASSIFICAZIONE CE A VALORE AGGIUNTO
# ─────────────────────────────────────────────────────────────────────────────

def compute_ce_va(cat_values: dict[str, float]) -> list[dict]:
    """
    Restituisce lista di righe per la visualizzazione CE a Valore Aggiunto.
    Ogni riga: {"label": str, "value": float, "type": "item"|"subtotal"|"total", "level": int}
    """
    rows = []
    running = 0.0
    subtotal_labels = {sub: items for sub, items in CE_VA_SUBTOTALS.items()}

    # Costruiamo dict running per ogni categoria
    cumulative = {}
    for cat_code, label, sign, subtotal_after in CE_VA_CATEGORIES:
        raw = cat_values.get(cat_code, 0.0)
        contrib = raw * sign  # contributo al subtotale (valore già con segno)
        cumulative[cat_code] = contrib

        rows.append({
            "label": label,
            "value": raw,
            "contrib": contrib,
            "type": "item",
            "level": 1,
            "code": cat_code,
        })

        if subtotal_after:
            # Calcola subtotale
            items = CE_VA_SUBTOTALS.get(subtotal_after)
            if items is None:
                # "RISULTATO NETTO" = somma di tutti
                sub_val = sum(cumulative.values())
            else:
                sub_val = sum(cumulative.get(c, 0.0) for c in items)

            rows.append({
                "label": subtotal_after,
                "value": sub_val,
                "contrib": sub_val,
                "type": "total" if "RISULTATO" in subtotal_after else "subtotal",
                "level": 0,
                "code": subtotal_after,
            })

    return rows


def compute_ce_cv(cat_values: dict[str, float]) -> list[dict]:
    """Riclassificazione CE a Costo del Venduto."""
    rows = []
    cumulative = {}

    for cat_code, label, sign, subtotal_after in CE_CV_CATEGORIES:
        raw = cat_values.get(cat_code, 0.0)
        contrib = raw * sign
        cumulative[cat_code] = contrib

        rows.append({
            "label": label,
            "value": raw,
            "contrib": contrib,
            "type": "item",
            "level": 1,
            "code": cat_code,
        })

        if subtotal_after:
            items = CE_CV_SUBTOTALS.get(subtotal_after)
            if items is None:
                sub_val = sum(cumulative.values())
            else:
                sub_val = sum(cumulative.get(c, 0.0) for c in items)

            rows.append({
                "label": subtotal_after,
                "value": sub_val,
                "contrib": sub_val,
                "type": "total" if "RISULTATO" in subtotal_after else "subtotal",
                "level": 0,
                "code": subtotal_after,
            })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  RICLASSIFICAZIONE SP FINANZIARIO
# ─────────────────────────────────────────────────────────────────────────────

def compute_sp_fin(cat_values: dict[str, float]) -> dict:
    """
    Restituisce {"attivo": [...righe...], "passivo": [...righe...]}
    """
    def _build_section(schema, subtotals):
        rows = []
        cumulative = {}
        for cat_code, label, sign, subtotal_after in schema:
            raw = cat_values.get(cat_code, 0.0)
            contrib = abs(raw)  # SP: tutti positivi per default
            cumulative[cat_code] = contrib

            rows.append({
                "label": label,
                "value": raw,
                "contrib": contrib,
                "type": "item",
                "level": 1,
                "code": cat_code,
            })

            if subtotal_after:
                items_list = subtotals.get(subtotal_after)
                if items_list is None:
                    sub_val = sum(cumulative.values())
                else:
                    sub_val = sum(cumulative.get(c, 0.0) for c in items_list)

                rows.append({
                    "label": subtotal_after,
                    "value": sub_val,
                    "contrib": sub_val,
                    "type": "subtotal",
                    "level": 0,
                    "code": subtotal_after,
                })

        # Totale finale
        total = sum(
            cumulative.get(c[0], 0.0)
            for c in schema
        )
        return rows, total

    att_rows, att_total = _build_section(SP_FIN_ATTIVO, SP_FIN_SUBTOTALS_ATTIVO)
    pass_rows, pass_total = _build_section(SP_FIN_PASSIVO, SP_FIN_SUBTOTALS_PASSIVO)

    att_rows.append({"label": "TOTALE ATTIVO", "value": att_total, "type": "total", "level": 0})
    pass_rows.append({"label": "TOTALE PASSIVO E PN", "value": pass_total, "type": "total", "level": 0})

    return {"attivo": att_rows, "passivo": pass_rows}


# ─────────────────────────────────────────────────────────────────────────────
#  RICLASSIFICAZIONE SP FUNZIONALE
# ─────────────────────────────────────────────────────────────────────────────

def compute_sp_fun(cat_values: dict[str, float]) -> list[dict]:
    """Riclassificazione SP funzionale (CIN = CCO + AF; CIN = PFN + PN)."""
    rows = []
    cumulative = {}

    for cat_code, label, sign, subtotal_after in SP_FUN_CATEGORIES:
        raw = cat_values.get(cat_code, 0.0)
        contrib = raw * sign
        cumulative[cat_code] = contrib

        rows.append({
            "label": label,
            "value": raw,
            "contrib": contrib,
            "type": "item",
            "level": 1,
            "code": cat_code,
        })

        if subtotal_after:
            items = SP_FUN_SUBTOTALS.get(subtotal_after)
            if subtotal_after == "CIN":
                # CCO + AF netto
                cco_cats = [c[0] for c in SP_FUN_CATEGORIES if c[3] == "CCO (Capitale Circolante Operativo)"]
                af_cats  = [c[0] for c in SP_FUN_CATEGORIES if c[3] == "ATTIVO FISSO NETTO"]
                sub_val  = sum(cumulative.get(c, 0.0) for c in cco_cats + af_cats)
            elif items is None:
                sub_val = sum(cumulative.values())
            else:
                sub_val = sum(cumulative.get(c, 0.0) for c in items)

            rows.append({
                "label": subtotal_after,
                "value": sub_val,
                "contrib": sub_val,
                "type": "total" if subtotal_after in ("CIN = PFN + PN",) else "subtotal",
                "level": 0,
                "code": subtotal_after,
            })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  Estrazione key values per indici
# ─────────────────────────────────────────────────────────────────────────────

def extract_kpis(cat_values: dict[str, float]) -> dict[str, float]:
    """
    Estrae i valori chiave necessari per il calcolo degli indici.
    """
    v = cat_values

    # CE
    ricavi = v.get("ricavi_netti", 0.0) or v.get("ricavi_netti_cv", 0.0)
    ebitda = sum(v.get(c, 0.0) * s for c, _, s, _ in CE_VA_CATEGORIES
                 if c in {"ricavi_netti","var_rim_pf","prod_cap_interna","altri_ricavi",
                           "acq_materie","var_rim_mp","costi_servizi","costi_godimento",
                           "oneri_diversi","costo_personale"})
    ebit   = ebitda - v.get("ammortamenti", 0.0) - v.get("accantonamenti", 0.0)
    risultato_netto = ebit + v.get("proventi_fin",0) - v.get("oneri_fin",0) \
                       + v.get("proventi_straord",0) - v.get("oneri_straord",0) - v.get("imposte",0)

    # SP Attivo
    liq_imm   = v.get("cassa_banche", 0.0) + v.get("titoli_bt", 0.0)
    rimanenze  = v.get("rimanenze", 0.0)
    crediti_c  = v.get("crediti_comm_bt", 0.0)
    ac         = liq_imm + v.get("altri_crediti_bt",0) + v.get("ratei_att",0) + rimanenze + crediti_c
    af         = (v.get("imm_immateriali",0) + v.get("imm_materiali",0)
                  + v.get("imm_finanziarie",0) + v.get("crediti_mlt",0) + v.get("altre_att_mlt",0))
    tot_attivo = ac + af

    # SP Passivo
    pc_fin     = v.get("deb_bancari_bt",0) + v.get("quota_corr_mlt",0)
    pc         = pc_fin + v.get("deb_commerciali",0) + v.get("deb_tributari",0) \
                 + v.get("altri_deb_corr",0) + v.get("ratei_pass",0)
    pml_fin    = v.get("deb_bancari_mlt",0) + v.get("altri_deb_fin_mlt",0)
    pml        = pml_fin + v.get("fondo_tfr",0) + v.get("fondi_rischi",0) + v.get("altre_pass_mlt",0)
    pn         = (v.get("capitale_sociale",0) + v.get("riserve",0)
                  + v.get("utile_portato",0) + v.get("utile_esercizio",0))

    # SP Funzionale
    cco        = (v.get("crediti_comm_f",0) + v.get("rimanenze_f",0) + v.get("altri_cc_att",0)
                  - v.get("deb_comm_f",0) - v.get("deb_trib_f",0) - v.get("altri_cc_pass",0))
    af_fun     = v.get("imm_mat_net",0) + v.get("imm_immat_net",0) + v.get("altre_att_fisse",0)
    cin        = cco + af_fun
    pfn        = v.get("deb_fin_bt_f",0) + v.get("deb_fin_mlt_f",0) - v.get("liquidita_fin",0)
    pn_fun     = v.get("pn_fun", pn)  # usa pn_fun se disponibile, altrimenti pn calcolato

    # Fornitori (per giorni)
    deb_comm   = v.get("deb_commerciali", 0.0)
    costi_acq  = abs(v.get("acq_materie",0)) + abs(v.get("costi_servizi",0))

    return {
        "RICAVI": ricavi,
        "EBITDA": ebitda,
        "EBIT": ebit,
        "RISULTATO_NETTO": risultato_netto,
        "LIQ_IMM": liq_imm,
        "RIMANENZE": rimanenze,
        "CREDITI_COMM": crediti_c,
        "AC": ac,
        "AF": af,
        "TOTALE_ATTIVO": tot_attivo,
        "PC": pc,
        "PC_fin": pc_fin,
        "PML": pml,
        "PML_fin": pml_fin,
        "TOTALE_PASSIVO_PN": pc + pml + pn,
        "PN": pn,
        "CCO": cco,
        "AF_FUN": af_fun,
        "CIN": cin if cin != 0 else 0.001,
        "PFN": pfn,
        "DEB_COMM": deb_comm,
        "COSTI_ACQ": costi_acq,
    }
