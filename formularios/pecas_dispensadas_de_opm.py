import streamlit as st
import pandas as pd
import datetime
import re
from datetime import timedelta
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário 
    """
    # Caixa de instruções
    with st.expander("📋 Instruções - Peças Dispensadas de OPM (Órteses, Próteses e Materiais)", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe o número total de peças de OPM dispensadas** para cada centro de custo no período de referência.
        2. **Objetivo**: Auxiliar no **rateio proporcional dos custos operacionais** do setor de OPM, de acordo com o volume de peças efetivamente atendidas.
        3. **Unidade de medida**: Quantidade de peças dispensadas.
        
        **Instruções específicas:**
        - Cada peça conta individualmente, mesmo que mais de uma peça seja entregue na mesma requisição.
        - Inclua apenas as peças efetivamente entregues e registradas.
        - Associe o valor ao centro de custo solicitante.
        - Deixe em branco ou zero se não houver dispensas para o centro de custo no período.
        
        **Exemplo de cálculo:**
        - Dia 02/06/2022: Entregues 2 próteses de quadril e 1 placa ortopédica → **3 peças**.
        - Dia 05/06/2022: Entregues 1 órtese de joelho → **1 peça**.
        - Total do mês: 4 peças dispensadas.
        
        Conclusão do exemplo:
        O número de peças será usado para **ratear os custos operacionais do setor de OPM** proporcionalmente entre os centros de custo atendidos.
        
        ⚠️ **Importante**: Considere apenas peças efetivamente utilizadas/entregues, não inclua peças solicitadas mas não retiradas.
        """)

    
    def processar_entrada_numero(entrada):
        """
        Processa a entrada do usuário e retorna um número inteiro válido
        """
        if not entrada or not entrada.strip():
            return 0
        
        entrada = entrada.strip()

        try:
            # Verifica se é um número válido (inteiro ou decimal)
            if re.match(r'^\d+\.?\d*$', entrada):
                numero = float(entrada)
                return int(numero)  # Converte para inteiro
            else:
                raise ValueError("Formato de número inválido")

        except (ValueError, TypeError) as e:
            st.warning(f"⚠️ Número inválido informado: '{entrada}'. Use apenas números inteiros.")
            return 0

    
    try:
        # Carrega a base de centros de custo
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        
        # Obtém a unidade selecionada do session_state (passada pelo app principal)
        unidade_selecionada = st.session_state.get('unidade_selecionada', '')
        
        # Verifica se a unidade foi selecionada
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 
                'Código CC', 'Quantidade'
            ])
        
        # Nome do formulário (deve corresponder ao nome da coluna no Excel)
        nome_formulario = "Peças Dispensadas de OPM"
        
        # Verifica se a coluna existe
        if nome_formulario not in df_centros_custo.columns:
            st.error(f"❌ Coluna '{nome_formulario}' não encontrada no arquivo Excel!")
            st.write("**Colunas disponíveis:**")
            st.write(list(df_centros_custo.columns))
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 
                'Código CC', 'Quantidade'
            ])
        
        # Filtra pela unidade e pelo formulário (coluna TRUE)
        centros_aplicaveis = df_centros_custo[
            (df_centros_custo['UNIDADE PLANILHA'] == unidade_selecionada) & 
            (df_centros_custo[nome_formulario] == True)
        ]
        
        # Verifica se há centros de custo aplicáveis
        if centros_aplicaveis.empty:
            st.warning(f"⚠️ Nenhum centro de custo encontrado para a unidade '{unidade_selecionada}' neste formulário.")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 
                'Código CC', 'Quantidade'
            ])
        
        # Ponderação fixa para este formulário
        ponderacao = "Peças Dispensadas de OPM"
        
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
                            
        # Cria o DataFrame para armazenar as respostas
        dados_formulario = []
        
        # Mostra informações do formulário
        st.write(f"**Ponderação**: {ponderacao}")
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")
        
        # Para cada centro de custo aplicável, cria um campo de input
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']
            
            field_key = f"{nome_formulario}_{codigo_cc}_{competencia}_{unidade_selecionada}"
            valor_default = st.session_state[form_key].get(field_key, "0")

            entrada = st.text_input(
                f"**{centro_custo}** (Código: {codigo_cc})",
                value=valor_default,
                # ... resto igual
                key=field_key
            )

            # Atualiza session_state
            st.session_state[form_key][field_key] = entrada
            
            # Processa a entrada
            quantidade = processar_entrada_numero(entrada)
            
            # Adiciona ao formulário
            dados_formulario.append({
                'Competência': competencia,
                'Ponderação': ponderacao,
                'Centro de Custo': centro_custo,
                'Código CC': codigo_cc,
                'Quantidade': quantidade
            })
        
        # Converte para DataFrame
        df_resultado = pd.DataFrame(dados_formulario)
        
        # Verifica se o DataFrame tem dados
        if df_resultado.empty:
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 
                'Código CC', 'Quantidade'
            ])
        
        # Ajusta as colunas para o formato final
        df_resultado = df_resultado[["Competência", "Ponderação", "Centro de Custo", "Quantidade"]]
        
        # Mostra um resumo dos dados inseridos
        if not df_resultado.empty:
            st.write("---")
            st.write("**📊 Resumo dos dados inseridos:**")
            registros_preenchidos = len(df_resultado[df_resultado['Quantidade'] != 0])
            total_quantidade = df_resultado['Quantidade'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Centros Preenchidos", registros_preenchidos)
            with col2:
                st.metric("Total de Centros", len(df_resultado))
            with col3:
                st.metric("Total de Peças Dispensadas de OPM", total_quantidade)
        
        return df_resultado
        
    except FileNotFoundError:
        st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
        ])
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o formulário: {str(e)}")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Código CC', 'Quantidade'
        ])