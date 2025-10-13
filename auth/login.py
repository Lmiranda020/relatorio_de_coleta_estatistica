"""
Funções relacionadas à autenticação e login
"""
import streamlit as st
import pandas as pd
import time
from data.manager_postgre import DatabaseManagerPostgres
from components.modal_recuperar_senha import mostrar_tela_recuperacao


def validar_login(email, senha):
    """Valida login usando banco de dados com senhas criptografadas"""
    try:
        if not email.lower().endswith("@cejam.org.br"):
            return False, "O e-mail deve terminar com @cejam.org.br"
        
        # Usa a nova validação do banco
        db = DatabaseManagerPostgres()
        return db.validar_senha_usuario(email, senha)
        
    except Exception as e:
        return False, f"Erro ao validar login: {str(e)}"

# === TELA DE LOGIN ===
def mostrar_tela_login(): # função para mostrar a tela de login
    """
    Exibe a tela de login
    """
    # VERIFICA SE DEVE MOSTRAR TELA DE RECUPERAÇÃO PRIMEIRO
    if st.session_state.get("tela_recuperacao", False):
        from components.modal_recuperar_senha import mostrar_tela_recuperacao
        mostrar_tela_recuperacao()
        return  # Para aqui se estiver na tela de recuperação
    
    # Centraliza o formulário de login
    col1, col2, col3 = st.columns([1, 3, 1]) # crio tres colunas, onde a coluna do meio será maior que as outras duas, ou seja, a coluna do meio terá o dobro da largura das colunas laterais
    # criar três colunas apenas para centralizar visualmente o conteúdo da coluna do meio col2

    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Login do Sistema</h2>", unsafe_allow_html=True) # criar o titulo, usei html para centralizar
        st.markdown("---") # cria uma linha horizontal para separar as seções
        
        # Formulário de login
        with st.form("login_form"): # crio um formulário de login com o nome "login_form", que será usado para enviar os dados do login
            st.markdown("### Acesso ao Relatório de Coleta") # apenas um texto para o título do formulário
            
            email = st.text_input( # cria um campo de texto para o email e será armazenado na variavel email
                "📧 Email:", # titulo
                placeholder="seu.email@cejam.org.br", # texto de espaço reservado
                help="Digite seu email cadastrado" # texto de ajuda que aparece quando o usuário passa o mouse sobre o campo
            )
            
            senha = st.text_input( # cria um campo de texto para o senha e será armazenado na variavel senha
                "🔑 Senha:", # titulo
                type="password", # tipo de campo de senha, ou seja, o texto digitado será oculto
                placeholder="Digite sua senha", # texto de espaço reservado
                help="Digite a senha cadastrada para sua unidade" # texto de ajuda que aparece quando o usuário passa o mouse sobre o campo
            )

            col_btn1, col_btn2 = st.columns([1, 1]) # cria duas colunas para os botões de login e esqueci os dados

            with col_btn1:
                botao_login = st.form_submit_button("🚪 Entrar", use_container_width=True) # use_container_width=True faz o botão ocupar toda a largura da coluna

            with col_btn2:
                botao_recuperar_senha = st.form_submit_button("🔑 Recuperar Senha", use_container_width=True)
        
        if botao_recuperar_senha:
            st.session_state.tela_recuperacao = True
            st.rerun()

        # Processa o login
        if botao_login: # se true, ou seja, se o botão de login foi clicado
            if not email or not senha: # se naõ existir email ou senha, ou seja, se o usuário não preencheu os campos
                st.warning("⚠️ Por favor, preencha email e senha.") # mostra uma mensagem de aviso para o usuário preencher os campos
            else: # se não ou seja, se o usuário preencheu os campos
                with st.spinner("Validando credenciais..."):
                    sucesso, resultado = validar_login(email, senha) # chamao a função validar_login passando os parametros email e senha, e armazena o retorno nas variaveis sucesso e resultado
                    
                    if sucesso: # ou seja se true, se o email e senha estiverem corretos
                        
                        # CORREÇÃO: Verificar se é primeiro acesso
                        if resultado.startswith("PRIMEIRA_VEZ|"):
                            unidade = resultado.split("|")[1]
                            st.session_state['email_usuario'] = email
                            st.session_state['unidade_usuario'] = unidade
                            st.session_state['primeiro_acesso'] = True
                            st.session_state['usuario_logado'] = False  # IMPORTANTE: não logar ainda
                            st.session_state.modal_cadastro_senha = True 
                            st.success("✅ Login validado! Agora defina sua senha pessoal.")
                            time.sleep(1)
                            st.rerun()  # IMPORTANTE: recarrega para mostrar o modal
                            
                        else:                 
                            # Login bem-sucedido - usuário já tem senha definida
                            st.session_state['usuario_logado'] = True # define a chave usuario_logado como VERDADEIRO no session_state, ou seja, o usuário está logado
                            st.session_state['email_usuario'] = email # define a chave email_usuario como o email digitado pelo usuário no session_state, ou seja, o email do usuário que está logado
                            st.session_state['unidade_usuario'] = resultado # redefine a chave unidade_usuario como o resultado da validação do login, ou seja, a unidade do usuário que está logado
                            # LIMPAR cache antigo
                            if 'df_competencias_cache' in st.session_state:
                                del st.session_state['df_competencias_cache']
                            st.success(f"✅ Login realizado com sucesso! Bem-vindo(a) {resultado}!") # mostra uma mensagem de sucesso para o usuário informando que o login foi realizado com sucesso
                            time.sleep(2)  # Pequena pausa para mostrar a mensagem
                            st.rerun() # é um comando do Streamlit que força a aplicação a recarregar (ou seja, executar tudo de novo do topo do script).
                    else: # agora se sucesso for FALSO, ou seja, se o email e senha estiverem incorretos
                        # Login falhou
                        st.error(f"❌ Falha no login: {resultado}") # apresenta essa mensagem infomando o nome da unidade