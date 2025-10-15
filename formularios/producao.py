import pandas as pd
import streamlit as st
import re
from api.api_producao import api_producao
from utils.carregar_dados import carregar_dados_salvos

# Chama a função para obter os dados de produção através da API
dados_api = api_producao()

# Inicializa DataFrame vazio como fallback
base_de_producao = pd.DataFrame()

# Processa os dados da API
if dados_api:
    try:
        # Extrai dados da chave 'items'
        if isinstance(dados_api, dict) and 'items' in dados_api:
            dados_para_df = dados_api['items']
        else:
            dados_para_df = dados_api
        
        # Cria o DataFrame
        base_de_producao = pd.DataFrame(dados_para_df)
        
        if not base_de_producao.empty:
            # Limpa os nomes das colunas
            base_de_producao.columns = base_de_producao.columns.str.strip()
            
            # Seleciona apenas as colunas necessárias
            colunas_necessarias = ["competenciaDescr", "unidadeDeProducaoDescr", "centroDeCustoDescr"]
            colunas_existentes = [col for col in colunas_necessarias if col in base_de_producao.columns]
            
            if colunas_existentes:
                base_de_producao = base_de_producao[colunas_existentes]
            else:
                st.error("❌ Colunas esperadas não encontradas na API!")
                base_de_producao = pd.DataFrame()
                
    except Exception as e:
        st.error(f"❌ Erro ao processar dados da API: {str(e)}")
        base_de_producao = pd.DataFrame()


