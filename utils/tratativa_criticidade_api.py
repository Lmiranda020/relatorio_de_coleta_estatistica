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

    with temp_container.container():
        st.info("🔍 Procurando dados de criticidade na memória...")
    
    # Verificar se os dados de criticidade estão na memória
    formularios_data = st.session_state.get('formularios_data', {})
    
    # Lista de formulários de criticidade que podem existir
    formularios_criticidade = [
        "Area_Criticidade_API",
        "Área (m²) x Nível de Criticidade (Área Crítica - I)",
        "Área (m²) x Nível de Criticidade (Área Semi Crítica)",
        "Área (m²) x Nível de Criticidade (Área Não Crítica - I)"
    ]
    
    # Filtra apenas os formulários de criticidade que existem na memória
    formularios_encontrados = [f for f in formularios_criticidade if f in formularios_data]
    
    if not formularios_encontrados:
        temp_container.empty()
        st.error(f"Nenhum formulário de criticidade encontrado na memória")
        st.info("Formulários esperados: " + ", ".join(formularios_criticidade))
        return False
    
    with temp_container.container():
        st.info(f"📁 Encontrados {len(formularios_encontrados)} formulário(s) de criticidade para processar")
    
    # Processa cada formulário encontrado
    sucesso_geral = True
    
    for nome_formulario in formularios_encontrados:
        with temp_container.container():
            st.info(f"⚙️ Processando: {nome_formulario}")
        
        try:
            # ========================================================================
            # MUDANÇA: Pegar dados da memória ao invés de ler CSV
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
                sucesso_geral = False
                continue
                
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
            # IMPORTANTE: Atualiza PRIMEIRO a memória, DEPOIS salva no disco
            # ========================================================================
            
            with temp_container.container():
                st.info(f"🔄 Atualizando dados na memória...")
            
            # Atualiza o session_state com os dados corrigidos
            st.session_state['formularios_data'][nome_formulario] = df_final.copy()
            
            with temp_container.container():
                st.info(f"💾 Salvando arquivo no disco...")
            
            # Define o nome do arquivo (mantém compatibilidade com código existente)
            nome_arquivo = f"{nome_formulario}_{competencia}.csv".replace("/", "-").replace(" ", "_")
            caminho_arquivo = os.path.join(output_dir, nome_arquivo)
            
            # Salva o arquivo atualizado no disco
            df_final.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
            
            # Se chegou até aqui sem erro, mostra sucesso
            with temp_container.container():
                st.success(f"✅ {nome_formulario} processado: {registros_com_match} ponderações atualizadas")
        
        except KeyError as ke:
            temp_container.empty()
            st.error(f"❌ Erro ao processar {nome_formulario}: Chave não encontrada - {ke}")
            sucesso_geral = False
            continue
            
        except Exception as e:
            temp_container.empty()
            st.error(f"❌ Erro ao processar {nome_formulario}: {e}")
            sucesso_geral = False
            continue
    
    # Limpa mensagens temporárias
    temp_container.empty()
    
    # Mensagem final
    if sucesso_geral:
        st.success(f"🎉 Tratativa de criticidade concluída para a competência {competencia}")
        st.info(f"✅ {len(formularios_encontrados)} formulário(s) processado(s) com sucesso")
    else:
        st.warning("⚠️ Tratativa concluída com alguns erros. Verifique as mensagens acima.")
    
    return sucesso_geral