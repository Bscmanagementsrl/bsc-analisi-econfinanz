"""
pages/1_Carica_Bilancio.py — Area cliente: upload bilancio + aggiustamenti
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import create_submission, save_lines, save_adjustments, get_lines, get_adjustments, list_submissions
from utils.parser import parse_excel, parse_pdf, get_sheet_names
from utils.notifier import notify_admin_new_submission
import pandas as pd

st.set_page_config(page_title="Carica Bilancio — BSC", page_icon="📤", layout="wide")

if not st.session_state.get("user_id"):
    st.warning("Accesso riservato. Torna alla home.")
    st.stop()


def main():
    st.title("📤 Carica il Bilancio Mensile")
    st.caption("Carica il file Excel del tuo gestionale e compila la griglia degli aggiustamenti.")

    client_id   = st.session_state["user_id"]
    client_name = st.session_state.get("client_name", "")

    tab1, tab2 = st.tabs(["📁 Nuovo invio", "📋 Storico invii"])

    # ── TAB 1: Nuovo invio ──────────────────────────────────────────────────
    with tab1:
        st.markdown("### 1️⃣ Seleziona il periodo")
        col1, col2 = st.columns(2)
        with col1:
            import datetime
            year  = st.selectbox("Anno", list(range(2022, 2030)), index=datetime.date.today().year - 2022)
            month = st.selectbox("Mese", list(range(1, 13)),
                                  format_func=lambda m: [
                                      "Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                                      "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"
                                  ][m-1],
                                  index=datetime.date.today().month - 1)
        period = f"{year}-{month:02d}"
        st.caption(f"Periodo selezionato: **{period}**")

        st.markdown("### 2️⃣ Carica il file bilancio")
        uploaded = st.file_uploader(
            "Trascina qui il file Excel o PDF del gestionale",
            type=["xlsx", "xls", "pdf"],
            help="Accettiamo qualunque layout: lo leggiamo e proponiamo il mapping automatico."
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
                        sheet_chosen = st.selectbox("Seleziona il foglio da importare", sheets)
                    else:
                        sheet_chosen = sheets[0]

                    lines = parse_excel(file_bytes, sheet_chosen)
                    st.success(f"✅ Estratte **{len(lines)}** righe dal foglio «{sheet_chosen}»")

                    if lines:
                        with st.expander("👁️ Anteprima dati estratti"):
                            preview_df = pd.DataFrame([
                                {"Codice": l["raw_code"],
                                 "Descrizione": l["raw_description"],
                                 "Valore (€)": f"{l['raw_value']:,.2f}"}
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
                    st.success(f"✅ Estratte **{len(lines)}** righe dal PDF")
                except Exception as e:
                    st.error(f"Errore lettura PDF: {e}")

        st.markdown("### 3️⃣ Aggiustamenti e note")
        st.info("Inserisci qui gli assestamenti mensili non presenti nel bilancio (ratei, risconti, svalutazioni extra, ecc.)")

        # Griglia aggiustamenti dinamica
        if "adj_rows" not in st.session_state:
            st.session_state["adj_rows"] = [{"description": "", "category": "", "value": 0.0, "notes": ""}]

        col_add, col_clear = st.columns([1, 1])
        with col_add:
            if st.button("➕ Aggiungi riga aggiustamento"):
                st.session_state["adj_rows"].append(
                    {"description": "", "category": "", "value": 0.0, "notes": ""}
                )
        with col_clear:
            if st.button("🗑️ Svuota griglia"):
                st.session_state["adj_rows"] = [{"description": "", "category": "", "value": 0.0, "notes": ""}]

        from schema import SECTION_OPTIONS, CATEGORY_LABEL_MAP
        all_cats = [("escludi", "— Seleziona categoria —")]
        for sec, cats in SECTION_OPTIONS.items():
            for code, label in cats:
                all_cats.append((code, f"[{sec[:6]}] {label}"))

        adj_data = []
        for i, row in enumerate(st.session_state["adj_rows"]):
            cols = st.columns([3, 3, 2, 3, 0.5])
            desc  = cols[0].text_input("Descrizione", value=row["description"], key=f"adj_desc_{i}", label_visibility="collapsed" if i > 0 else "visible")
            cat_idx = [c[0] for c in all_cats].index(row["category"]) if row["category"] in [c[0] for c in all_cats] else 0
            cat   = cols[1].selectbox("Categoria", options=[c[0] for c in all_cats],
                                       format_func=lambda x: dict(all_cats).get(x, x),
                                       index=cat_idx, key=f"adj_cat_{i}",
                                       label_visibility="collapsed" if i > 0 else "visible")
            val   = cols[2].number_input("Valore", value=float(row["value"]), key=f"adj_val_{i}",
                                          label_visibility="collapsed" if i > 0 else "visible")
            note  = cols[3].text_input("Note", value=row["notes"], key=f"adj_note_{i}",
                                        label_visibility="collapsed" if i > 0 else "visible")
            if cols[4].button("✕", key=f"adj_del_{i}") and len(st.session_state["adj_rows"]) > 1:
                st.session_state["adj_rows"].pop(i)
                st.rerun()
            adj_data.append({"description": desc, "category": cat, "value": val, "notes": note})

        st.session_state["adj_rows"] = adj_data

        st.markdown("### 4️⃣ Note libere per il consulente")
        free_notes = st.text_area("Note aggiuntive (opzionale)",
                                   placeholder="Es.: fatture da emettere, crediti contestati, lavori in corso...")

        st.markdown("---")
        col_sub, _ = st.columns([1, 3])
        with col_sub:
            submit_btn = st.button("📨 Invia al consulente BSC", type="primary", use_container_width=True)

        if submit_btn:
            if not lines and not any(r["description"] for r in adj_data if r["description"]):
                st.error("Carica almeno un file bilancio oppure inserisci degli aggiustamenti.")
            else:
                with st.spinner("Salvataggio in corso..."):
                    # Crea la submission
                    sub_id = create_submission(
                        client_id=client_id,
                        period=period,
                        notes=free_notes,
                        filename=uploaded.name if uploaded else ""
                    )

                    # Salva le righe estratte
                    if lines:
                        save_lines(sub_id, lines)

                    # Salva aggiustamenti
                    adj_to_save = [r for r in adj_data if r["description"]]
                    if adj_to_save:
                        save_adjustments(sub_id, adj_to_save)

                    # Notifica admin
                    ok, msg = notify_admin_new_submission(client_name, period, sub_id)

                st.success(f"✅ Invio completato (ID #{sub_id})! Il consulente BSC è stato notificato.")
                if not ok:
                    st.warning(f"Nota: notifica email non inviata ({msg}). Il consulente vedrà l'invio dalla dashboard.")

                # Reset
                st.session_state["adj_rows"] = [{"description": "", "category": "", "value": 0.0, "notes": ""}]
                st.rerun()

    # ── TAB 2: Storico ──────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 📋 I tuoi invii")
        subs = list_submissions(client_id=client_id)
        if not subs:
            st.info("Nessun invio ancora. Usa il tab «Nuovo invio» per iniziare.")
        else:
            status_icon = {"pending": "🟡 In attesa", "in_progress": "🔵 In elaborazione", "done": "✅ Analisi pronta"}
            for s in subs:
                icon_label = status_icon.get(s["status"], "⚪ Sconosciuto")
                with st.expander(f"{icon_label} — **{s['period']}** — _{s['submitted_at'][:16]}_"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**File:** {s['filename'] or 'N/D'}")
                    col2.write(f"**Stato:** {s['status']}")
                    if s["notes"]:
                        st.write(f"**Note:** {s['notes']}")

                    if s["status"] == "done":
                        st.success("L'analisi è stata elaborata dal suo consulente. 🎉")
                        # TODO: link a visualizzazione risultati per il cliente


if __name__ == "__main__":
    main()

main()
