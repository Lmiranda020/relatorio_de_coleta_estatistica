# ============================================================================
# ARQUIVO: api_envio_de_dados_estatistica.py (VERSÃO MODIFICADA)
# ============================================================================

import requests
import pandas as pd
import json
import os
import glob
import streamlit as st
from datetime import datetime
from data.limpeza_base_de_para_rpa_vs_kpih import (
    obter_competencia_usuario,
    obter_unidade_id_da_sessao
)
from api.api_centro_custo import ajustar_competencia
import datetime
from config.constants import get_token_unidades_importacao


def encontrar_arquivo_consolidado(diretorio_saida, unidade, competencia):
    """Encontra o arquivo consolidado mais recente no diretório especificado."""
    try:
        padrao_arquivo = f"CONSOLIDADO_{unidade}_{competencia}*.csv"
        padrao_arquivo = padrao_arquivo.replace("/", "-").replace(" ", "_")
        
        caminho_busca = os.path.join(diretorio_saida, padrao_arquivo)
        arquivos_encontrados = glob.glob(caminho_busca)
        
        if not arquivos_encontrados:
            st.error(f"❌ Nenhum arquivo consolidado encontrado: {caminho_busca}")
            return None
        
        arquivo_mais_recente = max(arquivos_encontrados, key=os.path.getctime)
        st.info(f"📁 Arquivo encontrado: {os.path.basename(arquivo_mais_recente)}")
        
        return arquivo_mais_recente
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar arquivo consolidado: {str(e)}")
        return None


def carregar_e_transformar_consolidado(caminho_arquivo):
    """Carrega o arquivo consolidado CSV e transforma para o formato necessário da API."""
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8-sig')
        st.success(f"✅ Arquivo carregado: {len(df)} registros")
        
        colunas_esperadas = ['Competência', 'Ponderação', 'Centro de Custo', 'Quantidade']
        colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Colunas faltantes no arquivo: {colunas_faltantes}")
            return None
        
        dados_api = []
        
        for _, row in df.iterrows():
            quantidade_str = str(row['Quantidade']).replace(',', '.')
            try:
                valor_limpo = quantidade_str.replace('.', '').replace(',', '.')
                quantidade = float(valor_limpo)
            except (ValueError, TypeError):
                st.warning(f"⚠️ Quantidade inválida ignorada: {row['Quantidade']} para {row['Centro de Custo']}")
                continue
            
            if quantidade > 0:
                registro_api = {
                    "ponderacaoDeRateio": str(row['Ponderação']).strip(),
                    "centroDeCusto": str(row['Centro de Custo']).strip(),
                    "quantidade": quantidade
                }
                dados_api.append(registro_api)
        
        st.info(f"🔄 {len(dados_api)} registros válidos preparados para envio")
        
        if dados_api:
            with st.expander("👀 Preview dos dados para API"):
                st.json(dados_api[:3])
        
        return dados_api
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        return None


