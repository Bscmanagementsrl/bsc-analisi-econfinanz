"""
pages/4_Analisi.py — Admin: riclassificazione + indici + export
"""
import streamlit as st
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import (get_submission, get_lines, get_adjustments,
                       get_all_mappings, update_submission_status,
                       save_result, get_result)
from utils.reclassifier import (aggregate_by_category, compute_ce_va,
                                  compute_ce_cv, compute_sp_fin, compute_sp_fun,
                                  extract_kpis)
from utils.indices import compute_indices, indices_to_dataframe
from utils.exporter import export_analysis_excel
from utils.notifier import notify_client_analysis_ready
import pandas as pd

st.set_page_config(page_title="Analisi — BSC", page_icon="📊", layout="wide")

if st.session_state.get("role") != "admin":
    st.warning("Sezione riservata all'amministratore.")
    st.stop()


STATUS_COLOR = {
    "green":  ("#d5f5e3", "✅ Buono"),
    "yellow": ("#fdebd0", "⚠️ Attenzione"),
    "red":    ("#fadbd8", "🔴 Critico"),
    "info":   ("#eaf2ff", "ℹ️ Info"),
}


def fmt_eur(v):
    if v is None:
        return "—"
    neg = v < 0
    s = f"{abs(v):,.0f}"
    return f"({s})" if neg else s


