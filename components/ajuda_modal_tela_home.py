import streamlit as st
from data.manager_postgre import DatabaseManagerPostgres
import time
from utils.email_utils import enviar_email

# Inicializa estado
if "abrir_card" not in st.session_state:
    st.session_state.abrir_card = False
if "mostrar_botao_ajuda" not in st.session_state:
    st.session_state.mostrar_botao_ajuda = True

# Inicializa estado do modal
if "abrir_modal_ajuda" not in st.session_state:
    st.session_state.abrir_modal_ajuda = False

@st.dialog("💬 Central de Ajuda")
def modal_ajuda():
    """Modal de ajuda usando st.dialog nativo do Streamlit"""
    st.markdown("### Entre em contato conosco")
    st.markdown("Descreva seu problema e nossa equipe entrará em contato.")
    
    with st.form("form_ajuda"):
        nome = st.text_input("Nome completo *", placeholder="Seu nome")
        email = st.text_input("E-mail *", placeholder="seu.email@cejam.org.br")
        unidade = st.text_input("Unidade/Setor", placeholder="Departamento ou setor")
        assunto = st.text_input("Assunto *", placeholder="Resumo do problema")
        
        mensagem = st.text_area(
            "Descreva o problema *",
            placeholder="Descreva detalhadamente o que aconteceu...",
            height=100
        )
        
        arquivo = st.file_uploader(
            "📎 Anexar arquivo (opcional)",
            type=["png", "jpg", "jpeg", "pdf", "xlsx", "docx", "txt"]
        )
        
        st.markdown("*Campos obrigatórios")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            enviado = st.form_submit_button("📤 Enviar", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state.abrir_modal_ajuda = False
                st.rerun()
        
        if enviado:
            # Validações
            if not all([nome.strip(), email.strip(), assunto.strip(), mensagem.strip()]):
                st.error("❌ Preencha todos os campos obrigatórios")
                return
            
            if "@" not in email or "." not in email.split("@")[-1]:
                st.error("❌ Digite um e-mail válido")
                return
            
            try:
                with st.spinner("Criando ticket..."):
                    # Inicializa o banco de dados
                    db = DatabaseManagerPostgres()
                    
                    # Testa a conexão
                    if not db.testar_conexao():
                        st.error("❌ Erro na conexão com o banco de dados")
                        return
                    
                    # Cria o ticket no banco
                    ticket_id = db.criar_ticket(
                        nome=nome,
                        email=email,
                        unidade=unidade,
                        assunto=assunto,
                        mensagem=mensagem,
                        arquivo=arquivo
                    )
                    
                    if ticket_id:
                        st.success(f"✅ Ticket #{ticket_id:06d} criado com sucesso!")
                        
                        # Enviar e-mail
                        try:
                            corpo_email = f"""
Novo ticket de suporte criado:

Ticket ID: #{ticket_id:06d}
Nome: {nome}
E-mail: {email}
Unidade: {unidade or 'Não informado'}
Assunto: {assunto}

Mensagem:
{mensagem}

{f'Anexo: {arquivo.name}' if arquivo else 'Sem anexos'}

---
Sistema de Relatórios - Central de Ajuda
                            """
                            
                            sucesso_email = enviar_email(
                                "custos@cejam.org.br", 
                                f"Ticket #{ticket_id:06d}: {assunto}", 
                                corpo_email
                            )
                            
                            if sucesso_email:
                                st.success("📧 E-mail enviado para a equipe de suporte!")
                            else:
                                st.warning("⚠️ Ticket criado, mas houve problema no envio do e-mail")
                        
                        except Exception as e:
                            st.warning(f"⚠️ Ticket criado, mas houve problema no e-mail: {str(e)}")
                        
                        time.sleep(4)
                        st.session_state.abrir_modal_ajuda = False
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar ticket no banco de dados")
            
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                print(f"Erro detalhado: {e}")  # Para debug no console

def adicionar_botao_ajuda_sidebar():
    """Adiciona o botão de ajuda na sidebar existente"""
    with st.sidebar:
        # Adiciona uma seção de ajuda no final da sidebar
        st.markdown("---")
        st.markdown("### 🆘 Precisa de Ajuda?")
        
        if st.button("❓ Abrir Central de Ajuda", use_container_width=True, key="btn_ajuda_sidebar"):
            st.session_state.abrir_modal_ajuda = True
        
        st.caption("📞 Relate problemas, dúvidas ou sugestões")


# Controla o fechamento do modal (incluindo o X)
if st.session_state.abrir_modal_ajuda:
    modal_ajuda()
    # Reseta o estado após o modal ser renderizado
    st.session_state.abrir_modal_ajuda = False