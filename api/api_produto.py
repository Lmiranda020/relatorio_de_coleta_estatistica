import requests
import pandas as pd
import json
from config.constants import DEPARA_EXCEL_PRODUTO
from data.limpeza_base_de_para_produto import (
    carregar_e_tratar_depara_json, 
    validar_estrutura_depara, 
    obter_estatisticas_depara, 
    obter_competencia_usuario,
    obter_unidade_id_da_sessao
)
from config.constants import get_token_unidades_importacao
import streamlit as st

#CODIGO PARA FAZER O MAPEMANETO DE PRODUTO

def ajustar_competencia(competencia: str) -> str:
    """
    Ajusta competência de formatos como 'mai/2025' para '05/2025'.
    Se já estiver no formato '05/2025', retorna igual.
    Retorna no formato MM/AAAA.
    """
    if "/" not in competencia:
        return competencia  # não tem como ajustar
    
    partes = competencia.split("/")
    if len(partes) != 2:
        return competencia  # formato inesperado
    
    mes_parte = partes[0].strip()
    ano_parte = partes[1].strip()

    # Se já for número (ex: "05/2025"), mantém
    if mes_parte.isdigit():
        return f"{mes_parte.zfill(2)}/{ano_parte}"

    # Converter mês por extenso (abreviado)
    meses_map = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12"
    }
    mes_numero = meses_map.get(mes_parte.lower()[:3])  # garante 3 primeiras letras
    if mes_numero:
        return f"{mes_numero}/{ano_parte}"

    return competencia  # caso não reconheça o mês