def render_form(competencia):
    """
    Renderiza o formulário de Produção (nº de atendimentos por centro de custo)
    Com ponderações dinâmicas vindas da API
    """
    # Caixa de instruções
    
    with st.expander("📋 Instruções - Produção", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Informe o número de atendimentos realizados** por cada centro de custo produtivo.
        2. **Objetivo**: Auxiliar no **rateio proporcional dos custos operacionais** entre os centros de custo que produziram atendimentos.
        3. **Unidade de medida**: Número de atendimentos.
        
        **Instruções específicas:**
        - Cada atendimento corresponde a **uma unidade de registro**.
        - Associe cada atendimento ao **centro de custo correto**.
        - Deixe em branco ou zero se não houver atendimentos para determinado centro.
        - **Cada centro de custo possui sua própria ponderação** (baseada na API de produção).
        
        **Exemplo de preenchimento:**
        - PRONTO SOCORRO ADULTO → 50 atendimentos
        - TELECONSULTA → 30 atendimentos
        - AMBULATORIO MEDICO (DERMATOLOGIA) → 20 atendimentos
        
        ✅ **Conclusão do exemplo**:
        O total será utilizado para calcular o **rateio proporcional dos custos operacionais** entre os centros de custo produtivos.
        
        ⚠️ **Importante**: Registre apenas os atendimentos efetivamente realizados no período de referência.
        """)

    def processar_entrada_numero(entrada):
        """Processa e valida a entrada numérica do usuário"""
        if not entrada or not entrada.strip():
            return 0
        entrada = entrada.strip()
        try:
            if re.match(r'^\d+\.?\d*$', entrada):
                numero = float(entrada)
                return int(numero)
            else:
                raise ValueError("Formato de número inválido")
        except (ValueError, TypeError):
            st.warning(f"⚠️ Número inválido informado: '{entrada}'. Use apenas números inteiros.")
            return 0

    def buscar_ponderacao_api(nome_centro_custo):
        """
        Busca a ponderação na API baseada no nome do centro de custo
        Prioriza ponderações salvas manualmente
        """
        # Primeiro, verifica se há ponderação salva manualmente
        ponderacoes_salvas = st.session_state.get(
            f'ponderacoes_salvas_PRODUCAO_{competencia}_{unidade_selecionada}',
            {}
        )
        
        if nome_centro_custo in ponderacoes_salvas:
            return ponderacoes_salvas[nome_centro_custo]
        
        # Se não há ponderação salva, busca na API
        if base_de_producao.empty:
            return ""  # Retorna vazio em vez de mensagem de API indisponível
            
        # Normaliza o nome do centro de custo para comparação
        nome_normalizado = nome_centro_custo.strip().upper()
        
        for idx, row in base_de_producao.iterrows():
            centro_api = row['centroDeCustoDescr'].strip().upper()
            
            # Match exato
            if centro_api == nome_normalizado:
                return row['unidadeDeProducaoDescr']
        
        # Se não encontrou match, retorna vazio
        return ""

    try:
        # Unidade selecionada pelo usuário
        unidade_selecionada = st.session_state.get('unidade_selecionada', '')

        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        # Carrega a base de centros de custo (fonte principal)
        try:
            df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        except FileNotFoundError:
            st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        # Nome do formulário para filtrar os centros de custo aplicáveis
        nome_formulario = "Produção"

        # # CHAVE PADRÃO PARA VALIDAÇÃO
        validation_key = f"validation_{nome_formulario}_{competencia}_{unidade_selecionada}"

        # Inicializar estado de validação se não existir
        if validation_key not in st.session_state:
            st.session_state[validation_key] = {
                'calculado': False,
                'valido': False
            }

        if nome_formulario not in df_centros_custo.columns:
            st.error(f"❌ Coluna '{nome_formulario}' não encontrada no arquivo Excel!")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        # Filtra centros de custo aplicáveis do Excel
        centros_aplicaveis = df_centros_custo[
            (df_centros_custo['UNIDADE PLANILHA'] == unidade_selecionada) & 
            (df_centros_custo[nome_formulario] == True)
        ]

        if centros_aplicaveis.empty:
            st.warning(f"⚠️ Nenhum centro de custo encontrado para a unidade '{unidade_selecionada}' no arquivo Excel.")
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        # Lista para armazenar as respostas
        dados_formulario = []

        # Mostra informações iniciais
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")

        # Carrega dados salvos
        dados_salvos = carregar_dados_salvos(competencia, unidade_selecionada, "PRODUCAO")

        # Gerencia session_state para os campos
        form_key = f"form_data_PRODUCAO_{competencia}_{unidade_selecionada}"
        if form_key not in st.session_state:
            st.session_state[form_key] = {}

        # Carrega valores salvos no session_state
        if dados_salvos:
            if 'formularios_data' in st.session_state and "PRODUCAO" in st.session_state['formularios_data']:
                df_salvo = st.session_state['formularios_data']["PRODUCAO"]
                if df_salvo is not None and not df_salvo.empty:
                    
                    # Cria um dicionário de ponderações corrigidas para usar durante a renderização
                    ponderacoes_salvas = {}
                    for _, row in df_salvo.iterrows():
                        ponderacoes_salvas[row['Centro de Custo']] = row['Ponderação']
                    
                    # Armazena no session_state para uso posterior
                    st.session_state[f'ponderacoes_salvas_PRODUCAO_{competencia}_{unidade_selecionada}'] = ponderacoes_salvas

                    df_filtrado = df_salvo[df_salvo.get('Competência', '') == competencia]
                    
                    for idx, row in centros_aplicaveis.iterrows():
                        centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
                        codigo_cc = row['CÓD CC']
                        
                        # Faz o "VLOOKUP" para buscar a ponderação na API
                        ponderacao = buscar_ponderacao_api(centro_custo)
                        
                        # Cria a chave única para este campo
                        key = f"producao_vlookup_{codigo_cc}_{competencia}_{unidade_selecionada}"

                        field_key = f"{nome_formulario}_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        valor_default = st.session_state[form_key].get(field_key, "0")

                        entrada = st.text_input(
                            f"**{centro_custo}** (Código: {codigo_cc})",
                            value=valor_default,
                            # ... resto igual
                            key=field_key
                        )
   
                        # Atualiza session_state
                        st.session_state[form_key][key] = entrada

                        quantidade = processar_entrada_numero(entrada)

                        dados_formulario.append({
                            'Competência': competencia,
                            'Ponderação': ponderacao,  # Ponderação vinda do "VLOOKUP" na API
                            'Centro de Custo': centro_custo,
                            'Quantidade': quantidade
                        })

        # Inputs dinâmicos por centro de custo (baseados no Excel + ponderação da API)
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']
            
            # Faz o "VLOOKUP" para buscar a ponderação na API
            ponderacao = buscar_ponderacao_api(centro_custo)

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

            quantidade = processar_entrada_numero(entrada)

            dados_formulario.append({
                'Competência': competencia,
                'Ponderação': ponderacao,  # Ponderação vinda do "VLOOKUP" na API
                'Centro de Custo': centro_custo,
                'Quantidade': quantidade
            })

        # Converte para DataFrame
        df_resultado = pd.DataFrame(dados_formulario)

        if df_resultado.empty:
            return pd.DataFrame(columns=[
                'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
            ])

        # BOTÃO DE VERIFICAÇÃO PRÉVIA DAS PONDERAÇÕES
        validar_clicked = st.form_submit_button("🔍 Verificar e Validar Ponderações", type="secondary", use_container_width=True)

        if validar_clicked:
            with st.spinner("Validando ponderações..."):
                verificacao_key = f'verificacao_realizada_{nome_formulario}_{competencia}_{unidade_selecionada}'
                if verificacao_key not in st.session_state:
                    st.session_state[verificacao_key] = False
                                
                # NOVA VALIDAÇÃO: Verifica ponderações vazias APENAS para registros com quantidade > 0
                df_com_quantidade = df_resultado[df_resultado['Quantidade'] > 0].copy()
                

                if not df_com_quantidade.empty:
                    # Identifica registros sem ponderação que têm quantidade preenchida
                    registros_sem_ponderacao = df_com_quantidade[
                        (df_com_quantidade['Ponderação'].isna()) | 
                        (df_com_quantidade['Ponderação'] == "") |
                        (df_com_quantidade['Ponderação'].str.contains("API indisponível|Sem match", na=False))
                    ]
                    
                    if not registros_sem_ponderacao.empty:
                        st.error("❌ **Erro de Validação: Ponderações em branco**")
                        st.warning("Os seguintes centros de custo têm quantidade preenchida mas estão sem ponderação válida:")
                        
                        # Lista os problemas encontrados
                        for idx, row in registros_sem_ponderacao.iterrows():
                            st.write(f"• **{row['Centro de Custo']}** (Quantidade: {row['Quantidade']})")
                        
                        # Salva estado de erro
                        st.session_state[validation_key] = {
                            'calculado': True,
                            'valido': False,
                            'erro': 'ponderacao_vazia',
                            'registros_problematicos': len(registros_sem_ponderacao)
                        }
                        
                        # NOVA FUNCIONALIDADE: Permite edição manual das ponderações
                        st.markdown("### ✏️ Correção Manual de Ponderações")
                        st.info("Você pode preencher manualmente as ponderações em branco abaixo:")
                        
                        # Cria inputs para corrigir ponderações vazias
                        ponderacoes_corrigidas = {}
                        
                        for idx, row in registros_sem_ponderacao.iterrows():
                            st.write(f"**{row['Centro de Custo']}** (Quantidade: {row['Quantidade']})")
                            
                            # Input para correção manual
                            ponderacao_key = f"correcao_ponderacao_{row['Centro de Custo']}_{competencia}"
                            ponderacao_corrigida = st.text_input(
                                f"Ponderação para {row['Centro de Custo']}:",
                                value="",
                                placeholder="Digite a ponderação correta...",
                                key=ponderacao_key
                            )
                            
                            if ponderacao_corrigida.strip():
                                ponderacoes_corrigidas[row['Centro de Custo']] = ponderacao_corrigida.strip()
                        
                        # Checkbox para aplicar correções
                        aplicar_correcoes = st.checkbox("✅ Aplicar Correções Manuais (necessário marcar antes de clicar em 'Verificar e Validar Ponderações')", key="aplicar_correcoes")
                        if aplicar_correcoes:
                            if ponderacoes_corrigidas:
                                # Aplica as correções no DataFrame
                                for centro_custo, nova_ponderacao in ponderacoes_corrigidas.items():
                                    mask = df_resultado['Centro de Custo'] == centro_custo
                                    df_resultado.loc[mask, 'Ponderação'] = nova_ponderacao
                                
                                # ✅ CORREÇÃO: Salva as ponderações no session_state para persistir
                                ponderacoes_key = f'ponderacoes_salvas_PRODUCAO_{competencia}_{unidade_selecionada}'
                                if ponderacoes_key not in st.session_state:
                                    st.session_state[ponderacoes_key] = {}
                                
                                st.session_state[ponderacoes_key].update(ponderacoes_corrigidas)
                                
                                st.success(f"✅ {len(ponderacoes_corrigidas)} ponderação(ões) corrigida(s) manualmente!")
                                
                                # Atualiza o estado de validação para válido
                                st.session_state[validation_key] = {
                                    'calculado': True,
                                    'valido': True, 
                                    'corrigido_manualmente': True
                                }
                            else:
                                st.warning("⚠️ Preencha pelo menos uma ponderação para aplicar as correções.")
                        
                        st.markdown("---")
                        st.info(f"""
                        **Orientações para preenchimento manual de ponderações:**

                        ⚠️ **Caso 1 – Existe quantidade mas não há ponderação correspondente:**  
                        1. Acesse o arquivo no link abaixo  
                        👉 [Consultar Ponderações](https://docs.google.com/spreadsheets/d/1bPV0IFLf6L6JwFX5AabqdQSjv_nqgCvVoQxLWhPyjIg/edit?gid=0#gid=0)  
                        2. Confirme a **filial da sua unidade** dentro da planilha  
                        3. Localize o **centro de custo** que deseja consultar  
                        4. Copie a **ponderação correspondente** e digite manualmente no campo indicado  

                        ✅ **Caso 2 – A quantidade foi preenchida errado (ou deveria ser zero):**  
                        → Basta ajustar o valor para **0** e salvar novamente, sem necessidade de preencher manualmente a ponderação.
                        """)
                        
                    else:
                        # Tudo OK
                        st.success("✅ **Todas as ponderações estão válidas!**")
                        st.session_state[validation_key] = {
                            'calculado': True,
                            'valido': True
                        }
                else:
                    st.info("ℹ️ Nenhum centro de custo com quantidade preenchida para validar.")
                    st.session_state[validation_key] = {
                        'calculado': True,
                        'valido': True
                    }

        # Só executa a validação se o botão foi clicado ou se já foi validado antes
        executar_validacao = st.session_state.get(f'verificacao_realizada_{nome_formulario}_{competencia}_{unidade_selecionada}', False)

        if executar_validacao and not validar_clicked:
            # Mostra resultado da validação anterior (sem reprocessar)
            verificacao_key = f'verificacao_realizada_{nome_formulario}_{competencia}_{unidade_selecionada}'
            # executar_validacao = st.session_state.get(verificacao_key, False)
            if verificacao_key not in st.session_state:
                st.session_state[verificacao_key] = False

            if executar_validacao and not validar_clicked:
                # Mostra resultado da validação anterior (sem reprocessar)
                validation_state = st.session_state.get(validation_key, {})
                
                if validation_state.get('valido', False):
                    st.success("✅ **Ponderações validadas anteriormente!**")
                elif validation_state.get('erro') == 'ponderacao_vazia':
                    problemas = validation_state.get('registros_problematicos', 0)
                    st.error(f"❌ **{problemas} ponderação(ões) ainda precisam ser corrigidas**")
                    st.info("💡 Clique novamente em 'Verificar e Validar Ponderações' para corrigir")

        # Mostra resumo
        if not df_resultado.empty:
            st.write("---")
            st.write("**📊 Resumo dos dados inseridos:**")
            registros_preenchidos = len(df_resultado[df_resultado['Quantidade'] != 0])
            total_quantidade = df_resultado['Quantidade'].sum()
            ponderacoes_unicas = df_resultado['Ponderação'].nunique()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Centros Preenchidos", registros_preenchidos)
            with col2:
                st.metric("Total de Centros", len(df_resultado))
            with col3:
                st.metric("Total de Atendimentos", total_quantidade)
            with col4:
                st.metric("Ponderações Únicas", ponderacoes_unicas)

            # NOVA SEÇÃO: Status de validação visual
            if registros_preenchidos > 0:
                df_com_dados = df_resultado[df_resultado['Quantidade'] > 0]
                ponderacoes_validas = len(df_com_dados[
                    (df_com_dados['Ponderação'] != "") & 
                    (df_com_dados['Ponderação'].notna()) &
                    (~df_com_dados['Ponderação'].str.contains("API indisponível|Sem match", na=False))
                ])
                
                if ponderacoes_validas == registros_preenchidos:
                    st.success(f"✅ Todas as {registros_preenchidos} ponderações estão válidas!")
                else:
                    st.error(f"❌ {registros_preenchidos - ponderacoes_validas} de {registros_preenchidos} ponderações estão inválidas")
                    if not executar_validacao:
                        st.info("💡 Clique em 'Verificar e Validar Ponderações' para corrigir os problemas")
                        
        # Filtra apenas linhas onde a coluna 'Ponderação' possui valor não vazio e não nulo
        df_resultado = df_resultado[df_resultado['Ponderação'].notna() & (df_resultado['Ponderação'] != "")]
        return df_resultado

    except Exception as e:
        st.error(f"❌ Erro ao processar o formulário: {str(e)}")
        return pd.DataFrame(columns=[
            'Competência', 'Ponderação', 'Centro de Custo', 'Quantidade'
        ])