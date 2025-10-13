import streamlit as st
import pandas as pd
import datetime
import re
from datetime import timedelta
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia):
    """
    Renderiza o formulário % de Atuação SCIH/CCIH
    """
    # Caixa de instruções
    with st.expander("📋 Instruções - % de Atuação SCIH/CCIH (Serviço de Controle de Infecção Hospitalar – SCIH/CCIH)", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe a porcentagem de atuação do SCIH/CCIH em cada centro de custo**
        2. **Objetivo**: Auxiliar na **análise e rateio dos custos do Serviço de Controle de Infecção Hospitalar** entre os centros que se beneficiaram da atuação do SCIH
        3. **Unidade de medida**: Porcentagem (%)
        
        **Instruções específicas:**
        - A porcentagem deve refletir o quanto cada centro de custo se beneficiou das ações do SCIH/CCIH
        - Associe cada valor ao centro de custo correspondente
        - Deixe em branco ou zero se o centro de custo não recebeu suporte do SCIH
        - **Digite apenas o número (ex: 50 para 50%, 30.5 para 30.5%)**
        
        **Exemplos:**
        - UTI Adulto: 50% de atuação → **Digite: 50**
        - Centro Cirúrgico: 30% de atuação → **Digite: 30**
        - Enfermaria Pediátrica: 20% de atuação → **Digite: 20**
        
        Conclusão do exemplo:
        No período analisado, os dados serão utilizados para calcular o **rateio proporcional dos custos do SCIH/CCIH** entre os diferentes centros de custo.
        
        ⚠️ **Importante**: Registre apenas a atuação efetiva do SCIH/CCIH no período de referência.
        """)

    def processar_entrada_numero(entrada):
        """
        Processa a entrada do usuário e retorna um número válido (porcentagem com decimais)
        Aceita tanto vírgula quanto ponto como separador decimal
        """
        if not entrada or not entrada.strip():
            return 0.0
        
        entrada = entrada.strip()

        try:
            # Substitui vírgula por ponto para padronizar
            entrada_normalizada = entrada.replace(',', '.')
            
            # Verifica se é um número válido (inteiro ou decimal)
            if re.match(r'^\d+\.?\d*$', entrada_normalizada):
                numero = float(entrada_normalizada)
                # Valida se a porcentagem está em uma faixa razoável
                if numero > 100:
                    st.warning(f"⚠️ Atenção: Valor {numero}% é maior que 100%. Verifique se está correto.")
                return numero
            else:
                raise ValueError("Formato de número inválido")

        except (ValueError, TypeError) as e:
            st.warning(f"⚠️ Porcentagem inválida informada: '{entrada}'. Use números com ou sem decimais (ex: 40, 35.5 ou 35,5 para 35.5%).")
            return 0.0

        
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
        nome_formulario = "% de Atuação SCIH/CCIH"

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
        ponderacao = "% de Atuação SCIH/CCIH"
        
        # Cria o DataFrame para armazenar as respostas
        dados_formulario = []
        
        # Mostra informações do formulário
        st.write(f"**Ponderação**: {ponderacao}")
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")
        
        # Adiciona um aviso sobre porcentagem
        st.info("💡 **Lembre-se**: Digite o número da porcentagem (ex: 40 para 40%, 35.5 ou 35,5 para 35.5%)")
        
        # Inicializa o estado de validação no session_state
        validation_key = f"validation_{nome_formulario}_{competencia}_{unidade_selecionada}"
        if validation_key not in st.session_state:
            st.session_state[validation_key] = {
                'calculado': False,
                'valido': False,
                'total': 0,
                'registros_preenchidos': 0,
                'errors': []
            }

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
        
        # Botão de Calcular
        col_calc, col_space = st.columns([1, 3])
        with col_calc:
            calcular = st.form_submit_button("🧮 Calcular")
        
        # Apenas processa e mostra o resumo se o botão foi clicado ou já foi calculado antes
        if calcular or st.session_state[validation_key].get('calculado', False):
            # Se o botão foi clicado, marca como calculado
            if calcular:
                st.session_state[validation_key]['calculado'] = True
            
            # Calcula baseado nos dados atuais
            registros_preenchidos = len(df_resultado[df_resultado['Quantidade'] != 0])
            total_quantidade = df_resultado['Quantidade'].sum()
            
            # Valida os dados
            errors = []
            for idx, row in df_resultado.iterrows():
                valor = row['Quantidade']
                if valor < 0:
                    errors.append(f"Centro '{row['Centro de Custo']}': valor negativo ({valor})")
            
            # Para formulário de resíduos, só é válido se somar EXATAMENTE 100%
            total_valido = (total_quantidade == 100.0)
            
            # Atualiza o session_state
            st.session_state[validation_key].update({
                'calculado': True,
                'valido': len(errors) == 0 and total_valido,
                'total': total_quantidade,
                'registros_preenchidos': registros_preenchidos,
                'errors': errors,
                'total_valido': total_valido
            })
            
            # Mostra o resumo
            validation_state = st.session_state[validation_key]
            st.write("---")
            st.write("**📊 Resumo dos dados inseridos:**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Centros Preenchidos", validation_state['registros_preenchidos'])
            with col2:
                st.metric("Total de Centros", len(df_resultado))
            with col3:
                st.metric("Total % Atuação SCIH/CCIH", f"{validation_state['total']}%")
            
            # Mostra erros se houver
            if validation_state['errors']:
                st.error("❌ **Erros encontrados:**")
                for error in validation_state['errors']:
                    st.write(f"• {error}")
            
            # Status da validação baseado no total
            if validation_state['total'] == 100:
                st.success("✅ **Validação aprovada!** O total soma exatamente 100%. Você pode salvar o formulário.")
            elif validation_state['total'] > 100:
                st.error(f"❌ **Total inválido**: {validation_state['total']}% é maior que 100%. Ajuste os valores para somar exatamente 100%.")
            elif validation_state['total'] < 100 and validation_state['total'] > 0:
                st.warning(f"⚠️ **Total insuficiente**: {validation_state['total']}% é menor que 100%. Complete os valores para somar exatamente 100%.")
            elif validation_state['total'] == 0:
                st.info("ℹ️ **Aguardando preenchimento**: Insira as porcentagens para cada centro de custo.")
   
        # Retorna os dados sempre (a validação será feita no app principal)
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