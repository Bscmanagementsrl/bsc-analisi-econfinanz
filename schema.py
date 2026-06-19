"""
schema.py — Struttura di riclassificazione BSC
Categorie CE (a Valore Aggiunto e a Costo del Venduto) e SP (Finanziario e Funzionale)
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CONTO ECONOMICO A VALORE AGGIUNTO
# ─────────────────────────────────────────────────────────────────────────────
CE_VA_CATEGORIES = [
    # (codice, label, segno, subtotal_after)
    # segno: +1 = voce positiva, -1 = voce negativa (costo)
    # subtotal_after: None oppure nome del subtotale che segue
    ("ricavi_netti",       "Ricavi netti di vendita e prestazioni",          +1, None),
    ("var_rim_pf",         "± Variazione rimanenze prodotti finiti/sem.",     +1, None),
    ("prod_cap_interna",   "+ Lavori interni capitalizzati",                  +1, None),
    ("altri_ricavi",       "+ Altri ricavi e proventi",                       +1, "VALORE DELLA PRODUZIONE"),
    ("acq_materie",        "- Acquisti materie prime e merci",                -1, None),
    ("var_rim_mp",         "± Variazione rimanenze materie prime",            +1, None),
    ("costi_servizi",      "- Costi per servizi",                             -1, None),
    ("costi_godimento",    "- Costi per godimento beni di terzi",             -1, None),
    ("oneri_diversi",      "- Oneri diversi di gestione",                     -1, "VALORE AGGIUNTO"),
    ("costo_personale",    "- Costi per il personale",                        -1, "EBITDA (MOL)"),
    ("ammortamenti",       "- Ammortamenti e svalutazioni",                   -1, None),
    ("accantonamenti",     "- Accantonamenti per rischi e oneri",             -1, "EBIT (Risultato Operativo)"),
    ("proventi_fin",       "+ Proventi finanziari",                           +1, None),
    ("oneri_fin",          "- Oneri finanziari",                              -1, None),
    ("proventi_straord",   "+ Proventi atipici/straordinari",                 +1, None),
    ("oneri_straord",      "- Oneri atipici/straordinari",                    -1, "EBT (Risultato ante imposte)"),
    ("imposte",            "- Imposte dell'esercizio",                        -1, "RISULTATO NETTO"),
]

CE_VA_SUBTOTALS = {
    "VALORE DELLA PRODUZIONE": ["ricavi_netti", "var_rim_pf", "prod_cap_interna", "altri_ricavi"],
    "VALORE AGGIUNTO":        ["ricavi_netti", "var_rim_pf", "prod_cap_interna", "altri_ricavi",
                                "acq_materie", "var_rim_mp", "costi_servizi", "costi_godimento", "oneri_diversi"],
    "EBITDA (MOL)":           ["ricavi_netti", "var_rim_pf", "prod_cap_interna", "altri_ricavi",
                                "acq_materie", "var_rim_mp", "costi_servizi", "costi_godimento", "oneri_diversi",
                                "costo_personale"],
    "EBIT (Risultato Operativo)": ["ricavi_netti", "var_rim_pf", "prod_cap_interna", "altri_ricavi",
                                    "acq_materie", "var_rim_mp", "costi_servizi", "costi_godimento", "oneri_diversi",
                                    "costo_personale", "ammortamenti", "accantonamenti"],
    "EBT (Risultato ante imposte)": ["ricavi_netti", "var_rim_pf", "prod_cap_interna", "altri_ricavi",
                                      "acq_materie", "var_rim_mp", "costi_servizi", "costi_godimento", "oneri_diversi",
                                      "costo_personale", "ammortamenti", "accantonamenti",
                                      "proventi_fin", "oneri_fin", "proventi_straord", "oneri_straord"],
    "RISULTATO NETTO":        None,  # tutti
}

# ─────────────────────────────────────────────────────────────────────────────
#  CONTO ECONOMICO A COSTO DEL VENDUTO
# ─────────────────────────────────────────────────────────────────────────────
CE_CV_CATEGORIES = [
    ("ricavi_netti_cv",    "Ricavi netti di vendita",                        +1, None),
    ("mat_dirette",        "- Materie prime e materiali diretti (consumi)",   -1, None),
    ("lav_diretto",        "- Lavoro diretto (MOD)",                         -1, None),
    ("overhead_prod",      "- Overhead di produzione",                        -1, None),
    ("amm_impianti",       "- Ammortamenti impianti produttivi",              -1, None),
    ("var_rim_cv",         "± Variazione rimanenze prodotti",                 +1, "MARGINE INDUSTRIALE"),
    ("costi_commerciali",  "- Costi commerciali e marketing",                 -1, None),
    ("costi_logistici",    "- Costi logistici e distribuzione",               -1, "MARGINE COMMERCIALE"),
    ("costi_amm_gen",      "- Costi generali e amministrativi",               -1, None),
    ("r_and_d",            "- Costi R&D e sviluppo",                         -1, "EBIT (CV)"),
    ("proventi_fin_cv",    "+ Proventi finanziari",                           +1, None),
    ("oneri_fin_cv",       "- Oneri finanziari",                              -1, "EBT (CV)"),
    ("imposte_cv",         "- Imposte dell'esercizio",                        -1, "RISULTATO NETTO (CV)"),
]

CE_CV_SUBTOTALS = {
    "MARGINE INDUSTRIALE": ["ricavi_netti_cv", "mat_dirette", "lav_diretto", "overhead_prod",
                             "amm_impianti", "var_rim_cv"],
    "MARGINE COMMERCIALE": ["ricavi_netti_cv", "mat_dirette", "lav_diretto", "overhead_prod",
                             "amm_impianti", "var_rim_cv", "costi_commerciali", "costi_logistici"],
    "EBIT (CV)":           ["ricavi_netti_cv", "mat_dirette", "lav_diretto", "overhead_prod",
                             "amm_impianti", "var_rim_cv", "costi_commerciali", "costi_logistici",
                             "costi_amm_gen", "r_and_d"],
    "EBT (CV)":            None,
    "RISULTATO NETTO (CV)": None,
}

# ─────────────────────────────────────────────────────────────────────────────
#  STATO PATRIMONIALE — SCHEMA FINANZIARIO
# ─────────────────────────────────────────────────────────────────────────────
SP_FIN_ATTIVO = [
    # ATTIVO CORRENTE
    ("cassa_banche",       "Cassa e disponibilità bancarie",                  +1, None),
    ("titoli_bt",          "Titoli e attività finanziarie correnti",           +1, None),
    ("crediti_comm_bt",    "Crediti commerciali (breve termine)",              +1, None),
    ("altri_crediti_bt",   "Altri crediti a breve termine",                   +1, None),
    ("ratei_att",          "Ratei e risconti attivi",                          +1, None),
    ("rimanenze",          "Rimanenze",                                        +1, "ATTIVO CORRENTE (AC)"),
    # ATTIVO FISSO
    ("imm_immateriali",    "Immobilizzazioni immateriali (nette)",             +1, None),
    ("imm_materiali",      "Immobilizzazioni materiali (nette)",               +1, None),
    ("imm_finanziarie",    "Immobilizzazioni finanziarie",                     +1, None),
    ("crediti_mlt",        "Crediti a lungo termine",                          +1, None),
    ("altre_att_mlt",      "Altre attività a lungo termine",                   +1, "ATTIVO FISSO (AF)"),
]

SP_FIN_PASSIVO = [
    # PASSIVO CORRENTE
    ("deb_bancari_bt",     "Debiti verso banche a breve",                     +1, None),
    ("quota_corr_mlt",     "Quota corrente debiti a M/L termine",              +1, None),
    ("deb_commerciali",    "Debiti commerciali (fornitori)",                   +1, None),
    ("deb_tributari",      "Debiti tributari e previdenziali",                 +1, None),
    ("altri_deb_corr",     "Altri debiti correnti",                            +1, None),
    ("ratei_pass",         "Ratei e risconti passivi",                         +1, "PASSIVO CORRENTE (PC)"),
    # PASSIVO CONSOLIDATO
    ("deb_bancari_mlt",    "Debiti verso banche a M/L termine",               +1, None),
    ("altri_deb_fin_mlt",  "Altri debiti finanziari a M/L termine",            +1, None),
    ("fondo_tfr",          "Fondo TFR",                                        +1, None),
    ("fondi_rischi",       "Fondi rischi e oneri a lungo",                     +1, None),
    ("altre_pass_mlt",     "Altre passività a lungo termine",                  +1, "PASSIVO CONSOLIDATO (PML)"),
    # PATRIMONIO NETTO
    ("capitale_sociale",   "Capitale sociale",                                 +1, None),
    ("riserve",            "Riserve (legale, statutaria, altre)",               +1, None),
    ("utile_portato",      "Utile/perdita portati a nuovo",                    +1, None),
    ("utile_esercizio",    "Utile/perdita d'esercizio",                        +1, "PATRIMONIO NETTO (PN)"),
]

SP_FIN_SUBTOTALS_ATTIVO = {
    "ATTIVO CORRENTE (AC)": ["cassa_banche", "titoli_bt", "crediti_comm_bt",
                              "altri_crediti_bt", "ratei_att", "rimanenze"],
    "ATTIVO FISSO (AF)":    ["imm_immateriali", "imm_materiali", "imm_finanziarie",
                              "crediti_mlt", "altre_att_mlt"],
    "TOTALE ATTIVO":        None,
}

SP_FIN_SUBTOTALS_PASSIVO = {
    "PASSIVO CORRENTE (PC)":      ["deb_bancari_bt", "quota_corr_mlt", "deb_commerciali",
                                    "deb_tributari", "altri_deb_corr", "ratei_pass"],
    "PASSIVO CONSOLIDATO (PML)":  ["deb_bancari_mlt", "altri_deb_fin_mlt", "fondo_tfr",
                                    "fondi_rischi", "altre_pass_mlt"],
    "PATRIMONIO NETTO (PN)":      ["capitale_sociale", "riserve", "utile_portato", "utile_esercizio"],
    "TOTALE PASSIVO E PN":        None,
}

# ─────────────────────────────────────────────────────────────────────────────
#  STATO PATRIMONIALE — SCHEMA FUNZIONALE
# ─────────────────────────────────────────────────────────────────────────────
SP_FUN_CATEGORIES = [
    # Capitale Circolante Operativo (CCO)
    ("crediti_comm_f",     "Crediti commerciali",                             +1, None),
    ("rimanenze_f",        "Rimanenze",                                        +1, None),
    ("altri_cc_att",       "Altre attività operative correnti",                +1, None),
    ("deb_comm_f",         "- Debiti commerciali (fornitori)",                 -1, None),
    ("deb_trib_f",         "- Debiti tributari e previdenziali",               -1, None),
    ("altri_cc_pass",      "- Altre passività operative correnti",             -1, "CCO (Capitale Circolante Operativo)"),
    # Attivo Fisso Netto Operativo
    ("imm_mat_net",        "Immobilizzazioni materiali nette",                 +1, None),
    ("imm_immat_net",      "Immobilizzazioni immateriali nette",               +1, None),
    ("altre_att_fisse",    "Altre attività fisse nette",                       +1, "ATTIVO FISSO NETTO"),
    # Totale CIN
    # -- subtotale CIN = CCO + AFNETTO
    # Fonti: PFN + PN
    ("deb_fin_bt_f",       "Debiti finanziari a breve (PFN)",                  +1, None),
    ("deb_fin_mlt_f",      "Debiti finanziari a M/L termine (PFN)",            +1, None),
    ("liquidita_fin",      "- Liquidità e titoli negoziabili",                 -1, "PFN (Posizione Finanziaria Netta)"),
    ("pn_fun",             "Patrimonio Netto",                                  +1, "CIN = PFN + PN"),
]

SP_FUN_SUBTOTALS = {
    "CCO (Capitale Circolante Operativo)": ["crediti_comm_f", "rimanenze_f", "altri_cc_att",
                                             "deb_comm_f", "deb_trib_f", "altri_cc_pass"],
    "ATTIVO FISSO NETTO": ["imm_mat_net", "imm_immat_net", "altre_att_fisse"],
    "CIN": None,  # CCO + AF netto
    "PFN (Posizione Finanziaria Netta)": ["deb_fin_bt_f", "deb_fin_mlt_f", "liquidita_fin"],
    "CIN = PFN + PN": None,
}

# ─────────────────────────────────────────────────────────────────────────────
#  INDICI FINANZIARI
# ─────────────────────────────────────────────────────────────────────────────
INDICES_DEFINITION = {
    # Solidità patrimoniale
    "indip_finanziaria":    {
        "label": "Indipendenza finanziaria (PN/Tot.Fonti)",
        "group": "Solidità",
        "formula": "PN / TOTALE_PASSIVO_PN",
        "good_if": "high",   # alto = buono
        "warn_below": 0.25,
        "ok_above": 0.40,
        "format": "pct",
    },
    "copertura_imm_I":      {
        "label": "Copertura immobilizzazioni I (PN/AF)",
        "group": "Solidità",
        "formula": "PN / ATTIVO_FISSO",
        "good_if": "high",
        "warn_below": 0.80,
        "ok_above": 1.00,
        "format": "ratio",
    },
    "copertura_imm_II":     {
        "label": "Copertura immobilizzazioni II ((PN+PML)/AF)",
        "group": "Solidità",
        "formula": "(PN + PML) / ATTIVO_FISSO",
        "good_if": "high",
        "warn_below": 1.00,
        "ok_above": 1.20,
        "format": "ratio",
    },
    "leverage":             {
        "label": "Leverage (Tot.Fonti/PN)",
        "group": "Solidità",
        "formula": "TOTALE_PASSIVO_PN / PN",
        "good_if": "low",
        "warn_above": 4.00,
        "ok_below": 2.50,
        "format": "ratio",
    },
    "debt_equity":          {
        "label": "Debt/Equity (Deb.Fin/PN)",
        "group": "Solidità",
        "formula": "(PC_fin + PML_fin) / PN",
        "good_if": "low",
        "warn_above": 2.00,
        "ok_below": 1.00,
        "format": "ratio",
    },
    # Liquidità
    "current_ratio":        {
        "label": "Current Ratio (AC/PC)",
        "group": "Liquidità",
        "formula": "AC / PC",
        "good_if": "high",
        "warn_below": 1.00,
        "ok_above": 1.50,
        "format": "ratio",
    },
    "quick_ratio":          {
        "label": "Quick Ratio ((AC-Rim)/PC)",
        "group": "Liquidità",
        "formula": "(AC - RIMANENZE) / PC",
        "good_if": "high",
        "warn_below": 0.70,
        "ok_above": 1.00,
        "format": "ratio",
    },
    "cash_ratio":           {
        "label": "Cash Ratio (Liq.Imm./PC)",
        "group": "Liquidità",
        "formula": "LIQ_IMM / PC",
        "good_if": "high",
        "warn_below": 0.10,
        "ok_above": 0.25,
        "format": "ratio",
    },
    "pfn_ebitda":           {
        "label": "PFN/EBITDA",
        "group": "Liquidità",
        "formula": "PFN / EBITDA",
        "good_if": "low",
        "warn_above": 5.00,
        "ok_below": 3.00,
        "format": "ratio",
    },
    # Redditività
    "roe":                  {
        "label": "ROE – Return on Equity (Rn/PN)",
        "group": "Redditività",
        "formula": "RISULTATO_NETTO / PN",
        "good_if": "high",
        "warn_below": 0.02,
        "ok_above": 0.08,
        "format": "pct",
    },
    "roi":                  {
        "label": "ROI – Return on Investment (EBIT/CIN)",
        "group": "Redditività",
        "formula": "EBIT / CIN",
        "good_if": "high",
        "warn_below": 0.03,
        "ok_above": 0.08,
        "format": "pct",
    },
    "ros":                  {
        "label": "ROS – Return on Sales (EBIT/Ricavi)",
        "group": "Redditività",
        "formula": "EBIT / RICAVI",
        "good_if": "high",
        "warn_below": 0.02,
        "ok_above": 0.06,
        "format": "pct",
    },
    "ebitda_margin":        {
        "label": "EBITDA Margin (EBITDA/Ricavi)",
        "group": "Redditività",
        "formula": "EBITDA / RICAVI",
        "good_if": "high",
        "warn_below": 0.05,
        "ok_above": 0.10,
        "format": "pct",
    },
    "roa":                  {
        "label": "ROA – Return on Assets (EBIT/Tot.Attivo)",
        "group": "Redditività",
        "formula": "EBIT / TOTALE_ATTIVO",
        "good_if": "high",
        "warn_below": 0.02,
        "ok_above": 0.06,
        "format": "pct",
    },
    # Efficienza operativa (opzionale, utili per commento)
    "gg_crediti":           {
        "label": "Giorni crediti clienti",
        "group": "Efficienza",
        "formula": "(CREDITI_COMM / RICAVI) * 365",
        "good_if": "low",
        "warn_above": 90,
        "ok_below": 60,
        "format": "days",
    },
    "gg_fornitori":         {
        "label": "Giorni debiti fornitori",
        "group": "Efficienza",
        "formula": "(DEB_COMM / (RICAVI - VA_ADDED)) * 365",
        "good_if": "context",
        "format": "days",
    },
    "gg_magazzino":         {
        "label": "Giorni di magazzino",
        "group": "Efficienza",
        "formula": "(RIMANENZE / (RICAVI - VA_ADDED)) * 365",
        "good_if": "low",
        "warn_above": 90,
        "ok_below": 45,
        "format": "days",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  MAPPATURE PREDEFINITE (suggerimenti AI)
#  pattern descrizione (lowercase) → categoria
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_MAPPING_HINTS = {
    # CE VA
    "ricavi": "ricavi_netti",
    "vendite": "ricavi_netti",
    "prestazioni": "ricavi_netti",
    "fatturato": "ricavi_netti",
    "contributi": "altri_ricavi",
    "plusvalenze": "altri_ricavi",
    "sopravvenienze attive": "altri_ricavi",
    "variazione rimanenze prodotti": "var_rim_pf",
    "variazione rimanenze materie": "var_rim_mp",
    "acquisti": "acq_materie",
    "materie prime": "acq_materie",
    "merci": "acq_materie",
    "servizi": "costi_servizi",
    "consulenze": "costi_servizi",
    "lavorazioni": "costi_servizi",
    "utenze": "costi_servizi",
    "manutenzioni": "costi_servizi",
    "godimento beni": "costi_godimento",
    "affitti": "costi_godimento",
    "leasing": "costi_godimento",
    "noleggio": "costi_godimento",
    "oneri diversi": "oneri_diversi",
    "personale": "costo_personale",
    "salari": "costo_personale",
    "stipendi": "costo_personale",
    "contributi previdenziali": "costo_personale",
    "tfr": "costo_personale",
    "ammortamenti": "ammortamenti",
    "svalutazioni": "ammortamenti",
    "accantonamenti": "accantonamenti",
    "interessi attivi": "proventi_fin",
    "proventi finanziari": "proventi_fin",
    "interessi passivi": "oneri_fin",
    "oneri finanziari": "oneri_fin",
    "mutui": "oneri_fin",
    "imposte": "imposte",
    "ires": "imposte",
    "irap": "imposte",
    # SP Finanziario — Attivo
    "cassa": "cassa_banche",
    "banche attivo": "cassa_banche",
    "c/c attivo": "cassa_banche",
    "crediti verso clienti": "crediti_comm_bt",
    "clienti": "crediti_comm_bt",
    "rimanenze": "rimanenze",
    "magazzino": "rimanenze",
    "ratei attivi": "ratei_att",
    "risconti attivi": "ratei_att",
    "immobilizzazioni immateriali": "imm_immateriali",
    "avviamento": "imm_immateriali",
    "brevetti": "imm_immateriali",
    "immobilizzazioni materiali": "imm_materiali",
    "terreni": "imm_materiali",
    "fabbricati": "imm_materiali",
    "macchinari": "imm_materiali",
    "attrezzature": "imm_materiali",
    "partecipazioni": "imm_finanziarie",
    # SP Finanziario — Passivo
    "banche passivo": "deb_bancari_bt",
    "fidi bancari": "deb_bancari_bt",
    "fornitori": "deb_commerciali",
    "debiti verso fornitori": "deb_commerciali",
    "debiti tributari": "deb_tributari",
    "debiti previdenziali": "deb_tributari",
    "erario": "deb_tributari",
    "ratei passivi": "ratei_pass",
    "risconti passivi": "ratei_pass",
    "mutui passivo": "deb_bancari_mlt",
    "leasing finanziario": "deb_bancari_mlt",
    "fondo tfr": "fondo_tfr",
    "trattamento di fine rapporto": "fondo_tfr",
    "fondo rischi": "fondi_rischi",
    "capitale sociale": "capitale_sociale",
    "riserve": "riserve",
    "riserva legale": "riserve",
    "utile": "utile_esercizio",
    "perdita": "utile_esercizio",
}

# Tutte le categorie in una lista flat (per form di mapping)
ALL_CE_VA_CODES = [c[0] for c in CE_VA_CATEGORIES]
ALL_CE_CV_CODES = [c[0] for c in CE_CV_CATEGORIES]
ALL_SP_FIN_ATT_CODES = [c[0] for c in SP_FIN_ATTIVO]
ALL_SP_FIN_PASS_CODES = [c[0] for c in SP_FIN_PASSIVO]
ALL_SP_FUN_CODES = [c[0] for c in SP_FUN_CATEGORIES]

CATEGORY_LABEL_MAP = {}
for c in CE_VA_CATEGORIES + CE_CV_CATEGORIES + SP_FIN_ATTIVO + SP_FIN_PASSIVO + SP_FUN_CATEGORIES:
    CATEGORY_LABEL_MAP[c[0]] = c[1]

SECTION_OPTIONS = {
    "CE Valore Aggiunto":    [(c[0], c[1]) for c in CE_VA_CATEGORIES],
    "CE Costo del Venduto":  [(c[0], c[1]) for c in CE_CV_CATEGORIES],
    "SP Fin — Attivo":       [(c[0], c[1]) for c in SP_FIN_ATTIVO],
    "SP Fin — Passivo":      [(c[0], c[1]) for c in SP_FIN_PASSIVO],
    "SP Funzionale":         [(c[0], c[1]) for c in SP_FUN_CATEGORIES],
    "DA ESCLUDERE":          [("escludi", "Voce da non includere nell'analisi")],
}
