import requests
import pandas as pd
import json
import datetime
import streamlit as st
from data.limpeza_base_de_para_rpa_vs_kpih import (
    obter_competencia_usuario,
    obter_unidade_id_da_sessao
)
from api.api_centro_custo import ajustar_competencia
from config.constants import get_token_unidades_importacao


def obter_dados_producao_da_memoria():
    """
    Busca os dados de produção diretamente do session_state.
    Retorna o DataFrame se existir, None caso contrário.
    """
    try:
        # Busca no dicionário de formulários
        formularios_data = st.session_state.get('formularios_data', {})
        
        # O formulário de produção pode ter esse nome exato
        if 'Produção' in formularios_data:
            df_producao = formularios_data['Produção']
            
            if isinstance(df_producao, pd.DataFrame) and not df_producao.empty:
                st.success(f"✅ Dados de produção encontrados na memória: {len(df_producao)} registros")
                return df_producao
        
        st.warning("⚠️ Dados de produção não encontrados na memória")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados de produção: {e}")
        return None


def transformar_dados_producao_da_memoria(df):
    """
    Transforma o DataFrame de produção da memória para o formato da API.
    Formato esperado: colunas 'Ponderação', 'Centro de Custo' e 'Quantidade'
    """
    try:
        # Validar colunas necessárias
        colunas_necessarias = ['Ponderação', 'Centro de Custo', 'Quantidade']
        colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Colunas necessárias não encontradas: {colunas_faltantes}")
            st.error(f"Colunas disponíveis: {list(df.columns)}")
            return None
        
        dados_api = []
        registros_ignorados = 0
        
        for idx, row in df.iterrows():
            try:
                # Limpar e converter produto (vem da coluna Ponderação)
                produto = str(row['Ponderação']).strip()
                
                # Limpar e converter centro de custo
                centro_custo = str(row['Centro de Custo']).strip()
                
                # Limpar e converter quantidade
                quantidade_str = str(row['Quantidade']).replace(',', '.').strip()
                quantidade = float(quantidade_str)
                
                # Validar se os campos não são vazios ou inválidos
                produto_valido = produto and produto.lower() not in ['nan', 'none', '']
                centro_valido = centro_custo and centro_custo.lower() not in ['nan', 'none', '']
                
                # Só adiciona se quantidade > 0 e campos válidos
                if quantidade > 0 and produto_valido and centro_valido:
                    registro_api = {
                        "produto": produto,
                        "centroDeCusto": centro_custo,
                        "quantidade": quantidade
                    }
                    dados_api.append(registro_api)
                else:
                    registros_ignorados += 1
                    if registros_ignorados <= 3:  # Mostra só os 3 primeiros
                        st.warning(f"⚠️ Linha {idx + 2} ignorada - produto: '{produto}' | centro: '{centro_custo}' | qtd: {quantidade}")
                    
            except Exception as e:
                registros_ignorados += 1
                if registros_ignorados <= 3:
                    st.warning(f"⚠️ Linha {idx + 2} com erro: {str(e)}")
                continue
        
        if registros_ignorados > 0:
            st.info(f"ℹ️ {registros_ignorados} registro(s) ignorado(s)")
        
        if registros_ignorados > 3:
            st.info(f"   ... e mais {registros_ignorados - 3} registros também foram ignorados")
        
        if not dados_api:
            st.warning("⚠️ Nenhum registro válido após transformação")
            return None
        
        st.success(f"✅ {len(dados_api)} registros válidos preparados")
        return dados_api
        
    except Exception as e:
        st.error(f"❌ Erro ao processar dados de produção: {str(e)}")
        st.exception(e)
        return None