def main():
    st.title("📊 Analisi Economico-Finanziaria")

    sub_id = st.session_state.get("active_sub_id")
    if not sub_id:
        st.info("Seleziona un invio dalla pagina «Da Elaborare».")
        st.stop()

    sub = get_submission(sub_id)
    if not sub:
        st.error("Invio non trovato.")
        st.stop()

    client_id   = sub["client_id"]
    client_name = sub["client_name"]
    period      = sub["period"]
    client_email = sub["email"]

    st.markdown(f"**Cliente:** {client_name} | **Periodo:** {period} | **ID:** #{sub_id}")

    # ── Carica dati ─────────────────────────────────────────────────────────
    lines    = list(get_lines(sub_id))
    adjs     = list(get_adjustments(sub_id))
    mappings = {m["raw_description"]: m["mapped_category"]
                for m in get_all_mappings(client_id)}

    # Applica mapping alle linee
    mapped_lines = []
    for line in lines:
        desc = line["raw_description"]
        cat  = mappings.get(desc, "escludi")
        mapped_lines.append(dict(line) | {"mapped_category": cat})

    # Aggiustamenti admin (schermata separata nella stessa pagina)
    st.markdown("---")
    is_admin = True  # la guardia in cima garantisce che siamo admin
    if is_admin:
        with st.expander("🔧 Aggiustamenti extracontabili (admin)", expanded=False):
            st.caption("Inserisci qui le rettifiche da applicare prima dell'analisi (ratei stimati, accantonamenti, WDO, ecc.)")

            from schema import SECTION_OPTIONS
            all_cats = [("escludi", "— Seleziona categoria —")]
            for sec, cats in SECTION_OPTIONS.items():
                for code, label in cats:
                    all_cats.append((code, f"[{sec[:6]}] {label}"))

            if "admin_adj" not in st.session_state:
                # Pre-carica aggiustamenti già salvati
                st.session_state["admin_adj"] = [
                    {"description": a["description"], "category": a["category"],
                     "value": float(a["value"]), "notes": a["notes"]}
                    for a in adjs
                ] or [{"description": "", "category": "escludi", "value": 0.0, "notes": ""}]

            if st.button("➕ Aggiungi aggiustamento"):
                st.session_state["admin_adj"].append(
                    {"description": "", "category": "escludi", "value": 0.0, "notes": ""}
                )

            new_adjs = []
            for i, row in enumerate(st.session_state["admin_adj"]):
                cols = st.columns([3, 3, 2, 3])
                desc = cols[0].text_input("Descr.", value=row["description"], key=f"aadjd_{i}", label_visibility="collapsed" if i else "visible")
                cat_idx = [c[0] for c in all_cats].index(row["category"]) if row["category"] in [c[0] for c in all_cats] else 0
                cat  = cols[1].selectbox("Cat.", options=[c[0] for c in all_cats],
                                         format_func=lambda x: dict(all_cats).get(x, x),
                                         index=cat_idx, key=f"aadjc_{i}",
                                         label_visibility="collapsed" if i else "visible")
                val  = cols[2].number_input("Val.", value=float(row["value"]), key=f"aadjv_{i}",
                                            label_visibility="collapsed" if i else "visible")
                note = cols[3].text_input("Note", value=row["notes"], key=f"aadjn_{i}",
                                          label_visibility="collapsed" if i else "visible")
                new_adjs.append({"description": desc, "category": cat, "value": val, "notes": note})

            st.session_state["admin_adj"] = new_adjs
            all_adjs = [r for r in new_adjs if r["description"]]
    else:
        all_adjs = adjs

    # ── Calcolo ─────────────────────────────────────────────────────────────
    cat_values = aggregate_by_category(mapped_lines, all_adjs)
    kpis       = extract_kpis(cat_values)
    ce_va      = compute_ce_va(cat_values)
    ce_cv      = compute_ce_cv(cat_values)
    sp_fin     = compute_sp_fin(cat_values)
    sp_fun     = compute_sp_fun(cat_values)
    indices    = compute_indices(kpis)

    # ── Tab output ───────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 CE Valore Aggiunto",
        "🏭 CE Costo del Venduto",
        "🏦 SP Finanziario",
        "⚙️ SP Funzionale",
        "📉 Indici",
    ])

    with tab1:
        _render_ce_table("CE a Valore Aggiunto", ce_va)

    with tab2:
        _render_ce_table("CE a Costo del Venduto", ce_cv)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            _render_sp_table("ATTIVO", sp_fin.get("attivo", []))
        with col2:
            _render_sp_table("PASSIVO E PN", sp_fin.get("passivo", []))

    with tab4:
        _render_ce_table("SP Funzionale", sp_fun)

    with tab5:
        _render_indices(indices)

    # ── KPIs box ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔑 Indicatori chiave")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("EBITDA", f"€ {fmt_eur(kpis.get('EBITDA',0))}")
    k2.metric("EBIT",   f"€ {fmt_eur(kpis.get('EBIT',0))}")
    k3.metric("PFN",    f"€ {fmt_eur(kpis.get('PFN',0))}")
    k4.metric("PN",     f"€ {fmt_eur(kpis.get('PN',0))}")

    # ── Azioni finali ────────────────────────────────────────────────────────
    st.markdown("---")
    col_save, col_export, col_notify = st.columns(3)

    with col_save:
        if st.button("💾 Salva analisi", type="primary"):
            result = {
                "kpis": kpis,
                "ce_va": ce_va,
                "ce_cv": ce_cv,
                "sp_fin": sp_fin,
                "sp_fun": sp_fun,
                "indices": indices,
            }
            save_result(sub_id, json.dumps(result, default=str))
            update_submission_status(sub_id, "done")
            st.success("✅ Analisi salvata. Stato aggiornato a «done».")

    with col_export:
        excel_bytes = export_analysis_excel(
            client_name=client_name,
            period=period,
            ce_va_rows=ce_va,
            ce_cv_rows=ce_cv,
            sp_fin=sp_fin,
            sp_fun_rows=sp_fun,
            indices=indices,
        )
        st.download_button(
            label="📥 Scarica Excel",
            data=excel_bytes,
            file_name=f"BSC_Analisi_{client_name.replace(' ', '_')}_{period}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col_notify:
        if client_email and st.button("📧 Notifica cliente"):
            ok, msg = notify_client_analysis_ready(client_email, client_name, period)
            if ok:
                st.success(f"✅ Email inviata a {client_email}")
            else:
                st.error(f"Errore invio email: {msg}")


def _render_ce_table(title: str, rows: list):
    st.markdown(f"#### {title}")

    for row in rows:
        row_type = row.get("type", "item")
        label    = row.get("label", "")
        value    = row.get("value", 0.0) or 0.0
        val_str  = fmt_eur(value)

        if row_type == "total":
            st.markdown(
                f"""<div style="background:#1a5276;color:white;padding:8px 12px;
                border-radius:4px;display:flex;justify-content:space-between;
                font-weight:bold;margin:4px 0">
                <span>{label}</span><span>{val_str}</span></div>""",
                unsafe_allow_html=True
            )
        elif row_type == "subtotal":
            color = "#d6eaf8"
            st.markdown(
                f"""<div style="background:{color};padding:6px 12px;
                display:flex;justify-content:space-between;font-weight:600;
                border-left:4px solid #1a5276;margin:3px 0">
                <span>{label}</span><span>{val_str}</span></div>""",
                unsafe_allow_html=True
            )
        else:
            color = "#f8f9fa" if value >= 0 else "#fff5f5"
            st.markdown(
                f"""<div style="background:{color};padding:4px 24px;
                display:flex;justify-content:space-between;font-size:0.9em;margin:1px 0">
                <span>{label}</span><span>{val_str}</span></div>""",
                unsafe_allow_html=True
            )


def _render_sp_table(title: str, rows: list):
    st.markdown(f"#### {title}")
    _render_ce_table("", rows)


def _render_indices(indices: list):
    groups = {}
    for idx in indices:
        g = idx["group"]
        groups.setdefault(g, []).append(idx)

    for group, idxs in groups.items():
        st.markdown(f"#### {group}")
        cols_per_row = 3
        for i in range(0, len(idxs), cols_per_row):
            row_idxs = idxs[i:i+cols_per_row]
            cols = st.columns(cols_per_row)
            for j, idx in enumerate(row_idxs):
                bg, emoji_label = STATUS_COLOR.get(idx["status"], ("#f8f9fa", ""))
                cols[j].markdown(
                    f"""<div style="background:{bg};padding:12px;border-radius:8px;
                    text-align:center;height:90px">
                    <div style="font-size:0.75em;color:#555">{idx['label']}</div>
                    <div style="font-size:1.4em;font-weight:bold;margin:4px 0">{idx['formatted']}</div>
                    <div style="font-size:0.7em">{emoji_label}</div></div>""",
                    unsafe_allow_html=True
                )

    st.markdown("---")
    st.markdown("**Tabella indici completa:**")
    df_idx = indices_to_dataframe(indices)
    if not df_idx.empty:
        st.dataframe(df_idx, use_container_width=True)


if __name__ == "__main__":
    main()

main()
