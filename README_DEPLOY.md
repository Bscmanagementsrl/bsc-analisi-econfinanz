# BSC Analisi Eco-Fin — Guida al Deployment

## Cosa fa l'applicazione

Applicazione web per l'analisi economico-finanziaria dei clienti BSC Management.

**Flusso cliente:**
1. Accede con username e password
2. Carica il file Excel del bilancio mensile (qualunque formato gestionale)
3. Compila la griglia degli aggiustamenti extracontabili
4. Invia → notifica automatica via email alla Dott.ssa Pietroforte

**Flusso admin (Annamaria):**
1. Riceve notifica email
2. Accede alla dashboard
3. Mappa le voci del bilancio alle categorie BSC (AI-assistito + memoria per cliente)
4. Inserisce eventuali rettifiche admin
5. Ottiene: CE a Valore Aggiunto, CE a Costo del Venduto, SP Finanziario, SP Funzionale, Indici
6. Scarica Excel formattato e/o notifica il cliente

---

## DEPLOYMENT — Passo per Passo

### Prerequisiti
- Account GitHub (gratuito): https://github.com
- Account Streamlit Community Cloud (gratuito): https://streamlit.io/cloud

---

### Passo 1 — Crea repository GitHub

1. Vai su https://github.com → **New repository**
2. Nome: `bsc-analisi-econfinanz` (o simile)
3. Visibilità: **Private** (consigliato)
4. Non aggiungere README (lo carichiamo noi)
5. Crea repository

---

### Passo 2 — Carica i file

Nella cartella `bsc_analisi/` trovi tutti i file dell'applicazione.
Caricali su GitHub trascinandoli nell'interfaccia web oppure con:

```bash
cd bsc_analisi
git init
git add .
git commit -m "BSC Analisi Eco-Fin v1.0"
git remote add origin https://github.com/TUO_USERNAME/bsc-analisi-econfinanz.git
git push -u origin main
```

**IMPORTANTE:** Non caricare il file `.streamlit/secrets.toml` (contiene le password).
Il file `.streamlit/secrets.toml.example` è sicuro da caricare.

---

### Passo 3 — Configura Streamlit Cloud

1. Vai su https://share.streamlit.io
2. Click **New app**
3. Repository: `bsc-analisi-econfinanz`
4. Branch: `main`
5. Main file path: `app.py`
6. Click **Deploy!**

---

### Passo 4 — Configura le Secrets

Nella dashboard Streamlit Cloud → tuo app → **Settings → Secrets**
Incolla il contenuto di `secrets.toml.example` compilato con i tuoi valori:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
SMTP_USER     = "la-tua-email@gmail.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
ADMIN_EMAIL   = "studiopietroforte@gmail.com"
```

**Come ottenere App Password Gmail:**
1. Vai su https://myaccount.google.com/security
2. Attiva "Verifica in due passaggi" (se non già attiva)
3. Cerca "App password" → Genera nuova → "Mail" + "Altro (BSC)"
4. Copia le 16 lettere generate

---

### Passo 5 — Ottieni il link

Dopo il deploy, Streamlit ti dà un URL tipo:
`https://bsc-analisi-econfinanz-xyz.streamlit.app`

Su WordPress: aggiungi questo link nell'area riservata come bottone o iframe.

---

## Credenziali di default

- **Admin:** username `admin` / password `bsc2024!`
- **Cambia la password subito** dopo il primo accesso!

---

## Aggiunta clienti

Dalla pagina "Admin Clienti" crea un profilo per ogni cliente con:
- Username (es. `mario.rossi`)
- Password iniziale (da comunicare al cliente)
- Ragione sociale
- Email (per le notifiche automatiche)

---

## Note tecniche

- **Database:** SQLite locale — persiste tra le sessioni su Streamlit Cloud
- **Per produzione con molti utenti:** migrare a PostgreSQL (Supabase gratuito)
- **Backup:** scarica periodicamente il file `data/bsc.db`

---

Assistenza tecnica: BRCManagement / studiopietroforte@gmail.com
