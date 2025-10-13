import streamlit as st
import pandas as pd
import datetime
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário de Produtos Lactários
    """
    # Definir as ponderações dos produtos lactários
    PONDERACOES_LACTARIOS = [
        "Leite + Achocol",
        "Pregomin", 
        "Leite integral",
        "Nan supreme 2",
        "Leite + Aveia",
        "Leite + Mucilon",
        "Nan supreme 1",
        "Pré-nan",
        "Neocate LCP",
        "Nan A.R."
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
    with st.expander("🥛 Instruções - Produtos Lactários", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe a quantidade de produtos lactários consumidos**, em **mililitros (mL)**, associando cada registro ao centro de custo correspondente.
        2. **Objetivo**: Permitir o **rateio proporcional dos custos de nutrição/lactário** entre os setores que utilizam produtos lactários.
        3. **Unidade de medida**: Mililitros (mL).
        
        **Instruções específicas:**
        - Registre apenas os volumes efetivamente consumidos no período de referência.
        - Sempre associe ao **centro de custo do setor que utilizou** o produto.
        - Se não houver consumo no período, deixe em branco ou registre **0**.
        
        **Exemplo de preenchimento:**
        - Dia 10/08/2025:
            - Clínica Médica → 600 mL
            - UTI → 750 mL
        - Total do dia:
            - Clínica Médica: 600 mL
            - UTI: 750 mL
        
        Conclusão do exemplo:
        Os números registrados serão utilizados para calcular o **rateio proporcional dos custos do lactário** entre os centros de custo.
        
        ⚠️ **Importante**: Registre somente os consumos efetivos (em mL), sem duplicações, e associe corretamente ao centro de custo de utilização.
        """)


    # Obtém a unidade selecionada do session_state
    unidade_selecionada = st.session_state.get('unidade_selecionada', '')

    # Nome do formulário no Excel (ajuste conforme necessário)
    nome_formulario = "Produtos Lactário (ml) x Peso"

    try:
        # Carrega a base de centros de custo
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        
        # Verifica se a unidade foi selecionada
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
            ])

        
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
        
    

        # Carrega dados salvos
        dados_salvos = carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario)

        # Gerencia session_state para os campos
        form_key = f"form_data_{nome_formulario}_{competencia}_{unidade_selecionada}"
        if form_key not in st.session_state:
            st.session_state[form_key] = {}

        # Carrega valores salvos no session_state
        if dados_salvos:
            if 'formularios_data' in st.session_state and nome_formulario in st.session_state['formularios_data']:
                df_salvo = st.session_state['formularios_data'][nome_formulario]
                if df_salvo is not None and not df_salvo.empty:
                    df_filtrado = df_salvo[df_salvo.get('Competência', '') == competencia]
                    
                    for _, row in df_filtrado.iterrows():
                        produto = row.get('Ponderação', '')
                        centro_custo = row.get('Centro de Custo', '')
                        quantidade = row.get('Quantidade', 0)
                        
                        centro_encontrado = centros_aplicaveis[
                            centros_aplicaveis['DESCRIÇÃO DE CENTRO DE CUSTO'] == centro_custo
                        ]
                        
                        if not centro_encontrado.empty:
                            codigo_cc = centro_encontrado.iloc[0]['CÓD CC']
                            key = f"{produto}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                            st.session_state[form_key][key] = str(quantidade) if quantidade != 0 else "0"

        # Lista para armazenar todas as respostas
        dados_formulario = []
        
        st.markdown("---")
        st.markdown("### 🥛 Preenchimento dos Produtos Lactários")
        
        # Para cada centro de custo aplicável
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']
            
            st.markdown(f"#### **{centro_custo}** (Código: {codigo_cc})")
            
            # Organiza os produtos em colunas (máximo 3 por linha)
            produtos_chunks = [PONDERACOES_LACTARIOS[i:i+3] for i in range(0, len(PONDERACOES_LACTARIOS), 3)]
            
            for chunk in produtos_chunks:
                cols = st.columns(len(chunk))
                
                for col_idx, produto in enumerate(chunk):
                    with cols[col_idx]:
                        # Cria uma chave única para cada input
                        key = f"{produto}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        
                       # valor_salvo = st.session_state[form_key].get(key, "0")

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

                        # valor = st.text_input(
                        #     produto.replace(" ", "\n", 1),  # Quebra linha no primeiro espaço
                        #     value=valor_salvo,  # Mudança principal
                        #     key=key,
                        #     help=f"Quantidade de {produto.lower()}"
                        # )

                        # st.session_state[form_key][key] = valor
                        
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
                st.metric("Produtos Utilizados", produtos_utilizados)
            with col4:
                st.metric("Total de Produtos", f"{total_produtos:,.0f}")
            
            # Resumo por produto
            st.markdown("**🥛 Resumo por Produto:**")
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