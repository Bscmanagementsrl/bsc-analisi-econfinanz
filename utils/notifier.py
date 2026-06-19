"""
utils/notifier.py — Notifiche email via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _get_smtp_config():
    try:
        import streamlit as st
        return {"host":st.secrets.get("SMTP_HOST","smtp.gmail.com"),"port":int(st.secrets.get("SMTP_PORT",587)),"user":st.secrets.get("SMTP_USER",""),"password":st.secrets.get("SMTP_PASSWORD",""),"from":st.secrets.get("SMTP_FROM",""),"admin":st.secrets.get("ADMIN_EMAIL","studiopietroforte@gmail.com")}
    except:
        import os
        return {"host":os.environ.get("SMTP_HOST","smtp.gmail.com"),"port":int(os.environ.get("SMTP_PORT",587)),"user":os.environ.get("SMTP_USER",""),"password":os.environ.get("SMTP_PASSWORD",""),"from":os.environ.get("SMTP_FROM",""),"admin":os.environ.get("ADMIN_EMAIL","studiopietroforte@gmail.com")}

def _send_email(to, subject, html_body):
    cfg = _get_smtp_config()
    if not cfg["user"] or not cfg["password"]: return False,"Config SMTP mancante"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject; msg["From"] = cfg["from"] or cfg["user"]; msg["To"] = to
    msg.attach(MIMEText(html_body,"html","utf-8"))
    try:
        with smtplib.SMTP(cfg["host"],cfg["port"]) as s:
            s.ehlo(); s.starttls(); s.login(cfg["user"],cfg["password"]); s.sendmail(cfg["from"] or cfg["user"],[to],msg.as_string())
        return True,"Email inviata"
    except Exception as e: return False,str(e)

def notify_admin_new_submission(client_name,period,sub_id):
    cfg = _get_smtp_config()
    subject = f"[BSC Analisi] Nuovo invio da {client_name} — {period}"
    body = f"<html><body><h2>📥 Nuovo bilancio da {client_name}</h2><p>Periodo: {period} - ID: {sub_id}</p><p>Accedi all'area admin per elaborare.</p></body></html>"
    return _send_email(cfg["admin"],subject,body)

def notify_client_analysis_ready(client_email,client_name,period):
    subject = f"[BSC] Analisi {period} disponibile"
    body = f"<html><body><h2>📊 L'analisi è pronta</h2><p>Gentile {client_name}, l'analisi per {period} è disponibile nel portale BSC.</p><p>Cordiali saluti,<br>Studio BSC Management</p></body></html>"
    return _send_email(client_email,subject,body)
