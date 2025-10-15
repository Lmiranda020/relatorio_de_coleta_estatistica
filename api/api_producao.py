import requests
import pandas as pd
import streamlit as st

def api_producao():
    """
    Consome a API de dados de produção
    """
    try:
        unidade_selecionada = st.session_state.get('unidade_usuario')
        
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada no session_state!")
            return {}

        # Carrega o arquivo de unidades
        try:
            # from config.constants import TOKEN_UNIDADES_EXPORTACAO_DF
            # df_unidades = TOKEN_UNIDADES_EXPORTACAO_DF
            from config.constants import get_token_unidades_exportacao
            df_unidades = get_token_unidades_exportacao()
        except FileNotFoundError:
            st.error("❌ Arquivo 'unidades_tokens_cejam_exportacao.xlsx' não encontrado!")
            return {}
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
            return {}

        # Filtra as unidades que correspondem ao nome selecionado
        df_unidades_filtradas = df_unidades[
            df_unidades['nome'].str.contains(unidade_selecionada, case=False, na=False)
        ]

        if df_unidades_filtradas.empty:
            st.error(f"❌ Nenhuma unidade encontrada com o nome '{unidade_selecionada}'")
            return {}

        # Pega a última (mais recente) unidade que corresponde ao filtro
        unidade_selecionada_row = df_unidades_filtradas.iloc[-1]
        
        id_unidade = unidade_selecionada_row['id']
        token = unidade_selecionada_row['token']

        # Verifica se ID e token foram encontrados
        if pd.isna(id_unidade) or not id_unidade:
            st.error("❌ ID da unidade não encontrado ou é inválido!")
            return {}
            
        if pd.isna(token) or not token:
            st.error("❌ Token não encontrado ou é inválido!")
            return {}

        # Monta URL da API
        url = f"https://www.kpih.com.br/api/v2/producoes/{id_unidade}"

        # Header com Token de autenticação
        headers = {
            "Authorization": f"Bearer {token}",
        }

        # Payload da requisição
        competencia_inicial_e_final = st.session_state.get('competencia_anterior_utilizada')
        
        if not competencia_inicial_e_final:
            st.error("Competência não encontrada no session_state! Execute a configuração de dados permanentes para evitar erros")
            return {}
        
        payload = {
            "competenciaInicial": competencia_inicial_e_final,
            "competenciaFinal": competencia_inicial_e_final,
            "quantificacaoUnidadeProducao": "ABSOLUTO"
        }
        
        # Fazer a requisição
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ Erro 401: Problema de autorização com a API")
            return {}
        else:
            st.error(f"❌ Erro na API: {response.status_code}")
            return {}
            
    except requests.exceptions.Timeout:
        st.error("⏰ Timeout na consulta da API")
        return {}
    except requests.exceptions.ConnectionError:
        st.error("🔌 Erro de conexão com a API")
        return {}
    except Exception as e:
        st.error(f"💥 Erro inesperado: {str(e)}")
        return {}