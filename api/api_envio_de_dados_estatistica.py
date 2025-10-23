import requests
import pandas as pd
import json
import streamlit as st
from datetime import datetime
from data.limpeza_base_de_para_rpa_vs_kpih import (
    obter_competencia_usuario,
    obter_unidade_id_da_sessao
)
from api.api_centro_custo import ajustar_competencia
from config.constants import get_token_unidades_importacao


def obter_dados_consolidados_da_memoria():
    """
    Busca os dados consolidados diretamente do session_state.
    Retorna o DataFrame se existir, None caso contrário.
    """
    try:
        # Opção 1: Dados consolidados já preparados
        if 'dados_consolidados' in st.session_state:
            df = st.session_state['dados_consolidados']
            if isinstance(df, pd.DataFrame) and not df.empty:
                st.success(f"✅ Dados consolidados encontrados na memória: {len(df)} registros")
                return df
        
        # Opção 2: DataFrame consolidado direto
        if 'df_consolidado' in st.session_state:
            df = st.session_state['df_consolidado']
            if isinstance(df, pd.DataFrame) and not df.empty:
                st.success(f"✅ DataFrame consolidado encontrado: {len(df)} registros")
                return df
        
        # Opção 3: Buscar nos dados dos formulários e consolidar na hora
        if 'formularios_data' in st.session_state:
            formularios = st.session_state['formularios_data']
            if formularios:
                st.info("🔄 Consolidando dados dos formulários...")
                df_consolidado = consolidar_formularios(formularios)
                if df_consolidado is not None and not df_consolidado.empty:
                    st.success(f"✅ Dados consolidados a partir dos formulários: {len(df_consolidado)} registros")
                    # Salva para próximas consultas
                    st.session_state['dados_consolidados'] = df_consolidado
                    return df_consolidado
        
        st.error("❌ Nenhum dado consolidado encontrado na memória!")
        st.info("💡 Certifique-se de que os formulários foram processados antes de enviar para a API")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados consolidados: {e}")
        return None


def consolidar_formularios(formularios_data):
    """
    Consolida dados de múltiplos formulários em um único DataFrame.
    
    Args:
        formularios_data: Dicionário com dados dos formulários
        
    Returns:
        DataFrame consolidado ou None
    """
    try:
        if not formularios_data:
            return None
        
        lista_dfs = []
        
        for nome_formulario, dados in formularios_data.items():
            if isinstance(dados, pd.DataFrame):
                df_temp = dados.copy()
                df_temp['formulario_origem'] = nome_formulario
                lista_dfs.append(df_temp)
        
        if not lista_dfs:
            return None
        
        df_consolidado = pd.concat(lista_dfs, ignore_index=True)
        
        # Garante que as colunas necessárias existem
        colunas_necessarias = ['Competência', 'Ponderação', 'Centro de Custo', 'Quantidade']
        if not all(col in df_consolidado.columns for col in colunas_necessarias):
            st.warning(f"⚠️ Colunas necessárias não encontradas. Disponíveis: {df_consolidado.columns.tolist()}")
            return None
        
        return df_consolidado
        
    except Exception as e:
        st.error(f"❌ Erro ao consolidar formulários: {e}")
        return None


