"""
app.py — BSC Analisi Economico-Finanziaria
Entry point Streamlit: login e routing
"""
import streamlit as st
import sys, os

# Rende importabili i moduli locali
sys.path.insert(0, os.path.dirname(__file__))

from utils.db import init_db, authenticate

init_db()

st.set_page_config(page_title="BSC — Analisi Eco-Fin", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("<style>#MainMenu{visibility:hidden}footer{visibility:hidden}</style>", unsafe_allow_html=True)

def is_logged_in(): return st.session_state.get("user_id") is not None

def login_form():
    _,col2,_ = st.columns([1,1.2,1])
    with col2:
        st.markdown("## 📊 BSC Management")
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Accedi", use_container_width=True)
        if ok:
            from utils.db import authenticate
            usr = authenticate(u, p)
            if usr:
                for k in ["user_id","username","role","client_name","email"]: st.session_state[k] = usr[k]
                st.rerun()
            else: st.error("Credenziali non valide")

def main():
    if not is_logged_in(): login_form(); st.stop()
    with st.sidebar:
        st.write(f"👤 {st.session_state.get('client_name','')}")
        st.caption(st.session_state.get('role','').upper())
        if st.button("Esci"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    role = st.session_state.get("role","client")
    if role=="admin":
        from utils.db import list_submissions
        st.title("📊 Dashboard Admin")
        subs=list_submissions()
        p,i,d=[s for s in subs if s['status']=='pending'],[s for s in subs if s['status']=='in_progress'],[s for s in subs if s['status']=='done']
        c1,c2,c3=st.columns(3)
        c1.metric("📥 In attesa",len(p)); c2.metric("🔄!...",len(i)); c3.metric("✅ Fatte",len(d))
    else:
        st.title(f"👋 Benvenuto, {st.session_state.get('client_name','')}")
        st.info("Carica il bilancio mensile dal menu laterale.")

if __name__=="__main__": main()
