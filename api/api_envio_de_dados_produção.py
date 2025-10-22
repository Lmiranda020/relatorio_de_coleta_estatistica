import requests
import pandas as pd
import json
import os
import glob
import datetime
import streamlit as st
from data.limpeza_base_de_para_rpa_vs_kpih import (
    obter_competencia_usuario,
    obter_unidade_id_da_sessao
)
from api.api_centro_custo import ajustar_competencia
from config.constants import get_token_unidades_importacao

def encontrar_arquivo_producao(diretorio_saida, competencia):
    """Encontra o arquivo de produção"""
    try:
        padrao_arquivo = f"Produção_{competencia}*.csv"
        padrao_arquivo = padrao_arquivo.replace("/", "-").replace(" ", "_")
        caminho_busca = os.path.join(diretorio_saida, padrao_arquivo)
        arquivos_encontrados = glob.glob(caminho_busca)
        
        if not arquivos_encontrados:
            return None
        
        return max(arquivos_encontrados, key=os.path.getctime)
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao buscar arquivo de produção: {str(e)}")
        return None


def transformar_dados_producao(caminho_arquivo):
    """
    Transforma dados de produção do Excel/CSV para formato da API.
    Formato esperado do arquivo: colunas 'Ponderação', 'Centro de Custo' e 'Quantidade'
    """
    try:
        # Tenta ler como CSV primeiro
        try:
            df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8-sig')
        except:
            # Se falhar, tenta como Excel
            df = pd.read_excel(caminho_arquivo)
        
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
        
        return dados_api if dados_api else None
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo de produção: {str(e)}")
        st.exception(e)
        return None