def transformar_dataframe_para_api(df):
    """
    Transforma o DataFrame consolidado para o formato da API.
    
    Args:
        df: DataFrame com colunas 'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
        
    Returns:
        Lista de dicionários no formato da API
    """
    try:
        colunas_esperadas = ['Competência', 'Ponderação', 'Centro de Custo', 'Quantidade']
        colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Colunas faltantes no DataFrame: {colunas_faltantes}")
            st.info(f"Colunas disponíveis: {df.columns.tolist()}")
            return None
        
        dados_api = []
        registros_ignorados = 0
        
        for idx, row in df.iterrows():
            try:
                # Limpar e validar ponderação
                ponderacao = str(row['Ponderação']).strip()
                
                # Limpar e validar centro de custo
                centro_custo = str(row['Centro de Custo']).strip()
                
                # Limpar e converter quantidade
                quantidade_str = str(row['Quantidade']).replace(',', '.')
                try:
                    # Remove separadores de milhar e converte
                    valor_limpo = quantidade_str.replace('.', '', quantidade_str.count('.') - 1)
                    quantidade = float(valor_limpo)
                except (ValueError, TypeError):
                    registros_ignorados += 1
                    continue
                
                # Validações
                if pd.isna(ponderacao) or ponderacao.lower() in ['nan', 'none', '']:
                    registros_ignorados += 1
                    continue
                
                if pd.isna(centro_custo) or centro_custo.lower() in ['nan', 'none', '']:
                    registros_ignorados += 1
                    continue
                
                if quantidade <= 0:
                    registros_ignorados += 1
                    continue
                
                # Adiciona registro válido
                registro_api = {
                    "ponderacaoDeRateio": ponderacao,
                    "centroDeCusto": centro_custo,
                    "quantidade": quantidade
                }
                dados_api.append(registro_api)
                
            except Exception as e:
                registros_ignorados += 1
                if registros_ignorados <= 3:
                    st.warning(f"⚠️ Linha {idx + 1} com erro: {str(e)}")
                continue
        
        if registros_ignorados > 0:
            st.info(f"ℹ️ {registros_ignorados} registro(s) ignorado(s)")
        
        if not dados_api:
            st.error("❌ Nenhum registro válido encontrado após transformação")
            return None
        
        st.success(f"✅ {len(dados_api)} registros válidos preparados para envio")
        
        # Mostra preview
        with st.expander("👀 Preview dos dados para API"):
            st.json(dados_api[:3])
        
        return dados_api
        
    except Exception as e:
        st.error(f"❌ Erro ao transformar dados: {str(e)}")
        st.exception(e)
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
            if 'errors' in response_json:
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
            
            elif 'erros' in response_json and isinstance(response_json['erros'], list):
                resultado['erros_detalhados'] = response_json['erros']
                resultado['total_rejeitados'] = len(response_json['erros'])
            
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
    BUSCA DADOS DA MEMÓRIA (session_state) ao invés do sistema de arquivos.
    
    RETORNA: (sucesso: bool, dados_extras: dict, analise: dict)
    """
    try:
        st.title("📡 Envio de Dados Consolidados para API")
        
        # debug_mode = st.checkbox("🐛 Modo Debug", value=True)
        
        # Obter informações da sessão
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
        
        competencia_ajustada = ajustar_competencia(competencia_usuario)
        
        # BUSCAR DADOS DA MEMÓRIA AO INVÉS DE ARQUIVO
        st.info("🔍 Buscando dados consolidados na memória...")
        df_consolidado = obter_dados_consolidados_da_memoria()
        
        if df_consolidado is None or df_consolidado.empty:
            st.error("❌ Nenhum dado consolidado disponível para envio!")
            return False, {}, {}
        
        # Transformar DataFrame para formato da API
        st.info("🔄 Transformando dados para formato da API...")
        dados_para_envio = transformar_dataframe_para_api(df_consolidado)
        
        if not dados_para_envio:
            st.error("❌ Falha ao transformar dados para API")
            return False, {}, {}
        
        # Obter token
        st.info("🔑 Obtendo token de autenticação...")
        token = get_token_unidades_importacao(unidade_id)
        
        if not token:
            st.error("❌ Não foi possível obter o token da unidade!")
            return False, {}, {}
        
        st.success("✅ Token obtido com sucesso")
        
        # Montar payload
        payload = {
            "competencia": competencia_ajustada,
            "dados": dados_para_envio
        }
        
        # with st.expander("🔍 Detalhes da Requisição"):
        #     st.write(f"**Competência:** {payload['competencia']}")
        #     st.write(f"**Quantidade de registros:** {len(payload['dados'])}")
        #     st.write(f"**Token:** ...{str(token)[-10:] if token else 'VAZIO'}")
            
        #     if payload['dados']:
        #         st.write("**Exemplo do primeiro registro:**")
        #         st.json(payload['dados'][0])
        
        # Validar JSON
        try:
            json_test = json.dumps(payload, ensure_ascii=False)
            st.success("✅ Payload JSON válido")
        except Exception as json_err:
            st.error(f"❌ Erro no JSON do payload: {json_err}")
            return False, {}, {}
        
        # if debug_mode:
        #     with st.expander("🔍 DEBUG - Session State"):
        #         st.write(f"**Email usuário:** {email_usuario}")
        #         st.write(f"**Unidade usuário:** {unidade_usuario}")
        #         st.write(f"**Formulários data:** {list(st.session_state.get('formularios_data', {}).keys())}")
        #         st.write(f"**Unidade ID:** {unidade_id}")
        
        # URL da API
        url = 'https://backoffice.kpih.com.br:8000/api/v2/kpih/estatisticas'
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Dados extras para registro
        dados_extras = {
            'formularios_preenchidos': list(st.session_state.get('formularios_data', {}).keys()),
            'navegador': 'streamlit_app',
            'timestamp_envio_api_estatisticas': datetime.now().isoformat(),
            'unidade_id': unidade_id,
            'total_registros_enviados_estatisticas': len(dados_para_envio),
            'origem_dados': 'memoria_session_state' 
        }
        
        with st.spinner("📡 Enviando dados para a API..."):
            try:
                st.info("🔗 Fazendo requisição para API...")
                response = requests.put(url, headers=headers, json=payload, timeout=60)
                
                status_code = response.status_code
                
                # if debug_mode:
                #     st.info(f"🐛 DEBUG - Status Code: {status_code}")
                #     st.info(f"🐛 DEBUG - Response Text: {response.text[:500]}...")
                
                st.info(f"📊 Status Code: {status_code}")
                
                dados_extras['status_code_api_estatisticas'] = status_code
                dados_extras['resposta_api_estatisticas'] = response.text[:1000]
                
                if status_code in [200, 201]:
                    try:
                        resposta_api = response.json()
                    except:
                        resposta_api = {"mensagem": response.text}
                    
                    mensagem_api = resposta_api.get('message', resposta_api.get('mensagem', ''))
                    is_parcial = 'parcialmente' in mensagem_api.lower()
                    
                    analise = analisar_resposta_api(resposta_api, len(dados_para_envio))
                    dados_extras['analise_envio_estatisticas'] = analise
                    
                    # 🔥 SALVAR NO SESSION_STATE
                    st.session_state['resultado_envio_estatisticas'] = {
                        'sucesso': True,
                        'analise': analise,
                        'resposta_api': resposta_api,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.success(analise['mensagem_resumo'])
                    
                    with st.expander("📄 Resposta completa da API"):
                        st.json(resposta_api)
                    
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
                # if debug_mode:
                #     st.exception(req_err)
                return False, {}, {}
                
            except Exception as err:
                st.error(f"⚠️ Erro inesperado: {err}")
                st.exception(err)
                return False, {}, {}
        
    except Exception as e:
        st.error(f"💥 Erro crítico no processamento: {e}")
        st.exception(e)
        return False, {}, {}