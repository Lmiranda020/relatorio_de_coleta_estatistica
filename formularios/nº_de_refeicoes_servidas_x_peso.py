import streamlit as st
import pandas as pd
import datetime
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário Nº de Refeições Servidas x Peso (Dietas) com condições
    """
    # Definir as ponderações organizadas por categoria
    PONDERACOES = {
        "Pacientes e Acompanhantes": [
            "Desjejum Paciente",
            "Almoço Paciente", 
            "Lanche da Tarde Paciente",
            "Jantar Pacientes",
            "Ceia Pacientes"
        ],
        "Colaboradores": [
            "Desjejum Col",
            "Almoço Col",
            "Jantar Col", 
            "Ceia Col"
        ],
        "Diversos": [
            "Garrafa de Água (litro)",
            "Coffee Break 1",
            "Garrafa de Café (litro)",
            "Lanche da Tarde",
            "Coffee Break 2", 
            "Garrafa de Chá"
        ]
    }
    
    # Obtém a unidade selecionada do session_state
    unidade_selecionada = st.session_state.get('unidade_selecionada', '')
   
   # Nome do formulário no Excel
    nome_formulario = "Nº de Refeições Servidas x Peso"

    
    def get_categorias_aplicaveis(condicao_refeicao):
        """
        Retorna as categorias aplicáveis baseado na condição de refeição
        """
        if pd.isna(condicao_refeicao) or condicao_refeicao.upper() == "TODOS":
            # Se for TODOS ou vazio, retorna todas as categorias
            return list(PONDERACOES.keys())
        else:
            # Se especificar uma categoria, remove ela da lista (condição negativa)
            todas_categorias = list(PONDERACOES.keys())
            condicao_upper = condicao_refeicao.upper()
            
            # Mapear possíveis nomes para as categorias
            mapeamento_condicoes = {
                "PACIENTES E ACOMPANHANTES": "Pacientes e Acompanhantes",
                "PACIENTE E ACOMPANHANTE": "Pacientes e Acompanhantes",
                "PACIENTES": "Pacientes e Acompanhantes",
                "COLABORADORES": "Colaboradores",
                "COLABORADOR": "Colaboradores",
                "DIVERSOS": "Diversos"
            }
            
            categoria_excluir = mapeamento_condicoes.get(condicao_upper)
            
            if categoria_excluir and categoria_excluir in todas_categorias:
                todas_categorias.remove(categoria_excluir)
                return todas_categorias
            else:
                # Se não reconhecer a condição, retorna todas
                st.warning(f"⚠️ Condição de refeição não reconhecida: '{condicao_refeicao}'. Aplicando todas as categorias.")
                return todas_categorias
    
    # Caixa de instruções
    with st.expander("📋 Instruções - Nº de Refeições Servidas x Peso", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe a quantidade de refeições servidas**, em cada centro de custo, separadas por categoria e tipo de refeição.  
        2. **Objetivo**: Garantir o **rateio proporcional dos custos de alimentação** entre os centros de custos utilizados refeição.  
        3. **Unidade de medida**: Número de refeições servidas no mês.  
        
        ---
        ### 🔹 Categorias de Refeições
        
        **👥 Pacientes e Acompanhantes**  
        - Desjejum, Almoço, Lanche da Tarde, Jantar, Ceia  
        
        **👨‍💼 Colaboradores**  
        - Desjejum, Almoço, Jantar, Ceia  
        
        **☕ Diversos**  
        - Garrafas de água, café e chá  
        - Coffee breaks e lanches extras  
        
        ---
        ### 🔹 Instruções específicas
        
        - Informe sempre o **número de refeições efetivamente servidas no período de referência**.  
        - Use **0 (zero)** nas categorias não utilizadas pelo centro de custo.  
        - O sistema criará automaticamente uma linha de ponderação para cada categoria preenchida.  

        ---
        ### 🔹 Exemplo de preenchimento
        
        Supondo os seguintes registros no mês para o centro de custo **"CLÍNICA MÉDICA"**:  
        - Colaboradores: 300 refeições  
        - Diversos: 120 consumos  
        
        **Total**: 420 refeições registradas para esse centro de custo.  
        
        ---
        ### 🔹 Conclusão do exemplo
        
        Os números registrados serão utilizados para calcular o **rateio proporcional dos custos de nutrição e alimentação** entre os centros de custo.  
        ⚠️ **Importante**: Registre apenas as refeições efetivamente servidas e associe corretamente cada lançamento ao centro de custo de referência.  
        """)

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
    
    try:
        # Carrega a base de centros de custo
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        
        # Verifica se a unidade foi selecionada
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        
        # Verifica se as colunas necessárias existem
        colunas_necessarias = [nome_formulario, 'CONDIÇÃO REFEIÇÃO']
        colunas_faltantes = [col for col in colunas_necessarias if col not in df_centros_custo.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Colunas não encontradas no arquivo Excel: {', '.join(colunas_faltantes)}")
            st.write("**Colunas disponíveis:**")
            st.write(list(df_centros_custo.columns))
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
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
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])
        
        # Mostra informações do formulário
        st.write(f"**Formulário**: {nome_formulario}")
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")
        
        # Lista para armazenar todas as respostas
        dados_formulario = []
        
        # Carrega dados salvos
        dados_salvos = carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario)

        # Gerencia session_state para os campos
        form_key = f"form_data_{nome_formulario}_{competencia}_{unidade_selecionada}"
        if form_key not in st.session_state:
            st.session_state[form_key] = {}

        # Carrega valores salvos no session_state
        if dados_salvos:
            # Para refeições, os dados salvos vêm como registros individuais
            # Precisamos reconstruir as chaves dos inputs
            
            # Se dados_salvos for um DataFrame (convertido pelo sistema de salvamento)
            # vamos tentar recuperar os dados da session original
            if 'formularios_data' in st.session_state and nome_formulario in st.session_state['formularios_data']:
                df_salvo = st.session_state['formularios_data'][nome_formulario]
                if df_salvo is not None and not df_salvo.empty:
                    # Filtra pelos dados da competência e unidade
                    df_filtrado = df_salvo[
                        (df_salvo.get('Competência', '') == competencia)
                    ]
                    
                    # Para cada registro salvo, reconstroi a chave do input
                    for _, row in df_filtrado.iterrows():
                        ponderacao = row.get('Ponderação', '')
                        centro_custo = row.get('Centro de Custo', '')
                        quantidade = row.get('Quantidade', 0)
                        
                        # Busca o código do centro de custo
                        centro_encontrado = centros_aplicaveis[
                            centros_aplicaveis['DESCRIÇÃO DE CENTRO DE CUSTO'] == centro_custo
                        ]
                        
                        if not centro_encontrado.empty:
                            codigo_cc = centro_encontrado.iloc[0]['CÓD CC']
                            key = f"{ponderacao}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                            st.session_state[form_key][key] = str(quantidade) if quantidade != 0 else "0"

        st.markdown("---")
        st.markdown("### 🍽️ Preenchimento das Refeições")
        
        # Para cada centro de custo aplicável
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']
            condicao_refeicao = row.get('CONDIÇÃO REFEIÇÃO', 'TODOS')
            
            # Determina quais categorias se aplicam a este centro de custo
            categorias_aplicaveis = get_categorias_aplicaveis(condicao_refeicao)
            
            st.markdown(f"#### **{centro_custo}** (Código: {codigo_cc})")
            
            # Mostra a condição aplicada
            if pd.isna(condicao_refeicao) or str(condicao_refeicao).upper() == "TODOS":
                st.markdown(f"🔹 **Condição**: TODOS - Aplica todas as categorias")
            else:
                categorias_excluidas = [cat for cat in PONDERACOES.keys() if cat not in categorias_aplicaveis]
                st.markdown(f"🔹 **Condição**: {condicao_refeicao} - Exclui: {', '.join(categorias_excluidas)}")
            
            # Para cada categoria aplicável
            for categoria in categorias_aplicaveis:
                ponderacoes = PONDERACOES[categoria]
                
                if categoria == "Pacientes e Acompanhantes":
                    emoji = "👥"
                elif categoria == "Colaboradores":
                    emoji = "👨‍💼"
                else:
                    emoji = "☕"
                
                st.markdown(f"##### {emoji} {categoria}")
                
                # Organiza as ponderações em colunas (máximo 3 por linha)
                ponderacoes_chunks = [ponderacoes[i:i+3] for i in range(0, len(ponderacoes), 3)]
                
                for chunk in ponderacoes_chunks:
                    cols = st.columns(len(chunk))
                    
                    for col_idx, ponderacao in enumerate(chunk):
                        with cols[col_idx]:
                            # Cria uma chave única para cada input
                            key = f"{ponderacao}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                            
                            # Recupera valor salvo se existir
                            valor_salvo = st.session_state[form_key].get(key, "0")
                            valor = st.text_input(
                                ponderacao.replace(" ", "\n", 1),  # Quebra linha no primeiro espaço
                                value=valor_salvo,
                                key=key,
                                help=f"Quantidade de {ponderacao.lower()}"
                            )
                            # Atualiza session_state
                            st.session_state[form_key][key] = valor
                            
                            # Processa o valor inserido
                            quantidade = processar_entrada_numero(valor)
                            
                            # Se a quantidade for maior que 0, adiciona aos dados
                            if quantidade > 0:
                                dados_formulario.append({
                                    'Competência': competencia,
                                    'Ponderação': ponderacao,
                                    'Centro de Custo': centro_custo,
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
            ponderacoes_utilizadas = df_resultado['Ponderação'].nunique()
            total_refeicoes = df_resultado['Quantidade'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Linhas", total_linhas)
            with col2:
                st.metric("Centros Preenchidos", centros_preenchidos)
            with col3:
                st.metric("Ponderações Utilizadas", ponderacoes_utilizadas)
            with col4:
                st.metric("Total de Refeições", f"{total_refeicoes:,.0f}")
            
            # Resumo por categoria
            st.markdown("**📋 Resumo por Categoria:**")
            for categoria, ponderacoes in PONDERACOES.items():
                dados_categoria = df_resultado[df_resultado['Ponderação'].isin(ponderacoes)]
                if not dados_categoria.empty:
                    total_categoria = dados_categoria['Quantidade'].sum()
                    linhas_categoria = len(dados_categoria)
                    st.write(f"• **{categoria}**: {linhas_categoria} registros | {total_categoria:,.0f} refeições")
            
            # Resumo por centro de custo
            if len(df_resultado['Centro de Custo'].unique()) > 1:
                st.markdown("**🏥 Resumo por Centro de Custo:**")
                resumo_cc = df_resultado.groupby('Centro de Custo')['Quantidade'].agg(['sum', 'count']).reset_index()
                for _, row_cc in resumo_cc.iterrows():
                    st.write(f"• **{row_cc['Centro de Custo']}**: {row_cc['count']} registros | {row_cc['sum']:,.0f} refeições")
                    
        else:
            st.info("ℹ️ Nenhum dado foi inserido ainda.")
        
        return df_resultado if not df_resultado.empty else pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
        ])
        
    except FileNotFoundError:
        st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
        ])
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o formulário: {str(e)}")
        st.write(f"**Detalhes do erro**: {type(e).__name__}")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
        ])