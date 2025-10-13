"""
Funções para manipulação de arquivos e pastas
"""
import os
import streamlit as st

# Função para obter o caminho do desktop do usuário
def get_desktop_path():
    """
    Retorna o caminho do desktop do usuário atual
    """
    try:
        # Windows
        if os.name == 'nt': # verifica se o sistema é Windows, name é um atributo do módulo os que retorna o nome do sistema operacional
            #se o sistema operacional for Windows, o caminho do desktop é obtido com a função os.path.join, 
            # que junta o caminho do usuário com a pasta Desktop
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            # pah -> é um submodulo do módulo os que fornece funções para manipular caminhos de arquivos e diretórios
            # então essa primeira parte eu quero fazer algo com o caminho, ou seja, fazer um join
            # e expanduser é uma função do módulo os que retorna o caminho do diretório home do usuário atual
            # o ~ é um atalho que representa o diretório home do usuário, ou seja, o diretório pessoal do usuário atual
            # o ~ é uma convenção do sistema operacional que indica o diretório home do usuário atual
            # o expanduser é quem interpreta o ~ e retorna o caminho completo do diretório home do usuário

        # macOS e Linux
        else:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        #Valor	Significado
        #'nt'	Windows (NT = Windows NT)
        #'posix'	Linux, macOS, Unix, etc.
        #'java'	JVM (Jython)
        
        # Verifica se o diretório existe
        if not os.path.exists(desktop): # para verificar se existe o caminho do desktop, se não existir, ele tenta alternativas
            # Tenta alternativas para Linux
            desktop = os.path.join(os.path.expanduser('~'), 'Área de Trabalho') # a diferença é que eu faço um join agora com o nome "Aréa de Trabalho"
            if not os.path.exists(desktop): # mesmo assim, se não existir, ele tenta outra alternativa
                desktop = os.path.expanduser('~')  # traz o nome do diretorio home, sem o join
        
        return desktop # por fim, retorna o caminho do desktop ou do home
    except Exception as e: # se der error, ele captura a exceção e mostra uma mensagem de erro
        st.error(f"Erro ao obter caminho do desktop: {str(e)}")
        return os.path.expanduser('~')  # se der erro, retorna o caminho do diretório home do usuário