def analisar_resposta_producao(response_json, dados_enviados):
    """
    Analisa a resposta da API de produção para identificar erros.
    Mesma lógica robusta usada em estatísticas.
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
            # Formato 1: {"message": "...", "errors": {"0": "erro", "1": "erro"}}
            if 'errors' in response_json:
                errors_dict = response_json['errors']
                
                if isinstance(errors_dict, dict):
                    # Itera pelos erros usando o índice
                    for indice_str, mensagem_erro in errors_dict.items():
                        try:
                            idx = int(indice_str)
                            
                            # Verifica se o índice é válido
                            if 0 <= idx < len(dados_enviados):
                                registro_original = dados_enviados[idx]
                                
                                resultado['registros_com_erro'].append({
                                    'motivo': str(mensagem_erro)
                                })
                            else:
                                # Índice fora do range - registra mesmo assim
                                resultado['registros_com_erro'].append({
                                    'motivo': str(mensagem_erro)
                                })
                                
                        except (ValueError, TypeError) as e:
                            st.warning(f"⚠️ Erro ao processar índice '{indice_str}': {e}")
                            # Registra erro mesmo sem conseguir parsear índice
                            resultado['registros_com_erro'].append({
                                'indice': indice_str,
                                'motivo': str(mensagem_erro)
                            })
                    
                    resultado['total_rejeitados'] = len(errors_dict)
                
                elif isinstance(errors_dict, list):
                    # Se errors vier como lista
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
            
            # Calcula aceitos
            resultado['total_aceitos'] = resultado['total_enviados'] - resultado['total_rejeitados']
        
        # Define se foi parcial
        resultado['parcial'] = resultado['total_rejeitados'] > 0
        
        # Mensagem resumo
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
        # Em caso de erro, assume que tudo foi aceito (fallback seguro)
        resultado['total_aceitos'] = resultado['total_enviados']
        resultado['mensagem_resumo'] = f"⚠️ {resultado['total_enviados']} enviados (análise de erros falhou)"
        return resultado

def enviar_producao_para_api():
    """
    Envia dados de produção para a API.
    RETORNA: (sucesso: bool, dados_extras: dict)
    """
    try:
        unidade_id = obter_unidade_id_da_sessao()
        competencia_usuario = obter_competencia_usuario()
        diretorio_saida = st.session_state.get('output_dir', None)
        
        dados_extras = {
            'timestamp_envio_producao': datetime.datetime.now().isoformat()
        }
        
        if not unidade_id or not competencia_usuario or not diretorio_saida:
            st.warning("⚠️ Produção não enviada - dados incompletos")
            dados_extras['erro_producao'] = 'dados_incompletos'
            return False, dados_extras
        
        caminho_arquivo = encontrar_arquivo_producao(diretorio_saida, competencia_usuario)
        if not caminho_arquivo:
            st.info("ℹ️ Arquivo de produção não encontrado - pulando envio")
            dados_extras['erro_producao'] = 'arquivo_nao_encontrado'
            return False, dados_extras
        
        st.info(f"📊 Processando arquivo: {os.path.basename(caminho_arquivo)}")
        dados_extras['arquivo_producao_enviado'] = os.path.basename(caminho_arquivo)
        
        dados_para_envio = transformar_dados_producao(caminho_arquivo)
        if not dados_para_envio:
            st.warning("⚠️ Nenhum dado válido de produção para enviar")
            dados_extras['erro_producao'] = 'dados_invalidos'
            return False, dados_extras
        
        dados_extras['total_registros_producao'] = len(dados_para_envio)
        st.success(f"✅ {len(dados_para_envio)} registro(s) de produção preparado(s)")
        
        token = get_token_unidades_importacao()
        if not token:
            st.warning("⚠️ Token não disponível - produção não enviada")
            dados_extras['erro_producao'] = 'token_indisponivel'
            return False, dados_extras
        
        # Ajustar competência para formato MM/AAAA
        competencia_ajustada = ajustar_competencia(competencia_usuario)
        
        # PAYLOAD NO FORMATO EXATO DA API
        payload = {
            "competencia": competencia_ajustada,
            "dados": dados_para_envio
        }
        
        # Debug do payload
        with st.expander("🔍 Detalhes do Payload de Produção"):
            st.write(f"**Competência:** {payload['competencia']}")
            st.write(f"**Total de registros:** {len(payload['dados'])}")
            if payload['dados']:
                st.write("**Exemplo do primeiro registro:**")
                st.json(payload['dados'][0])
            st.write("**Payload completo:**")
            st.json(payload)
        
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
                
                # Verifica se é envio parcial
                mensagem_api = resposta_api.get('message', resposta_api.get('mensagem', ''))
                is_parcial = 'parcialmente' in mensagem_api.lower()
                
                # Analisa a resposta para identificar erros
                analise = analisar_resposta_producao(resposta_api, dados_para_envio)
                dados_extras['analise_envio_producao'] = analise
                
                # 🔥 SALVAR NO SESSION_STATE
                st.session_state['resultado_envio_producao'] = {
                    'sucesso': True,
                    'analise': analise,
                    'resposta_api': resposta_api,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
                with st.expander("📄 Detalhes da resposta da API"):
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)
                
                email_usuario = st.session_state.get('email_usuario')
                unidade_usuario = st.session_state.get('unidade_usuario')
                
                if email_usuario and unidade_usuario:
                    st.info("💾 Registrando envio no banco de dados...")
                    
                    preenchimento_id = registrar_no_banco(
                        email_usuario=email_usuario,
                        unidade_usuario=unidade_usuario,
                        competencia_usuario=competencia_usuario,
                        dados_extras=dados_extras,
                        status_envio='enviado_api_sucesso'
                    )
                    
                    if preenchimento_id:
                        st.success(f"✅ Registro #{preenchimento_id} salvo no banco!")
                        dados_extras['preenchimento_id'] = preenchimento_id
                    else:
                        st.warning("⚠️ Envio bem-sucedido mas falha ao registrar no banco")
                else:
                    st.warning("⚠️ Email/Unidade não encontrados - registro no banco pulado")

                
                return True, dados_extras
                
            elif response.status_code == 400:
                st.error(f"❌ Erro de validação (400)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = f'http_400'
                return False, dados_extras
                
            elif response.status_code == 401:
                st.error(f"❌ Token inválido (401)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = f'http_401'
                return False, dados_extras
                
            elif response.status_code == 422:
                st.error(f"❌ Erro de validação de dados (422)")
                with st.expander("📄 Ver erro"):
                    st.error(response.text)
                dados_extras['erro_producao'] = f'http_422'
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
# FUNÇÃO DE REGISTRO NO BANCO (MESMA DO CÓDIGO ORIGINAL)
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
            st.rerun()
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