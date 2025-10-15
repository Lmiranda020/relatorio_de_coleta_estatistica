import pandas as pd
import os
import streamlit as st
from config.constants import DEPARA_CRITICIDADE


def tratativa_criticidade_api(output_dir, competencia):
    """
    Função para tratar arquivos de criticidade da API aplicando de-para na coluna de ponderação
    
    Args:
        output_dir (str): Diretório onde estão os arquivos
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

    inicio_arquivo = "Area_Criticidade_API_"
    
    with temp_container.container():
        st.info("🔍 Procurando arquivos para processar...")
    
    # Lista todos os arquivos no diretório
    try:
        arquivos = os.listdir(output_dir)
    except FileNotFoundError:
        temp_container.empty()
        st.error(f"Erro: Diretório não encontrado: {output_dir}")
        return False
    
    # Filtra apenas os arquivos que começam com o prefixo desejado
    arquivos_filtrados = [arquivo for arquivo in arquivos 
                         if arquivo.startswith(inicio_arquivo) and arquivo.endswith('.csv')]
    
    if not arquivos_filtrados:
        temp_container.empty()
        st.error(f"Nenhum arquivo encontrado com o prefixo '{inicio_arquivo}' no diretório {output_dir}")
        return False
    
    with temp_container.container():
        st.info(f"📁 Encontrados {len(arquivos_filtrados)} arquivo(s) para processar")
    
    # Processa cada arquivo encontrado
    for arquivo in arquivos_filtrados:
        caminho_arquivo = os.path.join(output_dir, arquivo)
        
        with temp_container.container():
            st.info(f"⚙️ Processando arquivo: {arquivo}")
        
        try:
            # Lê o arquivo atual
            df_original = pd.read_csv(caminho_arquivo, sep=';')
            
            with temp_container.container():
                st.info(f"📊 Arquivo carregado com {len(df_original)} registros")
            
            # Limpa espaços extras dos nomes das colunas
            df_original.columns = df_original.columns.str.strip()
            
            # Verifica se as colunas necessárias existem
            if 'Centro de Custo' not in df_original.columns:
                temp_container.empty()
                st.error(f"Erro: Coluna 'Centro de Custo' não encontrada no arquivo {arquivo}")
                st.error(f"Colunas disponíveis: {list(df_original.columns)}")
                return False
                
            if 'Ponderação' not in df_original.columns:
                temp_container.empty()
                st.warning(f"Aviso: Coluna 'Ponderação' não encontrada no arquivo {arquivo}")
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
                st.info(f"🔄 Fazendo correspondência entre arquivos...")
            
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
            
            with temp_container.container():
                st.info(f"💾 Salvando arquivo atualizado...")
            
            # Salva o arquivo atualizado (sobrescreve o original)
            df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')

            # ✅ ADICIONE ESTAS LINHAS: Atualiza o session_state com os dados corrigidos
            nome_formulario_session = 'Area_Criticidade_API'  # Nome usado no session_state
            if nome_formulario_session in st.session_state.get('formularios_data', {}):
                st.session_state['formularios_data'][nome_formulario_session] = df_final.copy()
                st.info(f"🔄 Session state atualizado para {nome_formulario_session}")
            
            # Se chegou até aqui sem erro, limpa as mensagens temporárias
            temp_container.empty()
            
            # Mostra apenas o resultado final de sucesso
            # st.success(f"✅ Arquivo {arquivo} atualizado com sucesso! ({registros_com_match} registros alterados)")
            return True
        
        except Exception as e:
            # Em caso de erro, limpa as mensagens temporárias e mostra o erro
            temp_container.empty()
            st.error(f"❌ Erro ao processar arquivo {arquivo}: {e}")
            return False
    
    # Mensagem final apenas se tudo deu certo
    st.success(f"🎉 Processamento concluído com sucesso para a competência {competencia}")
    return True