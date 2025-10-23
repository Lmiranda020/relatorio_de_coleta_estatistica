import streamlit as st
import pandas as pd

def carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario):
    """
    Carrega dados salvos anteriormente para a competência, unidade e formulário específico
    """
    try:
        # Verifica se existe dados salvos no session_state
        if 'formularios_data' not in st.session_state:
            return {}
        
        # Verifica se o formulário específico foi salvo
        if nome_formulario not in st.session_state['formularios_data']:
            return {}
        
        # Pega o DataFrame salvo do formulário
        df_salvo = st.session_state['formularios_data'][nome_formulario]
        
        # Verifica se o DataFrame não está vazio
        if df_salvo is None or df_salvo.empty:
            return {}
        
        # # DEBUG: Mostra as colunas disponíveis
        # st.write(f"**DEBUG - Colunas disponíveis no DataFrame salvo:** {list(df_salvo.columns)}")
        
        # # Verifica se pelo menos a coluna Quantidade existe
        # if 'Quantidade' not in df_salvo.columns:
        #     st.write(f"**DEBUG - Coluna 'Quantidade' não encontrada**")
        #     return {}
        
        # Filtra pelos dados da competência e unidade específica
        df_filtrado = df_salvo.copy()
        
        if 'Competência' in df_salvo.columns:
            df_filtrado = df_filtrado[df_filtrado['Competência'] == competencia]
        
        if 'Unidade' in df_salvo.columns:
            df_filtrado = df_filtrado[df_filtrado['Unidade'] == unidade_selecionada]
        elif 'UNIDADE PLANILHA' in df_salvo.columns:
            df_filtrado = df_filtrado[df_filtrado['UNIDADE PLANILHA'] == unidade_selecionada]
        
        # Verifica se ainda tem dados após o filtro
        if df_filtrado.empty:
            st.write("**DEBUG - DataFrame vazio após filtros**")
            return {}
        
        # Converte o DataFrame em um dicionário para facilitar o acesso
        dados_salvos = {}
        
        for _, row in df_filtrado.iterrows():
            # Como 'Código CC' não é salvo no Excel, vamos usar o nome do Centro de Custo
            # ou tentar encontrar um identificador alternativo
            
            # Tenta diferentes identificadores
            identificador = None
            
            # Primeiro tenta o nome do centro de custo
            for col_name in ['Centro de Custo', 'DESCRIÇÃO DE CENTRO DE CUSTO', 'Nome']:
                if col_name in row.index and not pd.isna(row[col_name]):
                    identificador = str(row[col_name])
                    break
            
            # Se não encontrou, tenta usar o índice da linha como identificador
            if identificador is None:
                identificador = str(row.name)  # Usa o índice da linha
            
            # Pega a quantidade
            quantidade = row.get('Quantidade', 0)
            
            # Trata diferentes tipos de dados
            if pd.isna(quantidade) or quantidade == '':
                quantidade = 0
            elif isinstance(quantidade, str):
                try:
                    quantidade = int(float(quantidade.strip())) if quantidade.strip() else 0
                except (ValueError, TypeError):
                    quantidade = 0
            elif isinstance(quantidade, (int, float)):
                quantidade = int(quantidade)
            else:
                quantidade = 0
            
            dados_salvos[identificador] = {
                'quantidade': quantidade,
                'criticidade': row.get('Criticidade_Selecionada', row.get('Criticidade', 'Selecione...')),
                'pontos_o2': row.get('Pontos_O2', 0),
                'tx_ocupacao': row.get('Tx_Ocupacao', 0),
                'local_simult': row.get('Local_Simult', 'Selecione um local...'),
                'gas_simult': row.get('Gas_Simult', 'Selecione um gás...'),
                'local_litros': row.get('Local_Litros', 'Selecione um local...'),
                'gas_litros': row.get('Gas_Litros', 'Selecione um gás...'),
                'horas_dia': row.get('Horas_Dia', 0),
                'dias_mes': row.get('Dias_Mes', 0)
            }
        
        # st.write(f"**DEBUG - Dados carregados:** {len(dados_salvos)} registros")
        return dados_salvos
        
    except Exception as e:
        # Debug em caso de erro
        st.write(f"**DEBUG - Erro em carregar_dados_salvos:** {str(e)}")
        st.write(f"**Tipo de erro:** {type(e)}")
        
        # Mostra mais informações para debug
        if 'formularios_data' in st.session_state and nome_formulario in st.session_state['formularios_data']:
            df_debug = st.session_state['formularios_data'][nome_formulario]
            st.write(f"**DEBUG - Formato do DataFrame:** {type(df_debug)}")
            if hasattr(df_debug, 'columns'):
                st.write(f"**DEBUG - Colunas:** {list(df_debug.columns)}")
            if hasattr(df_debug, 'shape'):
                st.write(f"**DEBUG - Shape:** {df_debug.shape}")
        
        return {}
    

    