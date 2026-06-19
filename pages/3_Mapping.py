"""
pages/3_Mapping.py — Admin: assegna ogni voce grezza alla categoria BSC
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import get_submission, get_lines, get_adjustments, save_mapping, get_all_mappings
from utils.mapper import suggest_mapping_heuristic, auto_map_lines
from schema import SECTION_OPTIONS, CATEGORY_LABEL_MAP
import pandas as pd

st.set_page_config(page_title="Mapping — BSC", page_icon="🗺️", layout="wide")

if st.session_state.get("role") != "admin":
    st.warning("Sezione riservata all'amministratore.")
    st.stop()


# Tutte le opzioni categorizzate
def all_options():
    opts = [("escludi", "— Escludi questa voce —")]
    for sec, cats in SECTION_OPTIONS.items():
        for code, label in cats:
            opts.append((code, f"[{sec[:8]}] {label}"))
    return opts


ALL_OPTS = all_options()
OPT_CODES  = [o[0] for o in ALL_OPTS]
OPT_LABELS = {o[0]: o[1] for o in ALL_OPTS}


def main():
    st.title("🗺️ Mapping Voci di Bilancio")
    st.caption("Assegna ogni voce alla categoria corretta. Il sistema apprende e riutilizza il mapping per questo cliente.")

    # Selezione submission
    sub_id = st.session_state.get("active_sub_id")
    if not sub_id:
        st.info("Seleziona un invio dalla pagina «Da Elaborare».")
        st.stop()

    sub = get_submission(sub_id)
    if not sub:
        st.error("Invio non trovato.")
        st.stop()

    st.markdown(f"**Cliente:** {sub['client_name']} | **Periodo:** {sub['period']} | **ID:** #{sub_id}")
    st.markdown("---")

    client_id = sub["client_id"]
    lines     = get_lines(sub_id)
    adjs      = get_adjustments(sub_id)

    if not lines:
        st.warning("Nessuna riga estratta per questo invio. Vai ad Analisi per inserire solo gli aggiustamenti.")
        if st.button("📊 Vai ad Analisi"):
            st.switch_page("pages/4_Analisi.py")
        st.stop()

    # Opzioni AI
    with st.expander("⚙️ Opzioni mapping"):
        use_ai = st.toggle("Suggerimenti AI (richiede chiave API Claude)", value=False)
        if use_ai:
            st.info("L'AI analizzerà ogni voce e suggerirà la categoria. Più lento ma più preciso.")

    st.markdown(f"**{len(lines)} voci da mappare**")

    # Carica mapping storici
    existing_mappings = {m["raw_description"]: (m["mapped_category"], m["mapped_section"])
                         for m in get_all_mappings(client_id)}

    # Inizializza stato per ogni voce
    if "mapping_state" not in st.session_state or st.session_state.get("mapping_sub_id") != sub_id:
        st.session_state["mapping_sub_id"] = sub_id
        mapping_state = {}
        for line in lines:
            desc = line["raw_description"]
            if desc in existing_mappings:
                cat, sec = existing_mappings[desc]
            else:
                cat, sec = suggest_mapping_heuristic(desc)
            mapping_state[desc] = cat
        st.session_state["mapping_state"] = mapping_state

    mapping_state = st.session_state["mapping_state"]

    # Tabella di mapping
    st.markdown("### 📋 Assegna le categorie")
    st.caption("Seleziona la categoria per ogni voce. Le voci già mappate in precedenza sono pre-compilate.")

    # Filtro per sezione
    filter_col1, filter_col2 = st.columns([2, 2])
    with filter_col1:
        section_filter = st.selectbox(
            "Filtra per sezione suggerita",
            ["Tutte"] + list(SECTION_OPTIONS.keys()) + ["DA ESCLUDERE"]
        )
    with filter_col2:
        only_unmapped = st.checkbox("Mostra solo voci non ancora mappate")

    # Header tabella
    header_cols = st.columns([0.5, 3, 2, 2.5, 1])
    header_cols[0].markdown("**#**")
    header_cols[1].markdown("**Descrizione voce**")
    header_cols[2].markdown("**Valore (€)**")
    header_cols[3].markdown("**Categoria assegnata**")
    header_cols[4].markdown("**Storico**")

    st.markdown("---")

    for i, line in enumerate(lines):
        desc  = line["raw_description"]
        val   = line["raw_value"]
        code  = line["raw_code"]
        cur_cat = mapping_state.get(desc, "escludi")
        is_stored = desc in existing_mappings

        # Filtri
        if only_unmapped and is_stored:
            continue

        cols = st.columns([0.5, 3, 2, 2.5, 1])
        cols[0].write(f"{i+1}")

        label_text = f"**{desc}**"
        if code:
            label_text += f" `{code}`"
        cols[1].markdown(label_text)
        cols[2].write(f"{val:,.2f}")

        cur_idx = OPT_CODES.index(cur_cat) if cur_cat in OPT_CODES else 0
        new_cat = cols[3].selectbox(
            f"cat_{i}",
            options=OPT_CODES,
            format_func=lambda x: OPT_LABELS.get(x, x),
            index=cur_idx,
            label_visibility="collapsed",
            key=f"mapping_{i}_{desc[:20]}"
        )
        mapping_state[desc] = new_cat

        # Indicatore se è già in storico
        if is_stored:
            cols[4].markdown("✅ storico")
        else:
            cols[4].markdown("🆕 nuovo")

    st.session_state["mapping_state"] = mapping_state

    # Riepilogo
    st.markdown("---")
    col_summary, col_actions = st.columns([2, 1])

    with col_summary:
        st.markdown("### 📊 Riepilogo mapping")
        from collections import Counter
        sections_count = Counter()
        for desc, cat in mapping_state.items():
            if cat == "escludi":
                sections_count["ESCLUSE"] += 1
            else:
                # Trova la sezione
                found = False
                for sec, cats in SECTION_OPTIONS.items():
                    for code, label in cats:
                        if code == cat:
                            sections_count[sec[:15]] += 1
                            found = True
                            break
                    if found:
                        break
                if not found:
                    sections_count["ALTRO"] += 1

        for sec, cnt in sections_count.most_common():
            st.write(f"- {sec}: **{cnt} voci**")

        unmapped_count = sum(1 for cat in mapping_state.values() if cat == "escludi")
        if unmapped_count > 0:
            st.warning(f"⚠️ {unmapped_count} voci impostate su «Escludi» — verifica che non siano importanti.")

    with col_actions:
        st.markdown("### 💾 Azioni")

        if st.button("💾 Salva mapping", type="primary", use_container_width=True):
            saved = 0
            for desc, cat in mapping_state.items():
                # Determina sezione
                section = "DA_ESCLUDERE"
                if cat != "escludi":
                    for sec_name, cats in SECTION_OPTIONS.items():
                        for code, label in cats:
                            if code == cat:
                                section = sec_name.replace(" ", "_")[:15]
                                break
                save_mapping(client_id, desc, cat, section)
                saved += 1

            st.success(f"✅ Salvati {saved} mapping per {sub['client_name']}")

        st.markdown("---")
        if st.button("📊 Vai ad Analisi →", use_container_width=True):
            # Salva automaticamente prima di andare
            for desc, cat in mapping_state.items():
                section = "DA_ESCLUDERE"
                if cat != "escludi":
                    for sec_name, cats in SECTION_OPTIONS.items():
                        for code, label in cats:
                            if code == cat:
                                section = sec_name.replace(" ", "_")[:15]
                                break
                save_mapping(client_id, desc, cat, section)

            st.switch_page("pages/4_Analisi.py")

        if st.button("🔄 Reset mapping", use_container_width=True):
            if "mapping_state" in st.session_state:
                del st.session_state["mapping_state"]
                del st.session_state["mapping_sub_id"]
            st.rerun()


main()
