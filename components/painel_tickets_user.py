import streamlit as st
from data.manager_postgre import DatabaseManagerPostgres
from streamlit.components.v1 import html
import io
from PIL import Image
from datetime import datetime
import time
import base64
from io import BytesIO
import streamlit.components.v1 as components
from utils.email_utils import enviar_email

def parse_data(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    except:
        return data_str  # caso já seja datetime ou vazio


def mostrar_meus_tickets(email_usuario):
    """Mostra os tickets do usuário logado"""
    st.subheader("🎫 Meus Tickets de Ajuda")
    
    db = DatabaseManagerPostgres()
    tickets = db.listar_tickets(email_usuario=email_usuario)
    
    if not tickets:
        st.info("📭 Você ainda não possui tickets de ajuda.")
        return
    
    for ticket in tickets:
        with st.expander(f"#{ticket['id']:06d} - {ticket['assunto']} ({ticket['status']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {ticket['status']}")
                st.write(f"**Prioridade:** {ticket.get('prioridade', 'Normal')}")
            
            with col2:
                data_criacao = parse_data(ticket['data_criacao'])
                st.write(f"**Criado em:** {data_criacao.strftime('%d/%m/%Y')}")
                if ticket['data_resposta']:
                    data_resposta = parse_data(ticket['data_resposta'])
                    st.write(f"**Respondido em:** {data_resposta.strftime('%d/%m/%Y')}")
            
            with col3:
                st.write(f"**Unidade:** {ticket['unidade'] or 'Não informado'}")
            if ticket['arquivo_nome']:
                st.write(f"**Anexo:** {ticket['arquivo_nome']}")
                # Buscar dados do arquivo no banco
                arquivo_dados = db.obter_arquivo_ticket(ticket['id'])  # Você precisa implementar este método
                exibir_arquivo_ticket(arquivo_dados, ticket['arquivo_nome'], ticket['id'])
            
            st.markdown("**Mensagem:**")
            st.write(ticket['mensagem'])
            
            if ticket['resposta']:
                st.markdown("**Resposta da equipe:**")
                st.success(ticket['resposta'])
                st.write(f"*Respondido por: {ticket['respondido_por']}*")

def exibir_arquivo_ticket(arquivo_dados, arquivo_nome, id):
    """Exibe arquivo do ticket - imagem inline ou botão download"""
    if not arquivo_dados or not arquivo_nome:
        return
    
    extensao = arquivo_nome.split('.')[-1].lower()
    
    # Exibir preview para imagens
    if extensao in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
        try:
            image = Image.open(BytesIO(arquivo_dados))
            st.image(image, caption=arquivo_nome, width=300)
        except Exception as e:
            st.error(f"Erro ao exibir imagem: {e}")
    else:
        # Para outros tipos, apenas mostrar info
        st.info(f"📄 Arquivo: {arquivo_nome} ({extensao.upper()})")
    
    # Sempre mostrar botão de download
    # Se arquivo_dados é um memoryview, converta para bytes:
    arquivo_dados_bytes = bytes(arquivo_dados)

    st.download_button(
        label=f"📥 Baixar {arquivo_nome}",
        data=arquivo_dados_bytes,  # Use os dados convertidos
        file_name=arquivo_nome,
        mime="application/octet-stream",
        key=hash(arquivo_dados_bytes)  # Também use os dados convertidos no hash
    )
    # O hash(objeto) em Python é uma função que transforma um objeto (por exemplo, uma string, um número, ou no seu caso, um arquivo armazenado como bytes) em um número inteiro "resumido" que representa o conteúdo desse objeto
    