def de_para_produto():
    """
    Consome a API para subir dados de produto para UMA unidade específica.
    Utiliza o ID da unidade armazenado na sessão do Streamlit.
    """
    try:
        # --- Obter ID da unidade da sessão ---
        unidade_id = obter_unidade_id_da_sessao()
        
        if not unidade_id:
            st.error("❌ ID da unidade não encontrado. Execute primeiro o processo de dados permanentes.")
            return False
        
        # --- Obter token da unidade específica ---
        st.info("📊 Obtendo token da unidade...")
        token = get_token_unidades_importacao(unidade_id)
        
        if not token:
            st.error("❌ Não foi possível obter o token da unidade!")
            return False
        
        st.success("✅ Token da unidade obtido com sucesso")

        # --- Carrega e trata o de-para ---
        st.info("🔄 Carregando e tratando dados de de-para...")
        dados_depara = carregar_e_tratar_depara_json(DEPARA_EXCEL_PRODUTO)
        
        if not dados_depara:
            st.error("❌ Nenhum dado de de-para foi carregado!")
            return False
        
        st.success(f"✅ {len(dados_depara)} registros preparados para envio")
        
        # Validar estrutura dos dados
        if not validar_estrutura_depara(dados_depara):
            st.error("❌ Estrutura dos dados inválida!")
            return False
        
        # Exibir estatísticas
        stats = obter_estatisticas_depara(dados_depara)
        
        # --- Estrutura o payload conforme documentação da API ---
        competencia_usuario = obter_competencia_usuario()
        competencia_ajustada = ajustar_competencia(competencia_usuario)
        st.success(f"📅 Competência final (usuário): {competencia_ajustada}")
        
        if dados_depara and len(dados_depara) > 0:
            # Cria lista de mapeamentos apenas com os campos necessários para a API
            mapeamentos_limpos = []
            for item in dados_depara:
                mapeamento = {
                    "produtoErp": item.get("produtoErp", "").strip(),
                    "produtoKpih": item.get("produtoKpih", "").strip()
                }
                # Só adiciona se ambos os campos estão preenchidos
                if mapeamento["produtoErp"] and mapeamento["produtoKpih"]:
                    mapeamentos_limpos.append(mapeamento)
        else:
            st.warning("⚠️ Nenhum mapeamento encontrado, usando dados padrão")
            mapeamentos_limpos = []

        st.info(f"🔧 Mapeamentos limpos para envio: {len(mapeamentos_limpos)}")
        
        st.info("🚀 Iniciando envio para a API...")
        
        # --- Processar a unidade específica ---
        nome_unidade = st.session_state.get('unidade_usuario', f'Unidade {unidade_id}')
        
        with st.spinner(f"📡 Processando {nome_unidade} (ID: {unidade_id})..."):

            # URL da API
            url = f'https://backoffice.kpih.com.br:8000/api/v2/kpih/mapeamento/produto'
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # PAYLOAD CONFORME DOCUMENTAÇÃO - Formato: "MM/AAAA"
            payload = {
                "competencia": competencia_ajustada,
                "mapeamentos": mapeamentos_limpos
            }

            # Debug detalhado
            with st.expander("🔍 Detalhes da Requisição"):
                st.write(f"**URL:** {url}")
                st.write(f"**Token:** ...{str(token)[-10:] if token else 'VAZIO'}")
                st.write(f"**Competência:** {payload['competencia']}")
                st.write(f"**Quantidade de mapeamentos:** {len(payload['mapeamentos'])}")
                
                # Mostra exemplo do primeiro mapeamento
                if payload['mapeamentos']:
                    st.write(f"**Exemplo mapeamento:**")
                    st.json(payload['mapeamentos'][0])
                
                # Mostra payload completo
                st.write("**Payload completo:**")
                st.json(payload)
            
            # Validar JSON
            try:
                json_test = json.dumps(payload, ensure_ascii=False)
                st.success("✅ Payload JSON válido")
            except Exception as json_err:
                st.error(f"❌ Erro no JSON do payload: {json_err}")
                return False

            # Executar requisição
            try:
                st.info("🔄 Enviando requisição...")
                response = requests.put(url, headers=headers, json=payload, timeout=30)

                status_code = response.status_code
                st.info(f"📊 Status Code: {status_code}")
                
                if status_code in [200, 201]:
                    st.success(f"✅ {nome_unidade} - Sucesso!")
                    
                    try:
                        dados_resposta = response.json()
                        with st.expander("📄 Resposta da API"):
                            st.json(dados_resposta)
                    except:
                        st.info(f"📄 Resposta (texto): {response.text[:200]}...")
                    
                    return True
                    
                elif status_code == 400:
                    st.error(f"❌ {nome_unidade} - Erro de validação (400)")
                    st.error(f"📄 Detalhes: {response.text}")
                    return False
                    
                elif status_code == 401:
                    st.error(f"❌ {nome_unidade} - Token inválido (401)")
                    st.error(f"📄 Detalhes: {response.text}")
                    return False
                    
                elif status_code == 403:
                    st.error(f"❌ {nome_unidade} - Acesso negado (403)")
                    st.error(f"📄 Detalhes: {response.text}")
                    return False
                    
                elif status_code == 422:
                    st.error(f"❌ {nome_unidade} - Erro de validação de dados (422)")
                    st.error(f"📄 Detalhes: {response.text}")
                    return False
                    
                else:
                    st.error(f"❌ {nome_unidade} - Erro HTTP {status_code}")
                    with st.expander("📄 Detalhes da Resposta"):
                        st.write(f"**Headers:** {dict(response.headers)}")
                        st.write(f"**Body:** {response.text}")
                    return False

            except requests.exceptions.Timeout:
                st.error(f"⏱️ {nome_unidade} - Timeout na requisição")
                return False
                
            except requests.exceptions.ConnectionError:
                st.error(f"🌐 {nome_unidade} - Erro de conexão")
                return False
                
            except requests.exceptions.RequestException as req_err:
                st.error(f"🔥 {nome_unidade} - Erro na requisição: {req_err}")
                return False
                
            except Exception as err:
                st.error(f"⚠️ {nome_unidade} - Erro inesperado: {err}")
                return False

    except Exception as e:
        st.error(f"💥 Erro crítico no processamento: {e}")
        st.exception(e)
        return False