def analisar_resposta_producao(response_json, dados_enviados):
    """
    Analisa a resposta da API de produção para identificar erros.
    """
    resultado = {
        'total_enviados': len(dados_enviados),
        'total_aceitos': 0,
        'total_rejeitados': 0,
        'registros_com_erro': [],
        'mensagem_resumo': '',
        'parcial': False
    }
    
    try:
        if isinstance(response_json, dict):
            if 'errors' in response_json:
                errors_dict = response_json['errors']
                
                if isinstance(errors_dict, dict):
                    for indice_str, mensagem_erro in errors_dict.items():
                        try:
                            idx = int(indice_str)
                            
                            if 0 <= idx < len(dados_enviados):
                                resultado['registros_com_erro'].append({
                                    'motivo': str(mensagem_erro)
                                })
                            else:
                                resultado['registros_com_erro'].append({
                                    'motivo': str(mensagem_erro)
                                })
                                
                        except (ValueError, TypeError) as e:
                            st.warning(f"⚠️ Erro ao processar índice '{indice_str}': {e}")
                            resultado['registros_com_erro'].append({
                                'indice': indice_str,
                                'motivo': str(mensagem_erro)
                            })
                    
                    resultado['total_rejeitados'] = len(errors_dict)
                
                elif isinstance(errors_dict, list):
                    for i, erro in enumerate(errors_dict):
                        if isinstance(erro, dict):
                            resultado['registros_com_erro'].append({
                                'motivo': erro.get('mensagem', erro.get('erro', 'Erro desconhecido'))
                            })
                        else:
                            resultado['registros_com_erro'].append({
                                'motivo': str(erro)
                            })
                    
                    resultado['total_rejeitados'] = len(errors_dict)
            
            resultado['total_aceitos'] = resultado['total_enviados'] - resultado['total_rejeitados']
        
        resultado['parcial'] = resultado['total_rejeitados'] > 0
        
        if resultado['total_rejeitados'] == 0:
            resultado['mensagem_resumo'] = f"✅ Todos os {resultado['total_aceitos']} registros foram aceitos"
        else:
            resultado['mensagem_resumo'] = (
                f"⚠️ {resultado['total_aceitos']} aceitos, "
                f"{resultado['total_rejeitados']} rejeitados"
            )
        
        return resultado
        
    except Exception as e:
        st.error(f"⚠️ Erro ao analisar resposta de produção: {e}")
        resultado['total_aceitos'] = resultado['total_enviados']
        resultado['mensagem_resumo'] = f"⚠️ {resultado['total_enviados']} enviados (análise de erros falhou)"
        return resultado


