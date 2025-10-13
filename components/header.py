"""
Componentes de interface - Header do usuário logado
"""
import streamlit as st
import time

def mostrar_header_usuario(): # cria uma função para mostrar o header do usuário logado
    """
    Mostra informações do usuário logado e botão de logout
    """
    col1, col2, col3 = st.columns([4, 2, 1]) # crio três colunas, onde a coluna da esquerda terá 4 partes, a do meio terá 2 partes e a da direita terá 1 parte, ou seja, a coluna da esquerda será maior que as outras duas
    
    with col1: # aqui nessa coluna 1, temos duas linhas
        st.markdown(f"👋 **Bem-vindo(a):** {st.session_state['email_usuario']}") # cria um texto de boas vindas e informa o email 
        st.markdown(f"📍 **Unidade:** {st.session_state['unidade_usuario']}") # cria um texto para informar a unidade 
    
    with col2: 
        st.markdown(f"📅 **Data:** {time.strftime('%d/%m/%Y')}") # aqui é um texto com a data do dia de hoje
    
    with col3: # aqui crio uma coluna com um botão de logout, para sair do sistema
        if st.button("🚪 Sair", help="Fazer logout do sistema"): # cria um botão com o texto "Sair" e adiciona uma mensagem de ajuda
            # Limpa os dados da sessão
            # e o if, é como se fosse um if do tipo "se o usuário clicar no botão Sair, então faça o que está dentro do if"
            # por padrão quando cria um botão no Streamlit, ele retorna True quando é clicado, e False quando não é clicado, ou seja o valor padrão é False
            st.session_state['usuario_logado'] = False # Marca o usuário como deslogado.
            st.session_state['email_usuario'] = None # Limpa o email do usuário, retornando None
            st.session_state['unidade_usuario'] = None # lima a unidade do usuário,  retornando None
            # Limpa também os dados dos formulários
            if 'formularios_data' in st.session_state: # se conter essa chave ne momeria, ou seja, se o usuário já tiver preenchido algum formulário
                st.session_state['formularios_data'] = {} # limpa os dados dos formulários preenchidos pelo usuário, substituindo o dicionário por um vazio
            st.success("✅ Logout realizado com sucesso!") # apareece uma mensagem de sucesso informando que o logout foi realizado com sucesso
            time.sleep(2) # faz uma pausa de 1 segundo para mostrar a mensagem de sucesso
            st.rerun() # é um comando do Streamlit que força a aplicação a recarregar, ou seja, executar tudo de novo do topo do script
            # e quando faz a leitura novamente do codigo do app
            # devido a chave usuario_logado ser false, a linha 65 (if not st.session_state['usuario_logado']: )
            # retorna True, e o usuário é redirecionado para a página de login
