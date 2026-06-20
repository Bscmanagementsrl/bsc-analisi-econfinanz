"""
pages/1_Carica_Bilancio.py — Area cliente: upload bilancio
"""
import streamlit as st
import sys, os, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import create_submission, save_lines, list_submissions
from utils.parser import parse_excel, parse_pdf, get_sheet_names
from utils.notifier import notify_admin_new_submission
import pandas as pd

st.set_page_config(page_title="Carica Bilancio — BSC", page_icon="📤", layout="wide")

if not st.session_state.get("user_id"):
    st.warning("Accesso riservato. Torna alla home.")
    st.stop()


def main():
    st.title("📤 Carica il Bilancio Mensile")
    st.caption("Carica il file Excel del tuo gestionale.")

    client_id   = st.session_state["user_id"]
    client_name = st.session_state.get("client_name", "")

    tab1, tab2 = st.tabs(["📁 Nuovo invio", "📋 Storico invii"])

    with tab1:
        st.markdown("### 1️⃣ Seleziona il periodo")
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox(
                "Anno", list(range(2022, 2031)),
                index=datetime.date.today().year - 2022,
                key="sel_anno"
            )
            month = st.selectbox(
                "Mese", list(range(1, 13)),
                format_func=lambda m: [
                    "Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                    "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"
                ][m-1],
                index=datetime.date.today().month - 1,
                key="sel_mese"
            )
        period = f"{year}-{month:02d}"
        st.caption(f"Periodo selezionato: **{period}**")

        st.markdown("### 2️⃣ Carica il file bilancio")
        uploaded = st.file_uploader(
            "Trascina qui il file Excel o PDF del gestionale",
            type=["xlsx", "xls", "pdf"],
            key="file_uploader_bilancio",
            help="Accettiamo qualunque layout."
        )

        lines = []
        sheet_chosen = None

        if uploaded:
            file_bytes = uploaded.read()
            ext = uploaded.name.split(".")[-1].lower()

            if ext in ("xlsx", "xls"):
                try:
                    sheets = get_sheet_names(file_bytes)
                    if len(sheets) > 1:
                        sheet_chosen = st.selectbox(
                            "Seleziona il foglio da importare", sheets, key="sel_foglio"
                        )
                    else:
                        sheet_chosen = sheets[0]
                    lines = parse_excel(file_bytes, sheet_chosen)
                    st.success(f"Estratte **{len(lines)}** righe dal foglio «{sheet_chosen}»")
                    if lines:
                        with st.expander("Anteprima dati estratti"):
                            preview_df = pd.DataFrame([
                                {"Codice": l["raw_code"],
                                 "Descrizione": l["raw_description"],
                                 "Valore": l["raw_value"]}
                                for l in lines[:30]
                            ])
                            st.dataframe(preview_df, use_container_width=True)
                            if len(lines) > 30:
                                st.caption(f"... e altre {len(lines)-30} righe")
                except Exception as e:
                    st.error(f"Errore lettura Excel: {e}")
            elif ext == "pdf":
                try:
                    lines = parse_pdf(file_bytes)
                    st.success(f"Estratte **{len(lines)}** righe dal PDF")
                except Exception as e:
                    st.error(f"Errore lettura PDF: {e}")

        st.markdown("### 3️⃣ Note per il consulente")
        free_notes = st.text_area(
            "Note aggiuntive (opzionale)",
            placeholder="Es.: crediti contestati, fatture da emettere, lavori in corso...",
            key="note_libere"
        )

        st.markdown("---")
        submit_btn = st.button("📨 Invia al consulente BSC", type="primary", key="btn_invia")

        if submit_btn:
            if not lines:
                st.error("Carica almeno un file bilancio prima di inviare.")
            else:
                with st.spinner("Salvataggio in corso..."):
                    sub_id = create_submission(
                        client_id=client_id, period=period,
                        notes=free_notes, filename=uploaded.name if uploaded else ""
                    )
                    save_lines(sub_id, lines)
                    ok, msg = notify_admin_new_submission(client_name, period, sub_id)
                st.success(f"Invio completato (ID #{sub_id}). Il consulente e' stato notificato.")
                if not ok:
                    st.warning(f"Notifica email non inviata ({msg}).")
                st.rerun()

    with tab2:
        st.markdown("### 📋 I tuoi invii")
        subs = list_submissions(client_id=client_id)
        if not subs:
            st.info("Nessun invio ancora. Usa il tab Nuovo invio per iniziare.")
        else:
            status_icon = {
                "pending":     "🟡 In attesa",
                "in_progress": "🔵 In elaborazione",
                "done":        "✅ Analisi pronta"
            }
            for s in subs:
                icon  = status_icon.get(s["status"], "Sconosciuto")
                per   = s["period"]
                ts    = s["submitted_at"][:16]
                with st.expander(f"{icon} — {per} — {ts}"):
                    c1, c2 = st.columns(2)
                    c1.write("File: " + (s["filename"] or "N/D"))
                    c2.write("Stato: " + s["status"])
                    if s["notes"]:
                        st.write("Note: " + s["notes"])
                    if s["status"] == "done":
                        st.success("L'analisi è stata elaborata dalconsulente BSC.")


main()
