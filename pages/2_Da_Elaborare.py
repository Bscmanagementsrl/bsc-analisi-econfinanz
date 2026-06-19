"""
pages/2_Da_Elaborare.py — Admin: coda invii in attesa
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import list_submissions, get_submission, get_lines, get_adjustments, update_submission_status
import pandas as pd

st.set_page_config(page_title="Da Elaborare — BSC", page_icon="📥", layout="wide")

if st.session_state.get("role") != "admin":
    st.warning("Sezione riservata all'amministratore.")
    st.stop()


def main():
    st.title("📥 Invii da elaborare")

    tab1, tab2, tab3 = st.tabs(["🟡 In attesa", "🔵 In lavorazione", "✅ Completati"])

    for tab, status, label in [
        (tab1, "pending", "In attesa"),
        (tab2, "in_progress", "In lavorazione"),
        (tab3, "done", "Completati"),
    ]:
        with tab:
            subs = list_submissions(status=status)
            if not subs:
                st.info(f"Nessun invio {label.lower()}.")
                continue

            for s in subs:
                with st.expander(
                    f"📁 **{s['client_name']}** — {s['period']} (#{s['id']}) — {s['submitted_at'][:16]}"
                ):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    col1.write(f"**File:** {s['filename'] or 'N/D'}")
                    col1.write(f"**Note:** {s['notes'] or '—'}")
                    col2.write(f"**Stato:** {s['status']}")
                    col2.write(f"**Username:** {s['username']}")

                    lines = get_lines(s["id"])
                    adjs  = get_adjustments(s["id"])

                    col3.metric("Righe bilancio", len(lines))
                    col3.metric("Aggiustamenti", len(adjs))

                    if lines:
                        with st.container():
                            st.markdown("**Anteprima voci bilancio:**")
                            df = pd.DataFrame([{
                                "Codice": l["raw_code"],
                                "Descrizione": l["raw_description"],
                                "Valore (€)": f"{l['raw_value']:,.2f}" if l["raw_value"] else "0"
                            } for l in lines[:20]])
                            st.dataframe(df, use_container_width=True, height=200)

                    if adjs:
                        st.markdown("**Aggiustamenti inseriti dal cliente:**")
                        df_adj = pd.DataFrame([{
                            "Descrizione": a["description"],
                            "Categoria": a["category"],
                            "Valore (€)": f"{a['value']:,.2f}",
                            "Note": a["notes"]
                        } for a in adjs])
                        st.dataframe(df_adj, use_container_width=True)

                    st.markdown("---")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if status != "in_progress" and st.button(
                            "▶ Avvia elaborazione", key=f"start_{s['id']}"
                        ):
                            update_submission_status(s["id"], "in_progress")
                            st.session_state["active_sub_id"] = s["id"]
                            st.rerun()

                    with col_b:
                        if st.button("🗺️ Vai a Mapping", key=f"map_{s['id']}"):
                            update_submission_status(s["id"], "in_progress")
                            st.session_state["active_sub_id"] = s["id"]
                            st.switch_page("pages/3_Mapping.py")

                    with col_c:
                        if status == "in_progress" and st.button(
                            "📊 Vai ad Analisi", key=f"anal_{s['id']}"
                        ):
                            st.session_state["active_sub_id"] = s["id"]
                            st.switch_page("pages/4_Analisi.py")


main()
