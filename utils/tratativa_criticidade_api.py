import pandas as pd
import os
import streamlit as st
from config.constants import DEPARA_CRITICIDADE


def tratativa_criticidade_api(output_dir, competencia):
    """
    Função para tratar arquivos de criticidade da API aplicando de-para na coluna de ponderação
    
    Args:
        output_dir (str): Diretório onde os arquivos serão salvos
        competencia (str): Competência para processamento
    """
    
    # Container para mensagens temporárias
    temp_container = st.empty()
    
    with temp_container.container():
        st.info("🔄 Carregando arquivo de de-para...")
    
    # Carrega o arquivo de de-para
    try:
        de_para_criticidade = pd.read_excel(DEPARA_CRITICIDADE)
        with temp_container.container():
            st.info(f"✅ Arquivo de de-para carregado com {len(de_para_criticidade)} registros")
    except FileNotFoundError:
        temp_container.empty()
        st.error(f"Erro: Arquivo de de-para não encontrado: {DEPARA_CRITICIDADE}")
        return False
    except Exception as e:
        temp_container.empty()
        st.error(f"Erro ao carregar arquivo de de-para: {e}")
        return False

    inicio_arquivo = "Area_Criticidade_API"
    
    with temp_container.container():
        st.info("🔍 Procurando arquivos para processar na memória...")
    
    # ========================================================================
    # BUSCA NA MEMÓRIA (session_state)
    # ========================================================================
    formularios_data = st.session_state.get('formularios_data', {})
    
    # Procura por chaves que começam com "Area_Criticidade_API"
    arquivos_encontrados = []
    
    for nome_formulario in formularios_data.keys():
        # Verifica se é um formulário de criticidade da API
        if nome_formulario.startswith(inicio_arquivo):
            arquivos_encontrados.append(nome_formulario)
    
    if not arquivos_encontrados:
        temp_container.empty()
        st.warning(f"⚠️ Nenhum arquivo encontrado com o prefixo '{inicio_arquivo}' na memória")
        st.info("Isso é normal se você preencheu os formulários manualmente (3 arquivos separados)")
        return True  # Retorna True porque não é erro
    
    with temp_container.container():
        st.info(f"📁 Encontrados {len(arquivos_encontrados)} arquivo(s) para processar")
    
    # Processa cada arquivo encontrado
    for nome_formulario in arquivos_encontrados:
        
        with temp_container.container():
            st.info(f"⚙️ Processando: {nome_formulario}")
        
        try:
            # ========================================================================
            # LÊ DA MEMÓRIA (NÃO DO DISCO!)
            # ========================================================================
            df_original = formularios_data[nome_formulario].copy()
            
            with temp_container.container():
                st.info(f"📊 Dados carregados com {len(df_original)} registros")
            
            # Limpa espaços extras dos nomes das colunas
            df_original.columns = df_original.columns.str.strip()
            
            # Verifica se as colunas necessárias existem
            if 'Centro de Custo' not in df_original.columns:
                temp_container.empty()
                st.error(f"Erro: Coluna 'Centro de Custo' não encontrada em {nome_formulario}")
                st.error(f"Colunas disponíveis: {list(df_original.columns)}")
                return False
                
            if 'Ponderação' not in df_original.columns:
                temp_container.empty()
                st.warning(f"Aviso: Coluna 'Ponderação' não encontrada em {nome_formulario}")
                # Se não existir, cria a coluna
                df_original['Ponderação'] = None
            
            # Verifica se o de-para tem as colunas necessárias
            if 'Centro de Custo' not in de_para_criticidade.columns:
                temp_container.empty()
                st.error("Erro: Coluna 'Centro de Custo' não encontrada no arquivo de de-para")
                return False
                
            if 'Nova Ponderação' not in de_para_criticidade.columns:
                temp_container.empty()
                st.error("Erro: Coluna 'Nova Ponderação' não encontrada no arquivo de de-para")
                return False
            
            with temp_container.container():
                st.info(f"🔄 Fazendo correspondência entre dados...")
            
            # Faz o merge (VLOOKUP) usando Centro de Custo como chave
            df_atualizado = df_original.merge(
                de_para_criticidade[['Centro de Custo', 'Nova Ponderação']], 
                on='Centro de Custo', 
                how='left'
            )
            
            # Conta quantos registros terão a ponderação atualizada
            registros_com_match = df_atualizado['Nova Ponderação'].notna().sum()
            
            with temp_container.container():
                st.info(f"🎯 Encontrados {registros_com_match} registros com correspondência")
            
            # Atualiza a coluna Ponderação onde houver match
            mask = df_atualizado['Nova Ponderação'].notna()
            df_atualizado.loc[mask, 'Ponderação'] = df_atualizado.loc[mask, 'Nova Ponderação']
            
            # Remove a coluna auxiliar do merge
            df_final = df_atualizado.drop(columns=['Nova Ponderação'])
            
            # ========================================================================
            # ATUALIZA A MEMÓRIA PRIMEIRO
            # ========================================================================
            with temp_container.container():
                st.info(f"🔄 Atualizando dados na memória...")
            
            st.session_state['formularios_data'][nome_formulario] = df_final.copy()
            
            # ========================================================================
            # SALVA NO DISCO DEPOIS (para backup)
            # ========================================================================
            with temp_container.container():
                st.info(f"💾 Salvando arquivo no disco...")
            
            # Define o nome do arquivo para salvar
            # Se o nome já contém a competência, usa direto; senão adiciona
            if competencia.replace("/", "-").replace(" ", "_") in nome_formulario:
                nome_arquivo = f"{nome_formulario}.csv"
            else:
                nome_arquivo = f"{nome_formulario}_{competencia}.csv".replace("/", "-").replace(" ", "_")
            
            caminho_arquivo = os.path.join(output_dir, nome_arquivo)
            
            # Salva o arquivo atualizado
            df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
            
            # Limpa mensagens temporárias
            temp_container.empty()
            
            # Mensagem de sucesso
            st.success(f"✅ {nome_formulario} processado com sucesso!")
            st.info(f"📊 {registros_com_match} ponderações atualizadas")
            
            return True
        
        except KeyError as ke:
            temp_container.empty()
            st.error(f"❌ Erro ao acessar dados de {nome_formulario}: {ke}")
            st.error("Verifique se os dados foram carregados corretamente da API")
            return False
            
        except Exception as e:
            temp_container.empty()
            st.error(f"❌ Erro ao processar {nome_formulario}: {e}")
            import traceback
            st.error(traceback.format_exc())
            return False
    
    # Mensagem final
    temp_container.empty()
    st.success(f"🎉 Tratativa de criticidade concluída para a competência {competencia}")
    return True