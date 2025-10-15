import pandas as pd
import os
import streamlit as st
from config.constants import DEPARA_CRITICIDADE


def tratativa_criticidade_api(output_dir, competencia):
    """
    Função para tratar arquivos de criticidade da API aplicando de-para na coluna de ponderação
    VERSÃO ATUALIZADA: Usa session_state ao invés de arquivos CSV
    
    Args:
        output_dir (str): Diretório onde os arquivos serão salvos (backup)
        competencia (str): Competência para processamento
    """
    
    st.info("🔄 Carregando arquivo de de-para...")
    
    # Carrega o arquivo de de-para
    try:
        de_para_criticidade = pd.read_excel(DEPARA_CRITICIDADE)
        st.info(f"✅ Arquivo de de-para carregado com {len(de_para_criticidade)} registros")
    except FileNotFoundError:
        st.error(f"Erro: Arquivo de de-para não encontrado: {DEPARA_CRITICIDADE}")
        return False
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de de-para: {e}")
        return False

    st.info("🔍 Procurando dados de criticidade na memória...")
    
    # Busca os dados de criticidade no session_state
    formularios_data = st.session_state.get('formularios_data', {})
    
    # Procura por qualquer formulário relacionado a criticidade
    formularios_criticidade = []
    nomes_criticidade = [
        'Area_Criticidade_API',
        'Área (m²) x Nível de Criticidade (Área Crítica - I)',
        'Área (m²) x Nível de Criticidade (Área Semi Crítica)',
        'Área (m²) x Nível de Criticidade (Área Não Crítica - I)'
    ]
    
    for nome_form in nomes_criticidade:
        if nome_form in formularios_data:
            formularios_criticidade.append(nome_form)
    
    if not formularios_criticidade:
        st.warning("⚠️ Nenhum formulário de criticidade encontrado na memória")
        return False
    
    st.info(f"📁 Encontrados {len(formularios_criticidade)} formulário(s) de criticidade")
    
    # Processa cada formulário encontrado
    for nome_formulario in formularios_criticidade:
        st.info(f"⚙️ Processando: {nome_formulario}")
        
        try:
            # Pega o DataFrame do session_state
            df_original = formularios_data[nome_formulario].copy()
            
            st.info(f"📊 Dados carregados com {len(df_original)} registros")
            
            # Limpa espaços extras dos nomes das colunas
            df_original.columns = df_original.columns.str.strip()
            
            # Verifica se as colunas necessárias existem
            if 'Centro de Custo' not in df_original.columns:
                st.error(f"Erro: Coluna 'Centro de Custo' não encontrada em {nome_formulario}")
                st.error(f"Colunas disponíveis: {list(df_original.columns)}")
                return False
                
            if 'Ponderação' not in df_original.columns:
                st.warning(f"Aviso: Coluna 'Ponderação' não encontrada em {nome_formulario}")
                df_original['Ponderação'] = None
            
            # Verifica se o de-para tem as colunas necessárias
            if 'Centro de Custo' not in de_para_criticidade.columns:
                st.error("Erro: Coluna 'Centro de Custo' não encontrada no arquivo de de-para")
                return False
                
            if 'Nova Ponderação' not in de_para_criticidade.columns:
                st.error("Erro: Coluna 'Nova Ponderação' não encontrada no arquivo de de-para")
                return False
            
            st.info(f"🔄 Fazendo correspondência...")
            
            # Faz o merge (VLOOKUP) usando Centro de Custo como chave
            df_atualizado = df_original.merge(
                de_para_criticidade[['Centro de Custo', 'Nova Ponderação']], 
                on='Centro de Custo', 
                how='left'
            )
            
            # Conta quantos registros terão a ponderação atualizada
            registros_com_match = df_atualizado['Nova Ponderação'].notna().sum()
            
            st.info(f"🎯 Encontrados {registros_com_match} registros com correspondência")
            
            # Atualiza a coluna Ponderação onde houver match
            mask = df_atualizado['Nova Ponderação'].notna()
            df_atualizado.loc[mask, 'Ponderação'] = df_atualizado.loc[mask, 'Nova Ponderação']
            
            # Remove a coluna auxiliar do merge
            df_final = df_atualizado.drop(columns=['Nova Ponderação'])
            
            # ✅ ATUALIZA NO SESSION_STATE
            st.session_state['formularios_data'][nome_formulario] = df_final.copy()
            st.success(f"✅ {nome_formulario} atualizado na memória!")
            
            # 💾 SALVA TAMBÉM NO DISCO (backup)
            st.info(f"💾 Salvando backup em disco...")
            
            nome_arquivo = f"{nome_formulario}_{competencia}.csv".replace("/", "-").replace(" ", "_")
            caminho_arquivo = os.path.join(output_dir, nome_arquivo)
            
            df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Backup salvo: {nome_arquivo}")
            
            return True
        
        except Exception as e:
            st.error(f"❌ Erro ao processar {nome_formulario}: {e}")
            st.exception(e)
            return False
    
    st.success(f"🎉 Processamento de criticidade concluído!")
    return True