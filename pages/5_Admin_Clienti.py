"""
pages/5_Admin_Clienti.py — Gestione clienti (admin only)
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import list_clients, create_user, update_user_password, get_all_mappings

st.set_page_config(page_title="Clienti — BSC", page_icon="👥", layout="wide")

if st.session_state.get("role") != "admin":
    st.warning("Sezione riservata all'amministratore.")
    st.stop()


def main():
    st.title("👥 Gestione Clienti")

    tab1, tab2, tab3 = st.tabs(["📋 Lista clienti", "➕ Nuovo cliente", "🔑 Reset password"])

    with tab1:
        clients = list_clients()
        if not clients:
            st.info("Nessun cliente ancora. Usa «Nuovo cliente» per aggiungere il primo.")
        else:
            for c in clients:
                with st.expander(f"🏢 {c['client_name']} — `{c['username']}`"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Email:** {c['email'] or '—'}")
                    col1.write(f"**Creato:** {c['created_at'][:10]}")
                    col2.write(f"**Attivo:** {'✅' if c['active'] else '❌'}")

                    # Mapping count
                    mappings = get_all_mappings(c["id"])
                    col2.write(f"**Mapping salvati:** {len(mappings)}")

                    if mappings:
                        if st.checkbox(f"Vedi mapping di {c['client_name']}", key=f"map_view_{c['id']}"):
                            import pandas as pd
                            df = pd.DataFrame([{
                                "Voce": m["raw_description"],
                                "Categoria": m["mapped_category"],
                                "Sezione": m["mapped_section"],
                                "Ultimo uso": m["last_used"][:10]
                            } for m in mappings])
                            st.dataframe(df, use_container_width=True)

    with tab2:
        st.markdown("### Crea nuovo cliente")
        with st.form("new_client_form"):
            col1, col2 = st.columns(2)
            username    = col1.text_input("Username *", placeholder="mario.rossi")
            password    = col2.text_input("Password iniziale *", type="password", placeholder="min 6 caratteri")
            client_name = col1.text_input("Ragione sociale *", placeholder="Pippo S.r.l.")
            email       = col2.text_input("Email cliente", placeholder="info@pipposrl.it")

            submitted = st.form_submit_button("✅ Crea cliente", type="primary")

        if submitted:
            if not username or not password or not client_name:
                st.error("Compila i campi obbligatori (*).")
            elif len(password) < 6:
                st.error("La password deve essere di almeno 6 caratteri.")
            else:
                ok, msg = create_user(username, password, "client", client_name, email)
                if ok:
                    st.success(f"✅ Cliente '{client_name}' creato. Username: **{username}**")
                else:
                    st.error(f"Errore: {msg}")

    with tab3:
        st.markdown("### Reset password cliente")
        clients = list_clients()
        if not clients:
            st.info("Nessun cliente da cui fare reset.")
        else:
            client_options = {c["id"]: f"{c['client_name']} ({c['username']})" for c in clients}
            selected_id = st.selectbox("Cliente", options=list(client_options.keys()),
                                       format_func=lambda x: client_options[x])
            new_pw = st.text_input("Nuova password", type="password")
            if st.button("🔑 Aggiorna password") and new_pw:
                if len(new_pw) < 6:
                    st.error("Password troppo corta (min 6 caratteri).")
                else:
                    update_user_password(selected_id, new_pw)
                    st.success("✅ Password aggiornata.")


main()
