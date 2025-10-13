import requests
import pandas as pd
import streamlit as st

from config.constants import TOKEN_UNIDADES_EXPORTACAO_DF

df_unidades = TOKEN_UNIDADES_EXPORTACAO_DF

def get_dados_permanentes(competencia_valida, payload_data):
    """
    Consome a API de dados permanentes
    """
    try:
        #pego o id da unidade, se não encontrar na competencia_valida, tenta pegar do payload_data
        unidade_id = competencia_valida.get('unidade_id') or payload_data.get('unidade_id')

        if not unidade_id: # se não encontrar o id da unidade
            st.error("❌ ID da unidade não encontrado")
            return {} #retorna um dicionário vazio

        url = f"https://www.kpih.com.br/api/v2/estatisticas/{unidade_id}" #url da API de dados permanentes juntamento com o id da unidade

        # Header com Token de autenticação
        token = competencia_valida.get('token') # pego o token, se não encontrar na competencia_valida, tenta pegar do payload_dat
        if not token: # se não encontrar o token
            st.error("❌ Token não encontrado nos dados da competência") #mostra essa mensagem de erro
            return {} #retorna um dicionário vazio
        

        headers = {
            "Authorization": f"Bearer {token}", #autenticação com o token
            "Content-Type": "application/json"
        }

        #payload data é um dicionário que contém a competência formatada e a unidade id
        payload = {
            "competenciaInicial": payload_data['competencia_formatada'],
            "competenciaFinal": payload_data['competencia_formatada'],
            "quantificacaoUnidadeProducao": "ABSOLUTO"
        }
        
        # # DEBUG: Informações da requisição
        # st.info(f"🌐 URL: {url}")
        # st.info(f"🔑 Token (primeiros 10 chars): {token[:10]}...")
        # st.info(f"🏢 Unidade ID: {unidade_id}")
        # st.info(f"📅 Competência: {payload_data.get('competencia_formatada', 'N/A')}")
        
        # Fazer a requisição
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Log da resposta
        st.info(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            st.success("✅ API retornou dados com sucesso!")
            return response.json()
        
        elif response.status_code == 401:
            st.error("❌ Erro 401: Problema de autorização")
            st.error(f"Resposta: {response.text}")
            
            # Tenta com Bearer se Token não funcionou
            st.info("🔄 Tentando com 'Bearer' em vez de 'Token'...")
            headers_bearer = headers.copy()
            headers_bearer["Authorization"] = f"Bearer {token}"
            
            response_bearer = requests.post(url, headers=headers_bearer, json=payload, timeout=30)
            
            if response_bearer.status_code == 200:
                st.success("✅ Funcionou com Bearer!")
                return response_bearer.json()
            else:
                st.error(f"❌ Também falhou com Bearer: {response_bearer.status_code}")
                st.error(f"Resposta Bearer: {response_bearer.text}")
            
            return {}

        else:
            st.error(f"❌ Erro na API:: {response.status_code}")
            st.error(f"Resposta: {response.text}")
            return {}
            
    except requests.exceptions.Timeout:
        st.error("⏰ Timeout na consulta da API")
        return {}
    except requests.exceptions.ConnectionError:
        st.error("🔌 Erro de conexão com a API")
        return {}
    except Exception as e:
        st.error(f"💥 Erro inesperado: {str(e)}")
        st.exception(e)
        return {}