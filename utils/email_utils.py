import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env que está na raiz
load_dotenv()

# configutação para roda localmente
# EMAIL_HOST = os.getenv("EMAIL_HOST")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
# EMAIL_USER = os.getenv("EMAIL_USER")
# EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

#configuração para rodar em produção (Streamlit Cloud)
import streamlit as st

def enviar_email(destinatario, assunto, corpo):
    try:
        EMAIL_HOST = st.secrets["email_credentials"]["EMAIL_HOST"]
        EMAIL_PORT = int(st.secrets["email_credentials"]["EMAIL_PORT"])
        EMAIL_USER = st.secrets["email_credentials"]["EMAIL_USER"]
        EMAIL_PASSWORD = st.secrets["email_credentials"]["EMAIL_PASSWORD"]
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = EMAIL_USER
        msg["To"] = destinatario
        msg.set_content(corpo)

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        
        return True
    
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
