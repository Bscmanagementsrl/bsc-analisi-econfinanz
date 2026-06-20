"""
utils/notifier.py — Notifiche email via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _get_smtp_config() -> dict:
    """Legge configurazione SMTP dalle secrets di Streamlit."""
    try:
        import streamlit as st
        return {
            "host":     st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
            "port":     int(st.secrets.get("SMTP_PORT", 587)),
            "user":     st.secrets.get("SMTP_USER", ""),
            "password": st.secrets.get("SMTP_PASSWORD", ""),
            "from":     st.secrets.get("SMTP_FROM", st.secrets.get("SMTP_USER", "")),
            "admin":    st.secrets.get("ADMIN_EMAIL", "studiopietroforte@gmail.com"),
        }
    except Exception:
        import os
        return {
            "host":     os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            "port":     int(os.environ.get("SMTP_PORT", 587)),
            "user":     os.environ.get("SMTP_USER", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "from":     os.environ.get("SMTP_FROM", ""),
            "admin":    os.environ.get("ADMIN_EMAIL", "studiopietroforte@gmail.com"),
        }


def _send_email(to: str, subject: str, html_body: str) -> tuple[bool, str]:
    cfg = _get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        return False, "Configurazione SMTP mancante (vedere secrets)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = cfg["from"] or cfg["user"]
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from"] or cfg["user"], [to], msg.as_string())
        return True, "Email inviata"
    except Exception as e:
        return False, str(e)


def notify_admin_new_submission(client_name: str, period: str, sub_id: int) -> tuple[bool, str]:
    """Avvisa Annamaria che un cliente ha caricato i dati."""
    cfg = _get_smtp_config()
    subject = f"[BSC Analisi] Nuovo invio da {client_name} — {period}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
    <h2 style="color:#1a5276">📥 Nuovo bilancio ricevuto</h2>
    <table style="border-collapse:collapse">
      <tr><td style="padding:6px 12px;font-weight:bold">Cliente:</td>
          <td style="padding:6px 12px">{client_name}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold">Periodo:</td>
          <td style="padding:6px 12px">{period}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold">ID invio:</td>
          <td style="padding:6px 12px">#{sub_id}</td></tr>
    </table>
    <br>
    <p>Accedi all'area admin per elaborare l'analisi.</p>
    <p style="color:#888;font-size:12px">BSC Management srl — Sistema automatico</p>
    </body></html>
    """
    return _send_email(cfg["admin"], subject, body)


def notify_client_analysis_ready(client_email: str, client_name: str, period: str) -> tuple[bool, str]:
    """Avvisa il cliente che l'analisi è pronta."""
    subject = f"[BSC] Analisi economico-finanziaria {period} disponibile"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
    <h2 style="color:#1a5276">📊 La sua analisi è pronta</h2>
    <p>Gentile {client_name},</p>
    <p>L'analisi economico-finanziaria relativa al periodo <strong>{period}</strong>
       è stata elaborata ed è disponibile nella sua area riservata.</p>
    <p>Acceda al portale BSC per visualizzare la riclassificazione e gli indici.</p>
    <br>
    <p>Cordiali saluti,<br><strong>Studio BSC Management</strong></p>
    <p style="color:#888;font-size:12px">Dott.ssa Annamaria Pietroforte — studiopietroforte@gmail.com</p>
    </body></html>
    """
    return _send_email(client_email, subject, body)