def analisar_resposta_api(response_json, total_registros_enviados):
    """Analisa a resposta da API para identificar registros aceitos/rejeitados."""
    resultado = {
        'total_enviados': total_registros_enviados,
        'total_aceitos': 0,
        'total_rejeitados': 0,
        'erros_detalhados': [],
        'parcial': False,
        'mensagem_resumo': ''
    }
    
    try:
        if isinstance(response_json, dict):
            # Verifica diferentes formatos de resposta
            if 'errors' in response_json:
                # Formato: {"message": "...", "errors": {"0": "erro1", "1": "erro2"}}
                errors_dict = response_json['errors']
                if isinstance(errors_dict, dict):
                    resultado['erros_detalhados'] = [
                        {'indice': k, 'mensagem': v} 
                        for k, v in errors_dict.items()
                    ]
                    resultado['total_rejeitados'] = len(errors_dict)
                elif isinstance(errors_dict, list):
                    resultado['erros_detalhados'] = errors_dict
                    resultado['total_rejeitados'] = len(errors_dict)
            
            # Também verifica 'erros' (português)
            elif 'erros' in response_json and isinstance(response_json['erros'], list):
                resultado['erros_detalhados'] = response_json['erros']
                resultado['total_rejeitados'] = len(response_json['erros'])
            
            # Calcula aceitos
            resultado['total_aceitos'] = total_registros_enviados - resultado['total_rejeitados']
        
        resultado['parcial'] = resultado['total_rejeitados'] > 0
        
        if resultado['total_rejeitados'] == 0:
            resultado['mensagem_resumo'] = f"✅ Todos os {resultado['total_aceitos']} registros foram aceitos"
        else:
            resultado['mensagem_resumo'] = (
                f"⚠️ Envio parcial: {resultado['total_aceitos']} aceitos, "
                f"{resultado['total_rejeitados']} rejeitados"
            )
        
        return resultado
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao analisar resposta: {e}")
        resultado['total_aceitos'] = total_registros_enviados
        resultado['mensagem_resumo'] = f"⚠️ {total_registros_enviados} enviados (análise indisponível)"
        return resultado