def enviar_producao_para_api():
    """
    Envia dados de produção para a API.
    BUSCA DADOS DA MEMÓRIA (session_state) ao invés do sistema de arquivos.
    
    RETORNA: (sucesso: bool, dados_extras: dict)
    """
    try:
        unidade_id = obter_unidade_id_da_sessao()
        competencia_usuario = obter_competencia_usuario()
        
        dados_extras = {
            'timestamp_envio_producao': datetime.datetime.now().isoformat(),
            'origem_dados': 'memoria_session_state'
        }
        
        if not unidade_id or not competencia_usuario:
            st.warning("⚠️ Produção não enviada - dados incompletos")
            dados_extras['erro_producao'] = 'dados_incompletos'
            return False, dados_extras
        
        # 🔥 BUSCAR DADOS DA MEMÓRIA AO INVÉS DE ARQUIVO
        st.info("🔍 Buscando dados de produção na memória...")
        df_producao = obter_dados_producao_da_memoria()
        
        if df_producao is None:
            st.info("ℹ️ Dados de produção não encontrados - pulando envio")
            dados_extras['erro_producao'] = 'arquivo_nao_encontrado'
            return False, dados_extras
        
        # Transformar DataFrame para formato da API
        st.info("🔄 Transformando dados para formato da API...")
        dados_para_envio = transformar_dados_producao_da_memoria(df_producao)
        
        if not dados_para_envio:
            st.warning("⚠️ Nenhum dado válido de produção para enviar")
            dados_extras['erro_producao'] = 'dados_invalidos'
            return False, dados_extras
        
        dados_extras['total_registros_producao'] = len(dados_para_envio)
        
        # Obter token
        st.info("🔑 Obtendo token de autenticação...")
        token = get_token_unidades_importacao(unidade_id)
        
        if not token:
            st.warning("⚠️ Token não disponível - produção não enviada")
            dados_extras['erro_producao'] = 'token_indisponivel'
            return False, dados_extras
        
        # Ajustar competência
        competencia_ajustada = ajustar_competencia(competencia_usuario)
        
        # Montar payload
        payload = {
            "competencia": competencia_ajustada,
            "dados": dados_para_envio
        }
        
        # # Debug do payload
        # with st.expander("🔍 Detalhes do Payload de Produção"):
        #     st.write(f"**Competência:** {payload['competencia']}")
        #     st.write(f"**Total de registros:** {len(payload['dados'])}")
        #     if payload['dados']:
        #         st.write("**Exemplo do primeiro registro:**")
        #         st.json(payload['dados'][0])
        
        # URL e headers
        url = 'https://backoffice.kpih.com.br:8000/api/v2/kpih/producoes'
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        with st.spinner("📡 Enviando produção para API..."):
            response = requests.put(url, headers=headers, json=payload, timeout=60)
            
            dados_extras['status_code_api_producao'] = response.status_code
            dados_extras['resposta_api_producao'] = response.text[:1000]
            
            st.info(f"📊 Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    resposta_api = response.json()
                except:
                    resposta_api = {"mensagem": response.text}
                
                # Analisa a resposta
                analise = analisar_resposta_producao(resposta_api, dados_para_envio)
                dados_extras['analise_envio_producao'] = analise
                
                # 🔥 SALVAR NO SESSION_STATE
                st.session_state['resultado_envio_producao'] = {
                    'sucesso': True,
                    'analise': analise,
                    'resposta_api': resposta_api,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
                st.success(analise['mensagem_resumo'])
                
                with st.expander("📄 Detalhes da resposta da API"):
                    st.json(resposta_api)
                
                return True, dados_extras
                
            elif response.status_code == 400:
                st.error("❌ Erro de validação (400)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = 'http_400'
                return False, dados_extras
                
            elif response.status_code == 401:
                st.error("❌ Token inválido (401)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = 'http_401'
                return False, dados_extras
                
            elif response.status_code == 422:
                st.error("❌ Erro de validação de dados (422)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = 'http_422'
                return False, dados_extras
                
            else:
                st.warning(f"⚠️ Erro ao enviar produção (Status {response.status_code})")
                with st.expander("❌ Ver erro de produção"):
                    st.error(response.text)
                dados_extras['erro_producao'] = f'http_{response.status_code}'
                return False, dados_extras
    
    except requests.exceptions.Timeout:
        st.warning("⏱️ Timeout ao enviar produção (limite de 60 segundos)")
        return False, {'erro_producao': 'timeout'}
    
    except requests.exceptions.ConnectionError:
        st.error("🌐 Erro de conexão ao enviar produção")
        return False, {'erro_producao': 'connection_error'}
    
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Erro na requisição de produção: {str(e)}")
        return False, {'erro_producao': str(e)}
    
    except Exception as e:
        st.error(f"💥 Erro inesperado ao enviar produção: {str(e)}")
        st.exception(e)
        return False, {'erro_producao': str(e)}


# ============================================================================
# FUNÇÃO DE REGISTRO NO BANCO (MANTIDA IGUAL)
# ============================================================================

def registrar_no_banco(email_usuario, unidade_usuario, competencia_usuario, dados_extras, status_envio='enviado_api_sucesso'):
    """Registra no banco de dados com tratamento robusto de erros."""
    try:
        from data.manager_postgre import DatabaseManagerPostgres
        
        st.info("💾 Iniciando registro no banco de dados...")
        
        if not email_usuario:
            st.error("❌ Email do usuário não encontrado na sessão")
            return None
            
        if not unidade_usuario:
            st.error("❌ Unidade do usuário não encontrada na sessão")
            return None
            
        if not competencia_usuario:
            st.error("❌ Competência não encontrada")
            return None
        
        db = DatabaseManagerPostgres()
        
        if not db.testar_conexao():
            st.error("❌ Falha ao conectar com o banco de dados")
            return None
        
        st.success("✅ Conexão com banco estabelecida")
        
        tabela_ok = db.criar_tabela_preenchimentos_finalizados()
        if not tabela_ok:
            st.error("❌ Falha ao criar/verificar tabela")
            return None
        
        st.success("✅ Tabela verificada/criada")
        
        dados_usuario = db.buscar_dados_usuario(email_usuario)
        nome_usuario = dados_usuario.get('nome', 'Usuário') if dados_usuario else 'Usuário'
        
        st.info(f"👤 Usuário identificado: {nome_usuario}")
        
        total_formularios = len(st.session_state.get('formularios_data', {}))
        
        st.info(f"📋 Total de formulários: {total_formularios}")
        st.info("💾 Salvando registro...")
        
        preenchimento_id = db.registrar_preenchimento_finalizado(
            email_usuario=email_usuario,
            nome_usuario=nome_usuario,
            unidade=unidade_usuario,
            competencia=competencia_usuario,
            total_formularios=total_formularios,
            dados_extras=dados_extras,
            status_envio=status_envio
        )
        
        if preenchimento_id:
            st.success(f"✅ Registro salvo com sucesso! ID: {preenchimento_id}")
            return preenchimento_id
        else:
            st.error("❌ Método de registro retornou None")
            return None
            
    except AttributeError as e:
        st.error(f"❌ Erro de atributo ao acessar banco: {str(e)}")
        st.error("Verifique se o método 'registrar_preenchimento_finalizado' existe na classe DatabaseManagerPostgres")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro ao registrar no banco: {str(e)}")
        st.exception(e)
        return None