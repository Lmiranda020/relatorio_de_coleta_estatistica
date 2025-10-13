import streamlit as st
import time
from utils.email_utils import enviar_email
from data.manager_postgre import DatabaseManagerPostgres


@st.dialog("💬 Precisa de Ajuda?") # titulo de modal
def modal_ajuda_login(): # cria uma função para o modal
    """Modal de ajuda específico para a tela de login"""
    st.markdown("### Como podemos ajudar?")
    st.markdown("Selecione o tipo de problema que você está enfrentando:")
    
    # Opções rápidas para problemas comuns de login
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Problemas de Login", use_container_width=True):
            st.session_state.tipo_problema_login = "login"
            
    
    # with col2:
    #     if st.button("📧 Esqueci minha Senha", use_container_width=True):
    #         # st.session_state.tipo_problema_login = "senha" # tirei essa parte para não habitar o modal padrão e sim o de recuperação de senha 
    #         st.session_state.tipo_problema_login = None  # limpa para não abrir o formulário
    #         st.session_state.modal_recuperar_senha = True
    #         st.rerun()
            
    # col3, col4 = st.columns(2)
    
    with col2:
        if st.button("👤 Cadastro/Acesso", use_container_width=True):
            st.session_state.tipo_problema_login = "cadastro"
    
    # with col4:
    if st.button("❓ Outro Problema", use_container_width=True):
        st.session_state.tipo_problema_login = "outro"

    # Formulário baseado no tipo selecionado
    if st.session_state.get('tipo_problema_login'): # vair pegar o que ele selecionar da memoria do streamlit usando a chave "tipo_problema_login"
        st.markdown("---")
        
        tipo = st.session_state.tipo_problema_login # armazeno em uma variavel
        
        # Títulos e mensagens personalizadas por tipo
        if tipo == "login": # se selcionado login aparece o markdown abaixo mais a informação
            st.markdown("#### 🔐 Problemas de Login")
            st.info("Descreva qual erro aparece quando tenta fazer login.")
        elif tipo == "senha":
            st.markdown("#### 📧 Recuperação de Senha")
            st.info("Informe seu e-mail para que possamos ajudar com a recuperação.")
        elif tipo == "cadastro":
            st.markdown("#### 👤 Solicitação de Acesso")
            st.info("Solicite criação de conta ou liberação de acesso.")
        else:
            st.markdown("#### ❓ Outro Problema")
            st.info("Descreva seu problema e nossa equipe entrará em contato.")
        
        with st.form("form_ajuda_login"): # cria um formulario com dois inputs iniciais nome e email
            nome = st.text_input("Nome completo *", placeholder="Seu nome")
            email = st.text_input("E-mail *", placeholder="seu.email@cejam.org.br")
            
            if tipo == "cadastro": # se o tipo foi cadastro vai habilitar mas dois inputs definidos
                unidade = st.text_input("Unidade/Setor *", placeholder="Em qual departamento você trabalha?")
                cargo = st.text_input("Cargo/Função", placeholder="Sua função na empresa")
            else: # nos outros três casos habilita esse input
                unidade = st.text_input("Unidade/Setor", placeholder="Departamento ou setor (opcional)")
                cargo = None # não será necessário para as demais opções
            
            # Mensagem pré-definida baseada no tipo
            if tipo == "login":
                mensagem_inicial = "Estou tendo problemas para fazer login no sistema. O erro que aparece é: "
            # elif tipo == "senha":
            #     mensagem_inicial = "Esqueci minha senha e preciso de ajuda para recuperar o acesso ao sistema."
            elif tipo == "cadastro":
                mensagem_inicial = "Preciso de acesso ao sistema. Trabalho na unidade mencionada acima e gostaria de solicitar a criação da minha conta."
            else:
                mensagem_inicial = ""
            
            mensagem = st.text_area( # crio uma are de texto, é como se fosse um input
                "Descreva o problema *", # titulo
                value=mensagem_inicial, # mensagem padrão já definida para ajudar
                placeholder="Detalhe seu problema...", # mensagem clara que aparece
                height=100 # tamanho
            )
            
            arquivo = None # defino primeiro a variavel arquivo como none
            if tipo in ["login", "outro"]: # se o tipo escolhido foi login ou outro será habilitado essa caixa
                arquivo = st.file_uploader( # metodo file_uploadre para carregar arquivos
                    "📎 Anexar print do erro (opcional)",
                    type=["png", "jpg", "jpeg", "pdf"]
                )
            
            st.markdown("*Campos obrigatórios") # cria um texto para
            
            col1, col2, col3 = st.columns([1, 1, 1]) # cria três colunas
            
            with col1:
                enviado = st.form_submit_button("📤 Enviar Solicitação", type="primary", use_container_width=True)
                # type="primary" = botão de destaque (cor azul por padrão)
            with col2:
                if st.form_submit_button("🔄 Limpar", use_container_width=True):
                    st.session_state.tipo_problema_login = None
                    st.rerun() # cria outro botão e se clicado tipo_de_problema vira None na memoria do streamlit e recarrega a pagina
                    # não está limapando

            with col3:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.tipo_problema_login = None
                    st.rerun()
            
            if enviado: # se clicar no botão enviar, vai retorna true e entra nessa condição
                # Validações específicas
                campos_obrigatorios = [nome.strip(), email.strip(), mensagem.strip()] # cria uma lista com as infmações do modal
                if tipo == "cadastro": # se o tipo escolhido foi cadastro
                    campos_obrigatorios.append(unidade.strip()) # ega a informação da unidade e adiciona na lista de campos obrigatorios
                
                if not all(campos_obrigatorios): # Se algum campo obrigatório estiver vazio, mostre erro e pare o processamento
                    st.error("❌ Preencha todos os campos obrigatórios")
                    return
                
                if "@" not in email or "." not in email.split("@")[-1]:
                    st.error("❌ Digite um e-mail válido")
                    #Se não tiver @ no email OU Se na parte depois do @ não tiver um ponto. Então o email é considerado inválido.
                    return
                
                try: # ele tenta..
                    with st.spinner("Enviando solicitação..."): # exibe uma animação de carregamento (spinner) na tela, junto com uma mensagem personalizada
                        # Definir assunto baseado no tipo
                        assuntos = {
                            "login": "Problema de Login",
                            "senha": "Recuperação de Senha",
                            "cadastro": "Solicitação de Acesso",
                            "outro": "Suporte - Tela de Login"
                        } # cria um dicionário com a chave e o valor para saber o assunto
                        
                        assunto = assuntos.get(tipo, "Suporte") # eu pego o tipo escolhido e busco no dicionario o valor que corresponde ao valor di tipo, caso não encontre traz o valor padrçao "Suporte"
                        
                        # Inicializa o banco de dados
                        db = DatabaseManagerPostgres()
                        
                        # Testa a conexão
                        if not db.testar_conexao():
                            st.error("❌ Erro na conexão com o banco de dados. Tentando enviar apenas por e-mail...")
                            ticket_id = None
                        else:
                            # Cria o ticket no banco
                            ticket_id = db.criar_ticket(
                                nome=nome,
                                email=email,
                                unidade=unidade,
                                assunto=assunto,
                                mensagem=mensagem,
                                arquivo=arquivo
                            )
                        
                        # Corpo do e-mail
                        if ticket_id:
                            titulo_email = f"Ticket #{ticket_id:06d}: {assunto} - {nome}"
                        else:
                            titulo_email = f"{assunto} - {nome}"
                        
                        corpo_email = f"""
SOLICITAÇÃO DE SUPORTE - TELA DE LOGIN

{f'Ticket ID: #{ticket_id:06d}' if ticket_id else '### Ticket não salvo no banco (apenas e-mail)'}
Tipo: {assunto}
Nome: {nome}
E-mail: {email}
Unidade: {unidade or 'Não informado'}
{f'Cargo: {cargo}' if cargo else ''}

Mensagem:
{mensagem}

{f'Anexo: {arquivo.name}' if arquivo else 'Sem anexos'}

---
Enviado da tela de login do Sistema de Relatórios
                        """
                        
                        # Enviar e-mail
                        sucesso_email = enviar_email("custos@cejam.org.br", titulo_email, corpo_email)
                        
                        if ticket_id and sucesso_email:
                            st.success(f"✅ Ticket #{ticket_id:06d} criado e e-mail enviado com sucesso!")
                        elif ticket_id:
                            st.success(f"✅ Ticket #{ticket_id:06d} criado com sucesso!")
                            st.warning("⚠️ Houve problema no envio do e-mail, mas o ticket foi salvo.")
                        elif sucesso_email:
                            st.success("✅ Solicitação enviada por e-mail com sucesso!")
                            st.warning("⚠️ Não foi possível salvar no banco, mas o e-mail foi enviado.")
                        else:
                            st.error("❌ Erro no envio. Tente novamente ou entre em contato por email custos@cejam.org.br .")
                            return
                        
                        if tipo == "cadastro":
                            st.info("👤 Sua solicitação de acesso foi encaminhada para análise.")
                        else:
                            st.info("🕐 Nossa equipe técnica entrará em contato em breve, caso seja necessário. "
                                    "Você também poderá acompanhar o status da sua solicitação na aba 'Meu Ticket'.")
                        

                        time.sleep(4)
                        st.session_state.tipo_problema_login = None
                        st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")
                    print(f"Erro detalhado no login: {e}")  # Para debug no console

    # Informações de ajuda
    with st.expander("ℹ️ Informações e Ajuda"):
        st.markdown("""
        **Como funciona:**
        - Cada unidade possui um email e senha únicos
        - Após o login, você terá acesso apenas aos formulários da sua unidade
        
        **Problemas técnicos:**
        - Verifique se digitou corretamente email e senha
        - Certifique-se de que sua unidade está ativa no sistema
              👉 [Clique aqui para consultar a lista de unidades ativas](https://docs.google.com/spreadsheets/d/1LjpZXq7wdRMT3Ov-D11TWMy4a_kLFkCcBM7PBubOyAY/edit?gid=0#gid=0)
        """)

def botao_ajuda_login_simples():
    """Versão mais simples do botão de ajuda para login"""
    # Só renderiza se realmente não estiver logado
    if not st.session_state.get('usuario_logado', False):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("❓ Precisa de Ajuda?", use_container_width=True, key="ajuda_login_simples"):
                modal_ajuda_login()