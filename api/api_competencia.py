import requests
import json
import pandas as pd
import streamlit as st
import base64

def get_competencias():

    unidade_selecionanda = st.session_state.get('unidade_usuario')

    # Verifica se já foi consultado nesta sessão
    if 'df_competencias_cache' in st.session_state:
        # print(f"DEBUG: RETORNANDO CACHE (pode estar desatualizado)")
        return st.session_state['df_competencias_cache']
 
    # Carregar tokens aqui dentro da função
    df_unidades = carregar_tokens_exportacao()

    # DEBUG: Mostrar quantas unidades existem no total
    # print(f"DEBUG: Total de unidades no arquivo: {len(df_unidades)}")
    # print(f"DEBUG: Unidade do usuário: {unidade_selecionanda}")

    # ADICIONAR ESTE FILTRO:
    if unidade_selecionanda:
        # # DEBUG: Mostrar unidades antes do filtro
        # print(f"DEBUG: Unidades antes do filtro: {df_unidades['nome'].tolist()}")
        
        df_unidades = df_unidades[df_unidades['nome'].str.contains(unidade_selecionanda, case=False, na=False)]
        
        # # DEBUG: Mostrar resultado do filtro
        # print(f"DEBUG: Unidades após filtro: {df_unidades['nome'].tolist()}")
        # print(f"DEBUG: Quantidade após filtro: {len(df_unidades)}")

    lista_competencias = []
    arquivo_unico = []

    for _, unidade in df_unidades.iterrows():
        id_unidade = unidade['id']
        token = unidade['token']

        url = f"https://www.kpih.com.br/api/v2/competencias/{id_unidade}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                competencias = response.json()
                # Extrai a lista de competências
                lista_competencias = competencias.get('items', [])

                # Verifica se há dados
                if lista_competencias:
                    df_competencias = pd.DataFrame(lista_competencias)
                    df_competencias['unidade_id'] = id_unidade  # Adiciona de onde veio
                    df_competencias = df_competencias.merge(df_unidades[['id', 'nome', 'token']],
                                                            left_on='unidade_id', right_on='id', how='left')
                    arquivo_unico.append(df_competencias)
            else:
                 st.warning(f"Erro {response.status_code} na unidade {id_unidade}")
        except Exception as e:
            st.error(f"Erro ao processar unidade {id_unidade}: {e}")

    # Concatena e salva
    if arquivo_unico: #se a lista não estiver vazia
        df_final = pd.concat(arquivo_unico, ignore_index=True) #concatena todos os dataframes da lista em um unico dataframe
        st.session_state['df_competencias_cache'] = df_final  # Cache na sessão
        return df_final #retona o dataframe final
    
    return pd.DataFrame() #retorno a base de competências vazia se não encontrar nada


def carregar_tokens_exportacao():
    """
    Carrega os tokens de exportação do secrets e converte de base64 para DataFrame
    """
    try:
        # Acessa o secret
        token_base64 = st.secrets["excel_tokens_exportacao_base64"]
        
        # Decodifica de base64
        token_decoded = base64.b64decode(token_base64)
        
        # Carrega o Excel a partir dos bytes decodificados
        from io import BytesIO
        df_tokens = pd.read_excel(BytesIO(token_decoded))
        
        return df_tokens
        
    except Exception as e:
        st.error(f"Erro ao carregar tokens de exportação: {e}")
        return pd.DataFrame()