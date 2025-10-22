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
from components.modal_gerenciar_usuarios import modal_gerenciar_usuarios
from utils.dashboard_functions import mostrar_dashboard_preenchimentos, mostrar_relatorio_unidades

def parse_data(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    except:
        return data_str  # caso já seja datetime ou vazio

def exibir_arquivo_ticket(arquivo_dados, arquivo_nome, id):
    """Exibe arquivo do ticket - imagem online ou botão download"""
    if not arquivo_dados or not arquivo_nome:
        return
    
    # Converte memoryview para bytes se necessário
    if isinstance(arquivo_dados, memoryview):
        arquivo_dados = bytes(arquivo_dados)
    
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
    st.download_button(
        label=f"📥 Baixar {arquivo_nome}",
        data=arquivo_dados,
        file_name=arquivo_nome,
        mime="application/octet-stream",
        key=f"download_{id}_{arquivo_nome}"
    )
    # O hash(objeto) em Python é uma função que transforma um objeto (por exemplo, uma string, um número, ou no seu caso, um arquivo armazenado como bytes) em um número inteiro "resumido" que representa o conteúdo desse objeto


def mostrar_painel_suporte():
    """Painel para equipe de suporte gerenciar tickets"""
    st.title("🛠️ Painel de Suporte Relatório de Coleta - CEJAM")
    
    tab1, tab2, tab3, aba_usuarios, aba_feedbacks = st.tabs(["🎫 Tickets", "📊 Relatórios", "📃Preenchimento unidades", "👥 Gerenciar Usuários", "⭐ Feedbacks"])
    
    with tab1:
        db = DatabaseManagerPostgres()
        #db = DatabaseManagerPostgres() cria a instância da classe
        # Automaticamente, o método __init__ roda.
        # Dentro do __init__,  definiu self.DB_CONFIG = ....
        # Ou seja, a instância db ganhou o atributo DB_CONFIG, que agora pertence a ela.
        
        # Filtros
        #crio tres colunas
        col1, col2, col3 = st.columns(3)
        with col1: # com a coluna 1 crio um select box, que o valor selecionado será armazenado na variavel status_filter
            status_filter = st.selectbox("Status", ["Todos", "Aberto", "Em Andamento", "Respondido", "Fechado"])
        with col2: # com a coluna 2 crio um botão atualizar, que recarrega a pagina se clicado
            if st.button("🔄 Atualizar"):
                st.rerun()
        
        # Listar tickets
        status = None if status_filter == "Todos" else status_filter # se o status é todos eu retorno None se não eu retorno o status escolhido para a variavel
        tickets = db.listar_tickets(status=status)
        # Quando  chama db.listar_tickets(...), o método recebe self como referência para a instância db.
        # Isso significa que dentro do método consegue acessar self.DB_CONFIG, ou seja, os dados que estão armazenados na instância.
        
        for ticket in tickets:
            with st.container():
                st.markdown("---")
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**#{ticket['id']:06d}** - {ticket['assunto']}")
                    st.write(f"👤 {ticket['nome']} ({ticket['email']})")
                
                with col2:
                    st.write(f"**Status:** {ticket['status']}")
                    data_criacao = parse_data(ticket['data_criacao'])
                    st.write(f"📅 {data_criacao.strftime('%d/%m/%Y')}")
                
                with col3:
                    if ticket['status'] == "Fechado":
                        st.markdown("🔒 Este ticket está fechado e não pode mais ser editado.")
                    else:
                        # Lista de status disponíveis
                        status_opcoes = ["Aberto", "Em Andamento", "Respondido", "Fechado"]
                        
                        # Verifica se o ticket tem um status válido
                        status_atual = ticket.get('status', 'Aberto')  # Default para 'Aberto' se não existir
                        
                        # Determina o índice atual de forma segura
                        if status_atual in status_opcoes:
                            indice_atual = status_opcoes.index(status_atual)
                        else:
                            indice_atual = 0  # Default para primeiro item (Aberto)
                            st.warning(f"⚠️ Status '{status_atual}' não reconhecido. Usando 'Aberto' como padrão.")
                        
                        # Alterar status
                        novo_status = st.selectbox(
                            "Alterar status", 
                            status_opcoes,
                            index=indice_atual,
                            key=f"status_{ticket['id']}"
                        )
                        
                        # Lógica de atualização
                        if novo_status != status_atual:
                            if st.button("Atualizar", key=f"btn_{ticket['id']}"):
                                sucesso_update = db.atualizar_status_ticket(ticket['id'], novo_status, "Suporte")
                                if sucesso_update:
                                    st.success("Status atualizado!")
                                    
                                    # Enviar email se fechou agora
                                    if novo_status == "Fechado" and status_atual != "Fechado":
                                        assunto = "Seu ticket foi fechado"
                                        corpo = f"Olá {ticket['nome']},\n\nSeu ticket #{ticket['id']:06d} foi fechado.\n\nObrigado."
                                        enviado = enviar_email(ticket['email'], assunto, corpo)
                                        if enviado:
                                            st.success("E-mail de fechamento enviado ao usuário.")
                                        else:
                                            st.error("Falha ao enviar o e-mail de fechamento.")
                                    
                                    st.rerun()
                
                with col4:
                    if st.button("👁️ Ver", key=f"ver_{ticket['id']}"):
                        st.session_state[f'show_ticket_{ticket["id"]}'] = True
                
                # Mostrar detalhes se solicitado
                if st.session_state.get(f'show_ticket_{ticket["id"]}', False):
                    with st.expander("📝 Detalhes do Ticket", expanded=True):
                        st.write(f"**Mensagem:** {ticket['mensagem']}")
                        
                        if ticket['arquivo_nome']:
                            st.write(f"**Anexo:** {ticket['arquivo_nome']}")
                            # Buscar dados do arquivo no banco
                            arquivo_dados = db.obter_arquivo_ticket(ticket['id'])
                            exibir_arquivo_ticket(arquivo_dados, ticket['arquivo_nome'], ticket['id'])
                        
                        # ===== NOVA LÓGICA PARA TICKETS FECHADOS =====
                        if ticket['status'] == "Fechado":
                            # Se o ticket está fechado, APENAS mostra a resposta (não permite responder)
                            st.markdown("---")
                            st.markdown("### 🔒 Ticket Fechado - Resposta Final")
                            
                            if ticket.get('resposta') and ticket.get('respondido_por'):
                                # Mostra a resposta em um container destacado
                                with st.container():
                                    st.success("✅ **Resposta enviada:**")
                                    st.write(ticket['resposta'])
                                    
                                    # Mostra informações sobre quem e quando respondeu
                                    col_resp1, col_resp2 = st.columns(2)
                                    with col_resp1:
                                        st.info(f"👤 **Respondido por:** {ticket['respondido_por']}")
                                    with col_resp2:
                                        if ticket.get('data_resposta'):
                                            data_resposta = parse_data(ticket['data_resposta'])
                                            if isinstance(data_resposta, datetime):
                                                st.info(f"📅 **Data:** {data_resposta.strftime('%d/%m/%Y às %H:%M')}")
                                            else:
                                                st.info(f"📅 **Data:** {data_resposta}")
                            else:
                                st.warning("⚠️ Este ticket foi fechado sem resposta registrada.")
                                
                        else:
                            # Se o ticket NÃO está fechado, mostra o formulário de resposta
                            st.markdown("---")
                            
                            # Primeiro, verifica se já tem uma resposta prévia
                            if ticket.get('resposta') and ticket.get('respondido_por'):
                                st.markdown("### 📋 Resposta Anterior")
                                with st.container():
                                    st.info("ℹ️ **Resposta já enviada anteriormente:**")
                                    st.write(ticket['resposta'])
                                    
                                    col_prev1, col_prev2 = st.columns(2)
                                    with col_prev1:
                                        st.write(f"👤 **Por:** {ticket['respondido_por']}")
                                    with col_prev2:
                                        if ticket.get('data_resposta'):
                                            data_resposta = parse_data(ticket['data_resposta'])
                                            if isinstance(data_resposta, datetime):
                                                st.write(f"📅 {data_resposta.strftime('%d/%m/%Y às %H:%M')}")
                                st.markdown("### ✏️ Nova Resposta/Atualização")
                            else:
                                st.markdown("### 📤 Responder Ticket")
                            
                            # Formulário para responder (só aparece se NÃO estiver fechado)
                            with st.form(f"resposta_{ticket['id']}"):
                                resposta = st.text_area("Resposta:", height=100)
                                respondido_por = st.text_input("Seu nome:", value="Equipe de Suporte")
                                
                                col_form1, col_form2 = st.columns([1, 1])
                                with col_form1:
                                    enviar_resposta = st.form_submit_button("📤 Enviar Resposta")
                                with col_form2:
                                    fechar_com_resposta = st.form_submit_button("🔒 Responder e Fechar")
                                
                                if enviar_resposta or fechar_com_resposta:
                                    if resposta and respondido_por:
                                        # Adiciona a resposta
                                        if db.adicionar_resposta(ticket['id'], resposta, respondido_por):
                                            st.success("✅ Resposta enviada!")
                                            
                                            # Se escolheu "Responder e Fechar", fecha o ticket também
                                            if fechar_com_resposta:
                                                db.atualizar_status_ticket(ticket['id'], "Fechado", respondido_por)
                                                st.success("🔒 Ticket fechado!")
                                                
                                                # Enviar email de fechamento
                                                assunto = "Seu ticket foi respondido e fechado"
                                                corpo = f"""Olá {ticket['nome']},

                Seu ticket #{ticket['id']:06d} foi respondido e fechado.

                Resposta:
                {resposta}

                Respondido por: {respondido_por}

                Obrigado por usar nosso sistema de suporte."""
                                                
                                                enviado = enviar_email(ticket['email'], assunto, corpo)
                                                if enviado:
                                                    st.success("📧 E-mail enviado ao usuário.")
                                                else:
                                                    st.error("❌ Falha ao enviar e-mail.")
                                            
                                            st.rerun()
                                    else:
                                        st.error("❌ Preencha todos os campos")
                        
                        if st.button("❌ Fechar detalhes", key=f"close_{ticket['id']}"):
                            st.session_state[f'show_ticket_{ticket["id"]}'] = False
                            st.rerun()

    
    with tab2:
        # Aqui adicionar gráficos e estatísticas dos tickets
        mostrar_dashboard_preenchimentos()
    with tab3:
        #aqui adicionar alguma forma de ver o que falta preencher das unidades
        mostrar_relatorio_unidades()
    with aba_usuarios:
        # Novo: gerenciamento de usuários
        modal_gerenciar_usuarios()

    with aba_feedbacks:
        from utils.painel_feedbacks import mostrar_painel_feedbacks
        mostrar_painel_feedbacks()