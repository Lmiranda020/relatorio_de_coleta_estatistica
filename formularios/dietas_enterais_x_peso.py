import streamlit as st
import pandas as pd
import datetime
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário de Produtos Lactários
    """
    # Definir as ponderações dos produtos lactários
    PONDERACOES_DIETAS = [
        "Sem Sacarose",
        "Diabéticas", 
        "Cicatrização",
        "Semi Elementar",
        "Suplemento",
        "Infantil Elementar",
        "Hiper Hiper",
        "Infatrini",
        "Renal",
        "Infantil"
    ]
    
    def processar_entrada_numero(entrada):
        """
        Processa a entrada do usuário e retorna um número válido
        """
        if not entrada or not entrada.strip():
            return 0
        
        entrada = entrada.strip()
        try:
            entrada = entrada.replace(',', '.')
            numero = float(entrada)
            return int(numero) if numero.is_integer() else round(numero, 2)
        except (ValueError, TypeError):
            st.warning(f"⚠️ Número inválido informado: '{entrada}'. Use apenas números.")
            return 0
    
    # Caixa de instruções
    with st.expander("🥤 Instruções - Dietas Enterais x Peso", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe o número de dietas enterais servidas**, associando cada registro ao centro de custo correspondente.  
        2. **Objetivo**: Permitir o **rateio proporcional dos custos nutricionais com dietas enterais** entre os setores que utilizaram esse recurso.  
        3. **Unidade de medida**: Quantidade de dietas enterais (cada dieta = 1 ocorrência).  
        
        ---
        ### 🔹 Instruções específicas
        
        - Registre apenas as dietas **efetivamente servidas** no período de referência.  
        - Sempre associe ao **centro de custo do setor/paciente que recebeu a dieta**.  
        - Se não houver dietas no período, deixe em branco ou registre **0**.  
        - O sistema criará automaticamente uma linha de ponderação para cada registro informado.  
        
        ---
        ### 🔹 Exemplo de preenchimento
        
        Para o mês de **Agosto/2025**:  
        - Clínica Médica → 180 dietas enterais  
        - UTI Adulto → 350 dietas enterais  
        
        **Total do período:**  
        - Clínica Médica: 180 dietas  
        - UTI Adulto: 350 dietas  
        
        ---
        ### 🔹 Conclusão do exemplo
        
        Os números registrados serão utilizados para calcular o **rateio proporcional dos custos com dietas enterais** entre os centros de custo.  
        
        ⚠️ **Importante**: Registre apenas dietas efetivamente servidas, sem duplicações, e associe corretamente ao centro de custo de utilização.  
        """)

    try:
        # Carrega a base de centros de custo
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        
        # Obtém a unidade selecionada do session_state
        unidade_selecionada = st.session_state.get('unidade_selecionada', '')
        
        # Verifica se a unidade foi selecionada
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
            ])
        
        # Nome do formulário no Excel (ajuste conforme necessário)
        nome_formulario = "Dietas Enterais X Peso"

        # Carrega dados salvos
        dados_salvos = carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario)

        # Gerenciamento mínimo do session_state
        form_key = f"form_data_{nome_formulario}_{competencia}_{unidade_selecionada}"
        if form_key not in st.session_state:
            st.session_state[form_key] = {}
            if dados_salvos:
                # Agora os dados_salvos usam o nome do centro de custo como chave
                for centro_custo_nome, dados in dados_salvos.items():
                    # Encontra o código CC correspondente ao nome do centro de custo
                    centro_encontrado = centros_aplicaveis[
                        centros_aplicaveis['DESCRIÇÃO DE CENTRO DE CUSTO'] == centro_custo_nome
                    ]
                    
                    if not centro_encontrado.empty:
                        codigo_cc = centro_encontrado.iloc[0]['CÓD CC']
                        field_key = f"{nome_formulario}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        quantidade = dados.get('quantidade', 0)
                        
                        if isinstance(quantidade, (int, float)) and quantidade > 0:
                            st.session_state[form_key][field_key] = str(int(quantidade))
                        else:
                            st.session_state[form_key][field_key] = "0"
        
        # Verifica se a coluna do formulário existe
        if nome_formulario not in df_centros_custo.columns:
            st.error(f"❌ Coluna '{nome_formulario}' não encontrada no arquivo Excel.")
            st.write("**Colunas disponíveis:**")
            st.write(list(df_centros_custo.columns))
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
            ])
        
        # Filtra pela unidade e pelo formulário
        centros_aplicaveis = df_centros_custo[
            (df_centros_custo['UNIDADE PLANILHA'] == unidade_selecionada) & 
            (df_centros_custo[nome_formulario] == True)
        ]
        
        # Verifica se há centros de custo aplicáveis
        if centros_aplicaveis.empty:
            st.warning(f"⚠️ Nenhum centro de custo encontrado para a unidade '{unidade_selecionada}' neste formulário.")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
            ])
        
        # Mostra informações do formulário
        st.write(f"**Formulário**: {nome_formulario}")
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")
        
        # Lista para armazenar todas as respostas
        dados_formulario = []
        
        st.markdown("---")
        st.markdown("### 🥛 Preenchimento das Dietas Enterais")
        
        # Para cada centro de custo aplicável
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']
            
            st.markdown(f"#### **{centro_custo}** (Código: {codigo_cc})")
            
            # Organiza os produtos em colunas (máximo 3 por linha)
            produtos_chunks = [PONDERACOES_DIETAS[i:i+3] for i in range(0, len(PONDERACOES_DIETAS), 3)]
            
            for chunk in produtos_chunks:
                cols = st.columns(len(chunk))
                
                for col_idx, produto in enumerate(chunk):
                    with cols[col_idx]:
                        # Cria uma chave única para cada input
                        key = f"{produto}_{codigo_cc}_{competencia}_{unidade_selecionada}"

                        field_key = f"{produto}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        valor_default = st.session_state[form_key].get(field_key, "0")

                        entrada = st.text_input(
                            produto.replace(" ", "\n", 1), 
                            # f"**{centro_custo}** (Código: {codigo_cc})",
                            value=valor_default,
                            # ... resto igual
                            key=field_key
                        )

                        # Atualiza session_state
                        st.session_state[form_key][field_key] = entrada
                        
                        # Processa o valor inserido
                        quantidade = processar_entrada_numero(entrada)
                        
                        # Se a quantidade for maior que 0, adiciona aos dados
                        if quantidade > 0:
                            dados_formulario.append({
                                'Competência': competencia,
                                'Ponderação': produto,
                                'Centro de Custo': centro_custo,
                                # 'Código CC': codigo_cc,
                                'Quantidade': quantidade
                            })
            
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)  # Espaço entre centros de custo
        
        # Converte para DataFrame
        df_resultado = pd.DataFrame(dados_formulario)
        
        # Mostra um resumo dos dados inseridos
        if not df_resultado.empty:
            st.write("---")
            st.write("**📊 Resumo dos dados inseridos:**")
            
            # Estatísticas gerais
            total_linhas = len(df_resultado)
            centros_preenchidos = df_resultado['Centro de Custo'].nunique()
            produtos_utilizados = df_resultado['Ponderação'].nunique()
            total_produtos = df_resultado['Quantidade'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Linhas", total_linhas)
            with col2:
                st.metric("Centros Preenchidos", centros_preenchidos)
            with col3:
                st.metric("Dietas Enterais", produtos_utilizados)
            with col4:
                st.metric("Total de Produtos", f"{total_produtos:,.0f}")
            
            # Resumo por produto
            st.markdown("**🥛 Resumo por Dietas:**")
            resumo_produtos = df_resultado.groupby('Ponderação')['Quantidade'].agg(['sum', 'count']).reset_index()
            resumo_produtos = resumo_produtos.sort_values('sum', ascending=False)
            
            for _, row_produto in resumo_produtos.iterrows():
                st.write(f"• **{row_produto['Ponderação']}**: {row_produto['count']} registros | {row_produto['sum']:,.0f} unidades")
            
            # Resumo por centro de custo
            if len(df_resultado['Centro de Custo'].unique()) > 1:
                st.markdown("**🏥 Resumo por Centro de Custo:**")
                resumo_cc = df_resultado.groupby('Centro de Custo')['Quantidade'].agg(['sum', 'count']).reset_index()
                resumo_cc = resumo_cc.sort_values('sum', ascending=False)
                
                for _, row_cc in resumo_cc.iterrows():
                    st.write(f"• **{row_cc['Centro de Custo']}**: {row_cc['count']} registros | {row_cc['sum']:,.0f} produtos")
                    
        else:
            st.info("ℹ️ Nenhum dado foi inserido ainda.")
        
        return df_resultado if not df_resultado.empty else pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
        ])
        
    except FileNotFoundError:
        st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
        ])
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o formulário: {str(e)}")
        st.write(f"**Detalhes do erro**: {type(e).__name__}")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
        ])