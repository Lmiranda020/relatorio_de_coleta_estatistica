import pandas as pd
import os
import streamlit as st
from config.constants import DEPARA_CRITICIDADE


def tratativa_criticidade_api(output_dir, competencia):
    """
    Função para tratar arquivos de criticidade da API aplicando de-para na coluna de ponderação
    E depois separar em 3 arquivos filtrados por tipo de criticidade
    
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
    
    # Busca na memória do Streamlit
    formularios_data = st.session_state.get('formularios_data', {})
    
    # Procura por chaves que começam com "Area_Criticidade_API"
    arquivo_encontrado = None
    
    for nome_formulario in formularios_data.keys():
        if nome_formulario.startswith(inicio_arquivo) or nome_formulario == 'Area_Criticidade_API':
            arquivo_encontrado = nome_formulario
            break
    
    if not arquivo_encontrado:
        temp_container.empty()
        st.warning(f"⚠️ Nenhum arquivo encontrado com o prefixo '{inicio_arquivo}' na memória")
        st.info("Isso é normal se você preencheu os formulários manualmente")
        return True
    
    with temp_container.container():
        st.info(f"📁 Arquivo encontrado: {arquivo_encontrado}")
    
    try:
        # Carrega o DataFrame da memória
        df_original = formularios_data[arquivo_encontrado].copy()
        
        with temp_container.container():
            st.info(f"📊 Arquivo carregado com {len(df_original)} registros")
        
        # Limpa espaços extras dos nomes das colunas
        df_original.columns = df_original.columns.str.strip()
        
        # Verifica se as colunas necessárias existem
        if 'Centro de Custo' not in df_original.columns:
            temp_container.empty()
            st.error(f"Erro: Coluna 'Centro de Custo' não encontrada")
            st.error(f"Colunas disponíveis: {list(df_original.columns)}")
            return False
            
        if 'Ponderação' not in df_original.columns:
            temp_container.empty()
            st.warning(f"Aviso: Coluna 'Ponderação' não encontrada")
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
        
        # ✅ ATUALIZA O ARQUIVO PRINCIPAL NA MEMÓRIA
        st.session_state['formularios_data']['Area_Criticidade_API'] = df_final.copy()
        
        # ✅ SALVA O ARQUIVO PRINCIPAL NO DISCO
        competencia_normalizada = competencia.replace("/", "-").replace(" ", "_")
        nome_arquivo_principal = f"Area_Criticidade_API_{competencia_normalizada}.csv"
        caminho_arquivo_principal = os.path.join(output_dir, nome_arquivo_principal)
        df_final.to_csv(caminho_arquivo_principal, index=False, sep=';', encoding='utf-8-sig')
        
        with temp_container.container():
            st.info(f"💾 Arquivo principal salvo e atualizado na memória")
        
        # ============================================================
        # *** 🔥 NOVA PARTE: FILTRAR E SALVAR OS 3 FORMULÁRIOS ***
        # ============================================================
        
        with temp_container.container():
            st.info("📂 Criando os 3 arquivos filtrados por tipo de criticidade...")
        
        # Dicionário com os mapeamentos: Nome do Formulário → Texto que deve conter na Ponderação
        mapeamento_criticidade = {
            "Área (m²) x Nível de Criticidade (Área Crítica - I)": "Área Crítica - I",
            "Área (m²) x Nível de Criticidade (Área Semi Crítica)": "Área Semi Crítica",
            "Área (m²) x Nível de Criticidade (Área Não Crítica - I)": "Área Não Crítica - I"
        }
        
        arquivos_criados = []
        
        for nome_formulario, texto_filtro in mapeamento_criticidade.items():
            # Filtra apenas as linhas que contêm o texto específico na coluna Ponderação
            df_filtrado = df_final[
                df_final['Ponderação'].str.contains(texto_filtro, case=False, na=False)
            ].copy()
            
            if not df_filtrado.empty:
                # Salva no session_state
                st.session_state['formularios_data'][nome_formulario] = df_filtrado.copy()
                
                # Salva no disco
                nome_arquivo = f"{nome_formulario}_{competencia_normalizada}.csv"
                caminho_arquivo = os.path.join(output_dir, nome_arquivo)
                df_filtrado.to_csv(caminho_arquivo, index=False, sep=';', encoding='utf-8-sig')
                
                arquivos_criados.append(nome_formulario)
                
                with temp_container.container():
                    st.info(f"  ✅ {nome_formulario}: {len(df_filtrado)} registros")
            else:
                with temp_container.container():
                    st.warning(f"  ⚠️ {nome_formulario}: Nenhum registro encontrado com '{texto_filtro}'")
        
        # Limpa mensagens temporárias
        temp_container.empty()
        
        # Mensagem final de sucesso
        st.success(f"✅ Tratativa concluída!")
        st.success(f"📊 {registros_com_match} ponderações atualizadas")
        st.success(f"📂 {len(arquivos_criados)} arquivos de criticidade criados")
        
        # Lista os arquivos criados
        with st.expander("📋 Arquivos de criticidade criados"):
            for form in arquivos_criados:
                registros = len(st.session_state['formularios_data'][form])
                st.write(f"• {form} ({registros} registros)")
        
        return True
    
    except KeyError as ke:
        temp_container.empty()
        st.error(f"❌ Erro ao acessar {arquivo_encontrado} na memória: {ke}")
        return False
        
    except Exception as e:
        temp_container.empty()
        st.error(f"❌ Erro ao processar arquivo: {e}")
        st.exception(e)
        return False