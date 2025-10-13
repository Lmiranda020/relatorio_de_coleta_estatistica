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

# ========== ARQUIVOS SENSÍVEIS - Carregados dos Secrets ==========

@st.cache_data
def carregar_tokens_importacao():
    """
    Carrega o arquivo de tokens para IMPORTAÇÃO dos Secrets do Streamlit.
    Em produção (Streamlit Cloud): lê do st.secrets
    Em desenvolvimento local: lê do arquivo Excel normal
    """
    try:
        # Tenta carregar dos Secrets (produção)
        if "excel_tokens_importacao_base64" in st.secrets:
            st.info("🔐 Carregando tokens de IMPORTAÇÃO dos Secrets (Produção)")
            excel_base64 = st.secrets["excel_tokens_importacao_base64"]
            excel_bytes = base64.b64decode(excel_base64)
            df = pd.read_excel(BytesIO(excel_bytes))
            st.success(f"✅ {len(df)} tokens de importação carregados dos Secrets")
            return df
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar tokens de importação dos Secrets: {e}")
    
    # Fallback para arquivo local (desenvolvimento)
    try:
        caminho_local = "data/unidades_tokens_cejam.xlsx"
        if os.path.exists(caminho_local):
            st.info("📂 Carregando tokens de IMPORTAÇÃO do arquivo local (Desenvolvimento)")
            df = pd.read_excel(caminho_local)
            st.success(f"✅ {len(df)} tokens de importação carregados localmente")
            return df
        else:
            st.error(f"❌ Arquivo não encontrado: {caminho_local}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar tokens de importação: {e}")
        return pd.DataFrame()


@st.cache_data
def carregar_tokens_exportacao():
    """
    Carrega o arquivo de tokens para EXPORTAÇÃO dos Secrets do Streamlit.
    Em produção (Streamlit Cloud): lê do st.secrets
    Em desenvolvimento local: lê do arquivo Excel normal
    """
    try:
        # Tenta carregar dos Secrets (produção)
        if "excel_tokens_exportacao_base64" in st.secrets:
            st.info("🔐 Carregando tokens de EXPORTAÇÃO dos Secrets (Produção)")
            excel_base64 = st.secrets["excel_tokens_exportacao_base64"]
            excel_bytes = base64.b64decode(excel_base64)
            df = pd.read_excel(BytesIO(excel_bytes))
            st.success(f"✅ {len(df)} tokens de exportação carregados dos Secrets")
            return df
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar tokens de exportação dos Secrets: {e}")
    
    # Fallback para arquivo local (desenvolvimento)
    try:
        caminho_local = "data/unidades_tokens_cejam_exportacao.xlsx"
        if os.path.exists(caminho_local):
            st.info("📂 Carregando tokens de EXPORTAÇÃO do arquivo local (Desenvolvimento)")
            df = pd.read_excel(caminho_local)
            st.success(f"✅ {len(df)} tokens de exportação carregados localmente")
            return df
        else:
            st.error(f"❌ Arquivo não encontrado: {caminho_local}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar tokens de exportação: {e}")
        return pd.DataFrame()


# Usar estas variáveis no lugar dos caminhos diretos
TOKEN_UNIDADES_IMPORTACAO_DF = carregar_tokens_importacao()
TOKEN_UNIDADES_EXPORTACAO_DF = carregar_tokens_exportacao()

# ========== CREDENCIAIS DO GOOGLE (dos Secrets) ==========
def obter_credenciais_email():
    """
    Obtém as credenciais de e-mail dos Secrets do Streamlit.
    """
    try:
        if "email_credentials" in st.secrets:
            return {
                "user": st.secrets["email_credentials"]["USER"],
                "password": st.secrets["email_credentials"]["PASSWORD"],
                "host": st.secrets["email_credentials"]["HOST"],
                "port": st.secrets["email_credentials"]["PORT"]
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
# Para funcionar no Streamlit Cloud, use caminhos relativos
imagem_cejam = "assets/logo cejam.png"
imagem_sus = "assets/logo sus.png"