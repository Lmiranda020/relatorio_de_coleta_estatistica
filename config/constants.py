import streamlit as st
import pandas as pd
import base64
from io import BytesIO
import os

# ========== ARQUIVOS LOCAIS (podem subir pro Git) ==========
DEPARA_UNIDADES = "data/formularios X unidades.xlsx"
FORM_DIR = "formularios"
DEPARA_EXCEL = "data/DE - PARA (RPA X KPIH).xlsx"
CAMINHO_BASE_AGUA = "data/base_calculo_agua.xlsx"
DEPARA_PONDERACAO = "data/DE - PARA (ponderação).xlsx"
DEPARA_CRITICIDADE = "data/Centro de custo por criticidade.xlsx"
DEPARA_EXCEL_PRODUTO = "data/DE - PARA (produto).xlsx"

# ========== VARIÁVEIS DE CACHE GLOBAL ==========
_TOKEN_IMPORTACAO_CACHE = None
_TOKEN_EXPORTACAO_CACHE = None

# ========== FUNÇÕES DE CARREGAMENTO DE TOKENS ==========

def carregar_tokens_importacao():
    """
    Carrega o arquivo de tokens para IMPORTAÇÃO dos Secrets do Streamlit.
    Em produção (Streamlit Cloud): lê do st.secrets
    Em desenvolvimento local: lê do arquivo Excel normal
    
    Usa cache global para evitar múltiplas leituras
    """
    global _TOKEN_IMPORTACAO_CACHE
    
    # Se já foi carregado, retorna do cache
    if _TOKEN_IMPORTACAO_CACHE is not None:
        return _TOKEN_IMPORTACAO_CACHE
    
    try:
        # Tenta carregar dos secrets (Streamlit Cloud)
        if "tokens" in st.secrets and "excel_tokens_importacao_base64" in st.secrets["tokens"]:
            excel_base64 = st.secrets["tokens"]["excel_tokens_importacao_base64"]
            excel_bytes = base64.b64decode(excel_base64)
            df = pd.read_excel(BytesIO(excel_bytes))
            
            # Armazena no cache
            _TOKEN_IMPORTACAO_CACHE = df
            return df
            
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar tokens de importação dos Secrets: {e}")
    
    # Fallback para arquivo local (desenvolvimento)
    try:
        caminho_local = "data/unidades_tokens_cejam.xlsx"
        if os.path.exists(caminho_local):
            df = pd.read_excel(caminho_local)
            _TOKEN_IMPORTACAO_CACHE = df
            return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo local de importação: {e}")
    
    # Se nenhuma opção funcionou, retornar DataFrame vazio
    st.error("❌ CRÍTICO: Não foi possível carregar tokens de importação de nenhuma fonte!")
    _TOKEN_IMPORTACAO_CACHE = pd.DataFrame()
    return _TOKEN_IMPORTACAO_CACHE


def carregar_tokens_exportacao():
    """
    Carrega o arquivo de tokens para EXPORTAÇÃO dos Secrets do Streamlit.
    Em produção (Streamlit Cloud): lê do st.secrets
    Em desenvolvimento local: lê do arquivo Excel normal
    
    Usa cache global para evitar múltiplas leituras
    """
    global _TOKEN_EXPORTACAO_CACHE
    
    # Se já foi carregado, retorna do cache
    if _TOKEN_EXPORTACAO_CACHE is not None:
        return _TOKEN_EXPORTACAO_CACHE
    
    try:
        # Tenta carregar dos secrets (Streamlit Cloud)
        if "tokens" in st.secrets and "excel_tokens_exportacao_base64" in st.secrets["tokens"]:
            excel_base64 = st.secrets["tokens"]["excel_tokens_exportacao_base64"]
            excel_bytes = base64.b64decode(excel_base64)
            df = pd.read_excel(BytesIO(excel_bytes))
            
            # Armazena no cache
            _TOKEN_EXPORTACAO_CACHE = df
            return df
            
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar tokens de exportação dos Secrets: {e}")
    
    # Fallback para arquivo local (desenvolvimento)
    try:
        caminho_local = "data/unidades_tokens_cejam_exportacao.xlsx"
        if os.path.exists(caminho_local):
            df = pd.read_excel(caminho_local)
            _TOKEN_EXPORTACAO_CACHE = df
            return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo local de exportação: {e}")
    
    # Se nenhuma opção funcionou, retornar DataFrame vazio
    st.error("❌ CRÍTICO: Não foi possível carregar tokens de exportação de nenhuma fonte!")
    _TOKEN_EXPORTACAO_CACHE = pd.DataFrame()
    return _TOKEN_EXPORTACAO_CACHE


# ========== FUNÇÕES AUXILIARES PARA COMPATIBILIDADE ==========

