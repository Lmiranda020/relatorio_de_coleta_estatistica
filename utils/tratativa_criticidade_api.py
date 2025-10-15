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

    inicio_arquivo = f'Area_Criticidade_API_{competencia}'
    
    with temp_container.container():
        st.info("🔍 Procurando arquivos para processar...")
    
    # Busca na memória do Streamlit
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
        st.info("Isso é normal se você preencheu os formulários manualmente")
        return True  # Retorna True pois não é erro
    
    with temp_container.container():
        st.info(f"📁 Encontrados {len(arquivos_encontrados)} arquivo(s) para processar")
    
    # Processa cada arquivo encontrado
    for arquivo in arquivos_encontrados:
        
        with temp_container.container():
            st.info(f"⚙️ Processando arquivo: {arquivo}")
        
        try:
            # ✅ Lê da MEMÓRIA (não do disco)
            df_original = formularios_data[arquivo].copy()
            
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
            
            # ✅ ATUALIZA A MEMÓRIA PRIMEIRO
            with temp_container.container():
                st.info(f"🔄 Atualizando session_state...")
            
            st.session_state['formularios_data'][arquivo] = df_final.copy()
            
            # ✅ SALVA NO DISCO DEPOIS (para backup)
            with temp_container.container():
                st.info(f"💾 Salvando arquivo no disco...")
            
            # Cria o nome do arquivo para salvar
            competencia_normalizada = competencia.replace("/", "-").replace(" ", "_")
            
            # Se já tem a competência no nome, não adiciona de novo
            if competencia_normalizada in arquivo:
                nome_arquivo = f"{arquivo}.csv"
            else:
                nome_arquivo = f"{arquivo}_{competencia_normalizada}.csv"
            
            caminho_arquivo = os.path.join(output_dir, nome_arquivo)
            
            # Salva o arquivo atualizado
            df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
            
            # Se chegou até aqui sem erro, limpa as mensagens temporárias
            temp_container.empty()
            
            st.success(f"✅ {arquivo} processado com sucesso!")
            st.info(f"📊 {registros_com_match} ponderações atualizadas")
            
            return True
        
        except KeyError as ke:
            temp_container.empty()
            st.error(f"❌ Erro ao acessar {arquivo} na memória: {ke}")
            return False
            
        except Exception as e:
            temp_container.empty()
            st.error(f"❌ Erro ao processar arquivo {arquivo}: {e}")
            return False
    
    # Mensagem final apenas se tudo deu certo
    st.success(f"🎉 Processamento concluído com sucesso para a competência {competencia}")
    return True