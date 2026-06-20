"""
app.py — BSC Analisi Economico-Finanziaria
Entry point Streamlit: login e routing
"""
import streamlit as st
import sys, os

# Rende importabili i moduli locali
sys.path.insert(0, os.path.dirname(__file__))

from utils.db import init_db, authenticate

# ─── Configurazione pagina ──────────────────────────────────────────────────
st.set_page_config(
    page_title="BSC — Analisi Eco-Fin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inizializzazione DB ────────────────────────────────────────────────────
init_db()

# ─── CSS personalizzato ─────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] { background: #1a3a5c; }
    [data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stSidebarNav"] a { color: #bdc3c7 !important; }
    [data-testid="stSidebarNav"] a:hover { color: #ffffff !important; }

    /* Bottoni primari */
    .stButton>button {
        background: #1a5276;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover { background: #154360; }

    /* Card metriche */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #1a5276;
    }

    /* Nasconde menu hamburger in produzione */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Logo area */
    .bsc-logo { font-size:1.8rem; font-weight:900; color:#1a5276; }
    .bsc-sub  { font-size:0.85rem; color:#7f8c8d; }
</style>
""", unsafe_allow_html=True)


# ─── Gestione sessione ──────────────────────────────────────────────────────
def is_logged_in() -> bool:
    return st.session_state.get("user_id") is not None


def login_form():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding:40px 0 20px'>
          <div class='bsc-logo'>📊 BSC Management</div>
          <div class='bsc-sub'>Analisi Economico-Finanziaria</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="es. mario.rossi")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi", use_container_width=True)

        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["user_id"]   = user["id"]
                st.session_state["username"]  = user["username"]
                st.session_state["role"]      = user["role"]
                st.session_state["client_name"] = user["client_name"]
                st.session_state["email"]     = user["email"]
                st.rerun()
            else:
                st.error("Credenziali non valide. Riprovare.")

        st.markdown("""
        <div style='text-align:center; margin-top:30px; color:#95a5a6; font-size:0.8rem'>
          Accesso riservato ai clienti BSC Management srl<br>
          Per assistenza: studiopietroforte@gmail.com
        </div>
        """, unsafe_allow_html=True)


# ─── Main ───────────────────────────────────────────────────────────────────
def main():
    if not is_logged_in():
        login_form()
        st.stop()

    # Sidebar con info utente e navigazione
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:12px 0'>
          <div style='font-size:1.3rem; font-weight:900'>📊 BSC</div>
          <div style='font-size:0.8rem; opacity:0.7'>Analisi Eco-Fin</div>
        </div>
        <hr style='border-color:#2e86c1; margin:8px 0'>
        <div style='font-size:0.85rem; margin-bottom:4px'>
          👤 <b>{st.session_state.get("client_name", "")}</b>
        </div>
        <div style='font-size:0.75rem; opacity:0.6; margin-bottom:16px'>
          {st.session_state.get("role","").upper()}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Esci", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Home page con dashboard
    role = st.session_state.get("role", "client")

    if role == "admin":
        _admin_home()
    else:
        _client_home()


def _admin_home():
    from utils.db import list_submissions
    st.title("📊 Dashboard Admin — BSC Analisi Eco-Fin")
    st.caption("Benvenuta, Dott.ssa Pietroforte. Seleziona una sezione dal menu laterale.")

    col1, col2, col3 = st.columns(3)
    subs = list_submissions()
    pending = [s for s in subs if s["status"] == "pending"]
    in_prog = [s for s in subs if s["status"] == "in_progress"]
    done    = [s for s in subs if s["status"] == "done"]

    col1.metric("📥 In attesa", len(pending))
    col2.metric("🔄 In elaborazione", len(in_prog))
    col3.metric("✅ Completate", len(done))

    if pending:
        st.markdown("### 🔔 Invii in attesa di elaborazione")
        for s in pending[:5]:
            with st.expander(f"📁 {s['client_name']} — {s['period']} (#{s['id']})"):
                st.write(f"**Inviato il:** {s['submitted_at']}")
                st.write(f"**Note cliente:** {s['notes'] or '—'}")
                if st.button(f"▶ Elabora #{s['id']}", key=f"goto_{s['id']}"):
                    st.session_state["active_sub_id"] = s["id"]
                    st.switch_page("pages/3_Mapping.py")


def _client_home():
    from utils.db import list_submissions
    name = st.session_state.get("client_name", "")
    st.title(f"👋 Benvenuto, {name}")
    st.info("Da qui puoi caricare il bilancio mensile e comunicare con il tuo consulente BSC.")

    subs = list_submissions(client_id=st.session_state["user_id"])

    if subs:
        st.markdown("### 📋 I tuoi invii recenti")
        status_icon = {"pending": "🟡", "in_progress": "🔵", "done": "✅"}
        for s in subs[:10]:
            icon = status_icon.get(s["status"], "⚪")
            st.markdown(f"{icon} **{s['period']}** — {s['status']} — _{s['submitted_at'][:10]}_")
    else:
        st.markdown("Nessun invio ancora. Usa **Carica Bilancio** per iniziare.")


if __name__ == "__main__":
    main()