def enviar_consolidado_para_api():
    """
    Envia dados consolidados (estatísticas) para a API.
    RETORNA: (sucesso: bool, dados_extras: dict, analise: dict)
    """
    try:
        st.title("📡 Envio de Dados Consolidados para API")
        
        debug_mode = st.checkbox("🐛 Modo Debug", value=True)
        
        unidade_id = obter_unidade_id_da_sessao()
        if not unidade_id:
            st.error("❌ ID da unidade não encontrado.")
            return False, {}, {}
        
        email_usuario = st.session_state.get('email_usuario')
        unidade_usuario = st.session_state.get('unidade_usuario', 'Unidade_Desconhecida')
        competencia_usuario = obter_competencia_usuario()
        
        if not email_usuario:
            st.error("❌ Email do usuário não encontrado.")
            return False, {}, {}
        
        st.info(f"👤 Usuário: {email_usuario}")
        st.info(f"🏢 Unidade: {unidade_usuario}")
        st.info(f"📅 Competência: {competencia_usuario}")

        competencia_usuario_p_payload = ajustar_competencia(competencia_usuario)
        
        diretorio_saida = st.session_state.get('output_dir', None)
        
        if not diretorio_saida or not os.path.exists(diretorio_saida):
            st.error(f"❌ Diretório de saída não encontrado: {diretorio_saida}")
            return False, {}, {}
        
        st.info("🔍 Buscando arquivo consolidado...")
        caminho_arquivo = encontrar_arquivo_consolidado(diretorio_saida, unidade_usuario, competencia_usuario)
        
        if not caminho_arquivo:
            return False, {}, {}
        
        st.info("🔄 Carregando e transformando dados...")
        dados_para_envio = carregar_e_transformar_consolidado(caminho_arquivo)
        
        if not dados_para_envio:
            return False, {}, {}
        
        st.info("🔑 Obtendo token de autenticação...")
        token = get_token_unidades_importacao()
        
        if not token:
            st.error("❌ Não foi possível obter o token da unidade!")
            return False, {}, {}
        
        st.success("✅ Token obtido com sucesso")
        
        payload = {
            "competencia": competencia_usuario_p_payload,
            "dados": dados_para_envio
        }
        
        with st.expander("🔍 Detalhes da Requisição"):
            st.write(f"**Competência:** {payload['competencia']}")
            st.write(f"**Quantidade de registros:** {len(payload['dados'])}")
            st.write(f"**Token:** ...{str(token)[-10:] if token else 'VAZIO'}")
            
            payload_exemplo = {
                "competencia": payload['competencia'],
                "dados": payload['dados'][:2] if len(payload['dados']) > 2 else payload['dados']
            }
            st.json(payload_exemplo)
        
        try:
            json_test = json.dumps(payload, ensure_ascii=False)
            st.success("✅ Payload JSON válido")
        except Exception as json_err:
            st.error(f"❌ Erro no JSON do payload: {json_err}")
            return False, {}, {}
        
        if debug_mode:
            with st.expander("🔍 DEBUG - Session State"):
                st.write(f"**Email usuário:** {email_usuario}")
                st.write(f"**Unidade usuário:** {unidade_usuario}")
                st.write(f"**Formulários data:** {list(st.session_state.get('formularios_data', {}).keys())}")
                st.write(f"**Unidade ID:** {unidade_id}")
        
        url = 'https://backoffice.kpih.com.br:8000/api/v2/kpih/estatisticas'
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        dados_extras = {
            'formularios_preenchidos': list(st.session_state.get('formularios_data', {}).keys()),
            'navegador': 'streamlit_app',
            'timestamp_envio_api_estatisticas': datetime.datetime.now().isoformat(),
            'unidade_id': unidade_id,
            'arquivo_consolidado_enviado': os.path.basename(caminho_arquivo),
            'total_registros_enviados_estatisticas': len(dados_para_envio)
        }
        
        with st.spinner("📡 Enviando dados para a API..."):
            try:
                st.info("🔗 Fazendo requisição para API...")
                response = requests.put(url, headers=headers, json=payload, timeout=60)
                
                status_code = response.status_code
                
                if debug_mode:
                    st.info(f"🐛 DEBUG - Status Code: {status_code}")
                    st.info(f"🐛 DEBUG - Response Text: {response.text[:500]}...")
                
                st.info(f"📊 Status Code: {status_code}")
                
                dados_extras['status_code_api_estatisticas'] = status_code
                dados_extras['resposta_api_estatisticas'] = response.text[:1000]
                
                if status_code in [200, 201]:
                    try:
                        resposta_api = response.json()
                    except:
                        resposta_api = {"mensagem": response.text}
                    
                    # Verifica se é um envio parcial através da mensagem
                    mensagem_api = resposta_api.get('message', resposta_api.get('mensagem', ''))
                    is_parcial = 'parcialmente' in mensagem_api.lower()
                    
                    analise = analisar_resposta_api(resposta_api, len(dados_para_envio))
                    dados_extras['analise_envio_estatisticas'] = analise
                    
                    # 🔥 SALVAR NO SESSION_STATE PARA NÃO PERDER
                    st.session_state['resultado_envio_estatisticas'] = {
                        'sucesso': True,
                        'analise': analise,
                        'resposta_api': resposta_api,
                        'timestamp': datetime.datetime.now().isoformat()
                    }

                    with st.expander("📄 Resposta completa da API"):
                        st.json(resposta_api)
                        # st.stop()

                    return True, dados_extras, analise
                    
                else:
                    if status_code == 400:
                        st.error("❌ Erro de validação (400)")
                    elif status_code == 401:
                        st.error("❌ Token inválido (401)")
                    elif status_code == 403:
                        st.error("❌ Acesso negado (403)")
                    elif status_code == 422:
                        st.error("❌ Erro de validação de dados (422)")
                    else:
                        st.error(f"❌ Erro HTTP {status_code}")
                    
                    st.error(f"📄 Detalhes: {response.text}")
                    dados_extras['erro_api_estatisticas'] = response.text
                    
                    return False, dados_extras, {}
                
            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout na requisição (60s)")
                return False, {}, {}
                
            except requests.exceptions.ConnectionError:
                st.error("🌐 Erro de conexão com a API")
                return False, {}, {}
                
            except requests.exceptions.RequestException as req_err:
                st.error(f"🔥 Erro na requisição: {req_err}")
                if debug_mode:
                    st.exception(req_err)
                return False, {}, {}
                
            except Exception as err:
                st.error(f"⚠️ Erro inesperado: {err}")
                st.exception(err)
                return False, {}, {}
        
    except Exception as e:
        st.error(f"💥 Erro crítico no processamento: {e}")
        st.exception(e)
        return False, {}, {}