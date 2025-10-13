import streamlit as st
import pandas as pd
import datetime
import re
from datetime import timedelta
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário RC_Classificação_de_Risco
    """
    # Caixa de instruções
    with st.expander("📋 Instruções - Nº de Solicitações (Central de Serviços Administrativos)", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe o número de solicitações realizadas à Central de Serviços Administrativos**, discriminando por centro de custo solicitante
        2. **Objetivo**: Auxiliar no **rateio proporcional dos custos operacionais da Central de Serviços Administrativos** entre os centros que demandaram atendimento
        3. **Unidade de medida**: Número de solicitações (cada solicitação = 1 atendimento realizado pelo setor)
        
        **Instruções específicas:**
        - Cada solicitação pode envolver serviços administrativos, protocolos, tramitação de documentos, contratos, entre outros
        - É essencial registrar o **centro de custo solicitante** para cada atendimento
        - Se o mesmo centro fizer múltiplas solicitações no período, registre cada solicitação separadamente
        - Deixe em branco ou zero se não houver solicitações para determinado centro de custo
        
        **Exemplo de cálculo:**
        - Dia 05/06/2022:
            - Solicitações do Pronto-Socorro → 3 atendimentos
            - Solicitações da UTI → 2 atendimentos
        - Dia 06/06/2022:
            - Solicitações da Clínica Médica → 4 atendimentos
        - Total do mês:
            - Pronto-Socorro: 3 solicitações
            - UTI: 2 solicitações
            - Clínica Médica: 4 solicitações
        
        Conclusão do exemplo:
        Os números registrados permitirão calcular o **rateio proporcional dos custos da Central de Serviços Administrativos** entre os centros de custo que demandaram atendimento.
        
        ⚠️ **Importante**: Registre apenas as solicitações efetivamente atendidas no período e associe corretamente ao centro de custo solicitante.
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
        nome_formulario = "Nº de solicitações Central de Serviços Administrativos"
        
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
        ponderacao = "Nº de solicitações Central de Serviços Administrativos"

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
                st.metric("Total de Nº de solicitações Central de Serviços Administrativos", total_quantidade)
        
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