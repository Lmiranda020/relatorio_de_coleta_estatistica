import pandas as pd
import os
import streamlit as st
from config.constants import DEPARA_CRITICIDADE


def tratativa_criticidade_api(output_dir, competencia):
    """
    Função para tratar arquivo de criticidade da API aplicando de-para na coluna de ponderação
    
    LÓGICA:
    - Quando vem da API: 1 arquivo "Area_Criticidade_API" com TODAS as criticidades juntas
    - Aplica o de-para de ponderação usando Centro de Custo
    - Salva 1 arquivo atualizado (não 3)
    - Quando manual: 3 arquivos separados já vêm corretos do preenchimento
    
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

    # ========================================================================
    # BUSCA APENAS O ARQUIVO "Area_Criticidade_API" NA MEMÓRIA
    # ========================================================================
    
    with temp_container.container():
        st.info("🔍 Procurando dados de Area_Criticidade_API na memória...")
    
    # Verificar se os dados de criticidade estão na memória
    formularios_data = st.session_state.get('formularios_data', {})
    
    # NOME EXATO do formulário que vem da API
    nome_formulario_api = "Area_Criticidade_API"
    
    if nome_formulario_api not in formularios_data:
        temp_container.empty()
        st.warning(f"⚠️ '{nome_formulario_api}' não encontrado na memória")
        st.info("Isso é normal se você preencheu os formulários manualmente (3 arquivos separados)")
        return True  # Retorna True porque não é erro, apenas não há dados da API
    
    with temp_container.container():
        st.info(f"📁 Dados de '{nome_formulario_api}' encontrados na memória")
    
    # ========================================================================
    # PROCESSA O ARQUIVO ÚNICO DA API
    # ========================================================================
    
    with temp_container.container():
        st.info(f"⚙️ Processando: {nome_formulario_api}")
    
    try:
        # Pega dados da memória
        df_original = formularios_data[nome_formulario_api].copy()
        
        with temp_container.container():
            st.info(f"📊 Dados carregados com {len(df_original)} registros")
        
        # Limpa espaços extras dos nomes das colunas
        df_original.columns = df_original.columns.str.strip()
        
        # Verifica se as colunas necessárias existem
        if 'Centro de Custo' not in df_original.columns:
            temp_container.empty()
            st.error(f"Erro: Coluna 'Centro de Custo' não encontrada em {nome_formulario_api}")
            st.error(f"Colunas disponíveis: {list(df_original.columns)}")
            return False
            
        if 'Ponderação' not in df_original.columns:
            temp_container.empty()
            st.warning(f"Aviso: Coluna 'Ponderação' não encontrada em {nome_formulario_api}")
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
            st.info(f"🔄 Aplicando de-para de ponderação...")
        
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
        # ATUALIZA MEMÓRIA E SALVA APENAS 1 ARQUIVO
        # ========================================================================
        
        with temp_container.container():
            st.info(f"🔄 Atualizando dados na memória...")
        
        # Atualiza o session_state com os dados corrigidos
        st.session_state['formularios_data'][nome_formulario_api] = df_final.copy()
        
        with temp_container.container():
            st.info(f"💾 Salvando arquivo único no disco...")
        
        # Define o nome do arquivo (APENAS UM)
        nome_arquivo = f"{nome_formulario_api}_{competencia}.csv"
        caminho_arquivo = os.path.join(output_dir, nome_arquivo)
        
        # Salva o arquivo atualizado no disco
        df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
        
        # Limpa mensagens temporárias
        temp_container.empty()
        
        # Mensagem final de sucesso
        st.success(f"✅ {nome_formulario_api} processado com sucesso!")
        st.info(f"📊 {registros_com_match} ponderações atualizadas")
        st.info(f"💾 Arquivo salvo: {nome_arquivo}")
        
        return True
    
    except KeyError as ke:
        temp_container.empty()
        st.error(f"❌ Erro ao processar {nome_formulario_api}: Chave não encontrada - {ke}")
        return False
        
    except Exception as e:
        temp_container.empty()
        st.error(f"❌ Erro ao processar {nome_formulario_api}: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False