def get_token_unidades_importacao(id_unidade=None):
    """
    Retorna o token de importação de uma unidade específica.
    Se id_unidade for None, retorna o DataFrame completo (compatibilidade).
    
    Args:
        id_unidade: ID da unidade (opcional)
    
    Returns:
        str: Token da unidade (se id_unidade fornecido)
        DataFrame: Todos os tokens (se id_unidade for None)
    """
    df = carregar_tokens_importacao()
    
    # Se não passar ID, retorna o DataFrame completo (compatibilidade com código antigo)
    if id_unidade is None:
        return df
    
    # Filtra pelo ID da unidade
    try:
        token_row = df[df['id'] == id_unidade]
        
        if token_row.empty:
            st.error(f"❌ Token não encontrado para unidade ID: {id_unidade}")
            return None
        
        token = token_row.iloc[0]['token']
        
        if pd.isna(token) or str(token).strip() == "":
            st.error(f"❌ Token vazio para unidade ID: {id_unidade}")
            return None
        
        return str(token).strip()
        
    except KeyError as e:
        st.error(f"❌ Coluna não encontrada no Excel: {e}")
        st.info("💡 Verifique se as colunas 'id' e 'token' existem no arquivo")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao buscar token: {e}")
        return None


def get_token_unidades_exportacao(id_unidade=None):
    """
    Retorna o token de exportação de uma unidade específica.
    Se id_unidade for None, retorna o DataFrame completo (compatibilidade).
    
    Args:
        id_unidade: ID da unidade (opcional)
    
    Returns:
        str: Token da unidade (se id_unidade fornecido)
        DataFrame: Todos os tokens (se id_unidade for None)
    """
    df = carregar_tokens_exportacao()
    
    # Se não passar ID, retorna o DataFrame completo (compatibilidade com código antigo)
    if id_unidade is None:
        return df
    
    # Filtra pelo ID da unidade
    try:
        token_row = df[df['id'] == id_unidade]
        
        if token_row.empty:
            st.error(f"❌ Token não encontrado para unidade ID: {id_unidade}")
            return None
        
        token = token_row.iloc[0]['token']
        
        if pd.isna(token) or str(token).strip() == "":
            st.error(f"❌ Token vazio para unidade ID: {id_unidade}")
            return None
        
        return str(token).strip()
        
    except KeyError as e:
        st.error(f"❌ Coluna não encontrada no Excel: {e}")
        st.info("💡 Verifique se as colunas 'id' e 'token' existem no arquivo")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao buscar token: {e}")
        return None


# ========== CREDENCIAIS DO GOOGLE (dos Secrets) ==========

def obter_credenciais_email():
    """
    Obtém as credenciais de e-mail dos Secrets do Streamlit.
    """
    try:
        if "email_credentials" in st.secrets:
            creds = st.secrets["email_credentials"]
            return {
                "user": creds.get("EMAIL_USER", ""),
                "password": creds.get("EMAIL_PASSWORD", ""),
                "host": creds.get("EMAIL_HOST", "smtp.gmail.com"),
                "port": int(creds.get("EMAIL_PORT", 587))
            }
        else:
            st.error("❌ Credenciais de e-mail não configuradas nos Secrets")
            return None
    except Exception as e:
        st.error(f"❌ Erro ao obter credenciais: {e}")
        return None


# ========== LISTAS E CONFIGURAÇÕES ==========

competencias = [
    "jan/2025", "fev/2025", "mar/2025", "abr/2025",
    "mai/2025", "jun/2025", "jul/2025", "ago/2025",
    "set/2025", "out/2025", "nov/2025", "dez/2025",
    "jan/2026", "fev/2026", "mar/2026", "abr/2026",
    "mai/2026", "jun/2026", "jul/2026", "ago/2026",
    "set/2026", "out/2026", "nov/2026", "dez/2026"
]

# ========== CAMINHOS DAS IMAGENS ==========
imagem_cejam = "assets/logo cejam.png"
imagem_sus = "assets/logo sus.png"


# ========== DEBUG: Mostrar status de carregamento ==========

def debug_secrets():
    """
    Função auxiliar para debugar o carregamento dos secrets
    """
    with st.expander("🔍 Debug: Status dos Secrets"):
        st.write("**Secrets disponíveis:**")
        try:
            secrets_disponiveis = list(st.secrets.keys())
            st.json(secrets_disponiveis)
            
            st.write("\n**Status dos DataFrames:**")
            
            # Testa importação
            df_imp = carregar_tokens_importacao()
            st.write(f"- Tokens Importação: {len(df_imp)} linhas")
            if not df_imp.empty:
                st.write(f"  - Colunas: {list(df_imp.columns)}")
            
            # Testa exportação
            df_exp = carregar_tokens_exportacao()
            st.write(f"- Tokens Exportação: {len(df_exp)} linhas")
            if not df_exp.empty:
                st.write(f"  - Colunas: {list(df_exp.columns)}")
                
        except Exception as e:
            st.error(f"Erro ao debugar: {e}")
            import traceback
            st.code(traceback.format_exc())