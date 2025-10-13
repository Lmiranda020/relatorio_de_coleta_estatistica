import streamlit as st
import pandas as pd
import datetime
import re
from datetime import timedelta
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário RC_Consultórios Compartilhado
    """
    # Caixa de instruções
    with st.expander("📋 Instruções - RC_Consultórios Compartilhado", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Ponderação**: Horas Consultório Compartilhado
        2. **Objetivo**: Registrar as horas de uso dos consultórios compartilhados
        3. **Unidade de medida**: Horas
        
        **Instruções específicas:**
        - Informe a quantidade de horas para cada centro de custo listado
        - Considere apenas os consultórios que são compartilhados entre diferentes serviços
        - Use valores inteiros ou decimais (ex: 8.5 horas)
        - Deixe em branco ou zero se não houver utilização

        **Exemplos:** Uma sala é compartilhada entre vários serviços, por exemplo, psicologia, nutrição e enfermagem. As horas de uso devem ser registradas como:
        - AMBULATORIO NAO MEDICO (NUTRICAO): 40 horas/mês
        - AMBULATORIO NAO MEDICO (PSICOLOGIA): 30 horas/mês
        - AMBULATORIO NAO MEDICO (ENFERMAGEM): 5 horas /mês
        - Totalizando 75 horas/mês
                    
        Conclusão do exemplo:
        No mês analisado, a sala compartilhada foi utilizada por diferentes serviços: 40 horas pela Nutrição, 30 horas pela Psicologia e 5 horas pela Enfermagem. Isso totaliza 
                    75 horas de uso no mês. Com base nesses dados, será possível calcular o rateio proporcional dos custos da sala para cada centro de custo envolvido. 
                    Ou seja, quanto maior o tempo de utilização, maior será a participação no custo total do espaço.
        
        ⚠️ **Importante**: Preencha todos os campos obrigatórios antes de salvar.
        """)
    
    def processar_entrada_tempo(entrada):
        if not entrada or not entrada.strip():
            return "0:00:00"
        
        entrada = entrada.strip()
        entrada = entrada.replace(',', '.')
        
        try:
            # Horas decimais, ex: 75 ou 75.5
            if re.match(r'^\d+\.?\d*$', entrada):
                horas_decimal = float(entrada)
                horas = int(horas_decimal)
                minutos = int((horas_decimal - horas) * 60)
                return f"{horas}:{minutos:02d}:00"
            
            # HH:MM:SS
            elif entrada.count(':') == 2:
                partes = entrada.split(':')
                if len(partes) != 3:
                    raise ValueError("Formato inválido HH:MM:SS")
                horas = int(partes[0])
                minutos = int(partes[1])
                segundos = int(partes[2])
                return f"{horas}:{minutos:02d}:{segundos:02d}"

            # HH:MM
            elif entrada.count(':') == 1:
                partes = entrada.split(':')
                if len(partes) != 2:
                    raise ValueError("Formato inválido HH:MM")
                horas = int(partes[0])
                minutos = int(partes[1])
                return f"{horas}:{minutos:02d}:00"

            else:
                raise ValueError("Formato de tempo inválido")

        except (ValueError, IndexError) as e:
            st.warning(f"⚠️ Tempo inválido informado: '{entrada}'. Use HH:MM ou HH:MM:SS.")
            return "0:00:00"

    
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
        nome_formulario = "Consultorio Compartilhado"
        
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
        ponderacao = "Horas Consultório Compartilhado"

        
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
                        quantidade = dados.get('quantidade', "0:00:00")
                        
                        # trabalha com strings de tempo
                        if quantidade and quantidade != "0:00:00":
                            st.session_state[form_key][field_key] = str(quantidade)
                        else:
                            st.session_state[form_key][field_key] = "0:00:00"
        
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
            valor_default = st.session_state[form_key].get(field_key, "0:00:00")

            entrada = st.text_input(
                f"**{centro_custo}** (Código: {codigo_cc})",
                value=valor_default,
                # ... resto igual
                key=field_key
            )
            
            st.session_state[form_key][field_key] = entrada
            
            # Processa a entrada
            tempo_formatado = processar_entrada_tempo(entrada)
            
            # Adiciona ao formulário
            dados_formulario.append({
                'Competência': competencia,
                'Ponderação': ponderacao,
                'Centro de Custo': centro_custo,
                'Código CC': codigo_cc,
                'Quantidade': tempo_formatado
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
            registros_preenchidos = len(df_resultado[df_resultado['Quantidade'] != "0:00:00"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Centros Preenchidos", registros_preenchidos)
            with col2:
                st.metric("Total de Centros", len(df_resultado))
        
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