import streamlit as st
import pandas as pd
import datetime
import re
from datetime import timedelta
from utils.carregar_dados import carregar_dados_salvos

# Carregar tabela long de simultaneidade
df_simultaneidade = pd.read_excel("data/fatores_simultaneidade.xlsx")
df_litros_wide = pd.read_excel("data/fatores_litros_por_minuto.xlsx")

def render_form(competencia):
    """
    Renderiza o formulário RC_Consumo_de_Gases_Medicinais - Nova versão
    """
    # Caixa de instruções
    with st.expander("📋 Instruções - Consumo de Gases Medicinais", expanded=False):
        st.markdown("""
    <div style='overflow-x: auto'>

    Este formulário coleta informações para calcular o **consumo de oxigênio por setor**.  
    O cálculo é necessário para **ratear os custos** de forma justa entre os centros de custo.

    ### 🔹 Explicação dos Campos

    1. **Quantidade de pontos de oxigênio**  
    → Representa o número total de pontos instalados no setor.   
    Define a capacidade máxima do setor e ajuda a identificar o consumo potencial.

    ---

    2. **Taxa de ocupação (%)**  
    → Percentual médio de leitos ocupados no mês.  
    **Por que importa?**  
    Permite calcular quantos pontos estavam realmente em uso, evitando superestimar o consumo.
    Exemplo: Na **UTI**, normalmente todos os pontos estão sempre em uso. Já na **enfermaria**, muitos pontos ficam livres.  

    ---

    3. **Simultaneidade (%)**  
    → Percentual médio de pontos que funcionam ao mesmo tempo.  
    Exemplo: Na UTI, praticamente todos os pacientes usam oxigênio simultaneamente. Já em uma enfermaria, apenas parte dos pacientes costuma usar.  
    **Por que importa?**  
    Representa o **pico de uso real** do setor, evitando inflar ou reduzir demais o consumo estimado.

    ---

    4. **Consumo por paciente/ponto (L/min)**  
    → Média de oxigênio utilizado por paciente ativo (litros por minuto).  
    **Por que importa?**  
    É o fator base para estimar o consumo real em litros de cada ponto em uso.

    ---

    5. **Horas de uso por dia (h/dia)**  
    → Quantas horas, em média, cada paciente/ponto usa oxigênio por dia.  
    **Por que importa?**  
    Multiplica o consumo por paciente para refletir a duração do uso diário.

    ---

    6. **Dias de uso por mês (dias/mês)**  
    → Quantos dias no mês, em média, os pacientes utilizam oxigênio.  
    **Por que importa?**  
    Ajusta o cálculo para refletir o uso mensal.

    ---

    7. **Consumo total em litros (L)**  
    → Resultado do cálculo em litros considerando todos os fatores acima.  
    **Por que importa?**  
    É a primeira métrica de volume antes da conversão.

    ---

    8. **Consumo total em metros cúbicos (m³)**  
    → Conversão do resultado para m³ (1 m³ = 1000 L).  
    **Por que importa?**  
    É a unidade usada na **cobrança e rateio de custos** entre os setores.

    ---

    ### 🔹 Resumindo
    Esses campos juntos permitem calcular **quanto cada setor realmente consome de oxigênio**.  
    O resultado final em m³ é usado para dividir o **custo total** proporcionalmente entre os setores, de forma justa e transparente.
    A lógica por trás é que a unidade não paga pelo número de pontos instalados nem pelo número de leitos ocupados, mas sim pelo consumo real de oxigênio.
    Só que, para chegar nesse consumo real, precisamos de todas essas camadas (capacidade, ocupação, simultaneidade, duração e intensidade do uso).

    ---

    ### 🔹 Exemplo Prático

    | Setor       | Pontos | Ocupação | Simult. | Consumo L/min | Horas/dia | Dias/mês | Consumo total (m³) |
    |------------|--------|----------|---------|----------------|-----------|----------|------------------|
    | UTI        | 20     | 50%      | 80%     | 150            | 24        | 30       | 51.840           |
    | Enfermaria | 20     | 40%      | 30%     | 50             | 8         | 22       | 1.267,20          |

    **Como interpretar:**  
    - Na **UTI**, a maioria dos pontos está em uso simultâneo, gerando maior consumo e custo.  
    - Na **Enfermaria**, menor simultaneidade e uso diário resultam em consumo menor.  
    - O consumo total em m³ será a base para **rateio proporcional de custos** entre setores.

    ---
                    
    </div>
    """, unsafe_allow_html=True)

    def processar_entrada_numero(entrada, permitir_decimal=True):
        """Processa entrada de texto e converte para número"""
        if not entrada or not entrada.strip():
            return 0.0 if permitir_decimal else 0
        entrada = entrada.strip()
        try:
            entrada = entrada.replace(',', '.')
            numero = float(entrada)
            return round(numero, 3) if permitir_decimal else int(numero)
        except (ValueError, TypeError):
            st.warning(f"⚠️ Número inválido: '{entrada}'")
            return 0.0 if permitir_decimal else 0

    def verificar_combinacao_valida(local, gas, df_referencia, tipo_tabela="simultaneidade"):
        """Verifica se a combinação local/gás é válida e retorna o valor"""
        try:
            # Mapeamento dos gases para ambas as tabelas
            mapa_gases = {
                "Oxigênio medicinal": "Oxigênio medicinal",
                "Ar medicinal": "Ar medicinal", 
                "Óxido nitroso": "Óxido nitroso medicinal",
                "Vácuo clínico": "Vácuo clínico"
            }
            
            coluna_gas = mapa_gases.get(gas)
            if not coluna_gas:
                return None, "Gás não encontrado"
            
            # Filtrar por local
            filtro = df_referencia[df_referencia["Local"] == local]
            if filtro.empty:
                return None, "Local não encontrado"
            
            # Verificar se a coluna do gás existe
            if coluna_gas not in df_referencia.columns:
                return None, "Gás não disponível nesta tabela"
            
            # Obter o valor
            valor = filtro[coluna_gas].values[0]
            
            # Verificar se é "Não aplicável" ou valor vazio
            if pd.isna(valor) or str(valor).strip().lower() == "não aplicável":
                return None, "Não aplicável"
            
            # Tentar converter para número
            try:
                valor_numerico = float(str(valor).strip())
                return valor_numerico, None
            except (ValueError, TypeError):
                return None, "Valor inválido"
                
        except Exception as e:
            return None, f"Erro: {str(e)}"

    def calcular_consumo_total(pontos_o2, tx_ocupacao, simultaneidade, consumo_litros_min, horas_dia, dias_mes):
        """Calcula o consumo total em m³"""
        try:
            # Validar se todos os valores são maiores que zero
            if any(val <= 0 for val in [pontos_o2, tx_ocupacao, simultaneidade, consumo_litros_min, horas_dia, dias_mes]):
                return 0, "Todos os valores devem ser maiores que zero"
            
            # Pontos em uso considerando ocupação e simultaneidade
            pontos_uso = pontos_o2 * (tx_ocupacao / 100) * (simultaneidade / 100)
            
            # Consumo total em litros
            consumo_litros = pontos_uso * consumo_litros_min * horas_dia * dias_mes * 60
            
            # Conversão para m³
            consumo_m3 = consumo_litros / 1000
            
            return round(consumo_m3, 6), None
            
        except Exception as e:
            return 0, f"Erro no cálculo: {str(e)}"

    try:
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        unidade_selecionada = st.session_state.get('unidade_selecionada', '')
        
        if not unidade_selecionada:
            st.error("❌ Nenhuma unidade selecionada!")
            return pd.DataFrame()

        nome_formulario = "Consumo de Gases Medicinais (m³)"
        if nome_formulario not in df_centros_custo.columns:
            st.error(f"❌ Coluna '{nome_formulario}' não encontrada no Excel!")
            return pd.DataFrame()

        centros_aplicaveis = df_centros_custo[
            (df_centros_custo['UNIDADE PLANILHA'] == unidade_selecionada) & 
            (df_centros_custo[nome_formulario] == True)
        ]

        if centros_aplicaveis.empty:
            st.warning(f"⚠️ Nenhum centro de custo encontrado para a unidade '{unidade_selecionada}'.")
            return pd.DataFrame()

        # Carrega dados salvos
        dados_salvos = carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario)

        # Gerencia session_state para os campos
        form_key = f"form_data_{nome_formulario}_{competencia}_{unidade_selecionada}"
        if form_key not in st.session_state:
            st.session_state[form_key] = {}
            if dados_salvos:
                for centro_custo_nome, dados in dados_salvos.items():
                    centro_encontrado = centros_aplicaveis[
                        centros_aplicaveis['DESCRIÇÃO DE CENTRO DE CUSTO'] == centro_custo_nome
                    ]
                    
                    if dados_salvos:
                        for centro_custo_nome, dados in dados_salvos.items():
                            centro_encontrado = centros_aplicaveis[
                                centros_aplicaveis['DESCRIÇÃO DE CENTRO DE CUSTO'] == centro_custo_nome
                            ]
                            
                            if not centro_encontrado.empty:
                                codigo_cc = centro_encontrado.iloc[0]['CÓD CC']
                                
                                # Carrega dados salvos para os campos específicos
                                st.session_state[form_key][f"pontos_o2_{codigo_cc}"] = str(dados.get('pontos_o2', '0'))
                                st.session_state[form_key][f"tx_ocupacao_{codigo_cc}"] = str(dados.get('tx_ocupacao', '0'))
                                st.session_state[form_key][f"local_simult_{codigo_cc}"] = dados.get('local_simult', 'Selecione um local...')
                                st.session_state[form_key][f"gas_simult_{codigo_cc}"] = dados.get('gas_simult', 'Selecione um gás...')
                                st.session_state[form_key][f"local_litros_{codigo_cc}"] = dados.get('local_litros', 'Selecione um local...')
                                st.session_state[form_key][f"gas_litros_{codigo_cc}"] = dados.get('gas_litros', 'Selecione um gás...')
                                st.session_state[form_key][f"horas_dia_{codigo_cc}"] = str(dados.get('horas_dia', '0'))
                                st.session_state[form_key][f"dias_mes_{codigo_cc}"] = str(dados.get('dias_mes', '0'))

        ponderacao = "Consumo de Gases Medicinais (m³)"
        st.write(f"**Ponderação**: {ponderacao}")
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")

        # Inicializar session state para controle do formulário
        if 'dados_calculados_gases' not in st.session_state:
            st.session_state.dados_calculados_gases = {}
        if 'calculo_realizado_gases' not in st.session_state:
            st.session_state.calculo_realizado_gases = False

        # NOVA ABORDAGEM: Listas completas de opções (todos os locais e gases disponíveis)
        
        # Obter todos os locais únicos de ambas as tabelas
        locais_simultaneidade = sorted(df_simultaneidade["Local"].unique().tolist())
        locais_litros = sorted(df_litros_wide["Local"].tolist())
        todos_locais = sorted(list(set(locais_simultaneidade + locais_litros)))
        
        # Obter todos os gases únicos de ambas as tabelas
        gases_simultaneidade = ["Oxigênio medicinal", "Ar medicinal", "Óxido nitroso medicinal", "Vácuo clínico"]
        gases_litros = ["Oxigênio medicinal", "Ar medicinal", "Óxido nitroso medicinal", "Vácuo clínico"]
        todos_gases = sorted(list(set(gases_simultaneidade + gases_litros)))

        st.markdown("---")
        st.markdown("### 📝 Preenchimento dos Dados")
        
        # Alert sobre o novo fluxo
        st.info("""
        📝 Fluxo de Preenchimento dos Dados
        1. Preencha todos os campos obrigatórios.
        2. Clique em "Calcular" para validar as informações.
        
        ⚠️ Atenção: não utilize o botão "Salvar" antes de realizar o cálculo.
        
        3. Se não houver erros no cálculo, finalize clicando em "Salvar".
                
        Este formulário utiliza duas tabelas de referência para os cálculos:

        - 🔗 [Tabela de Simultaneidade](https://docs.google.com/spreadsheets/d/1kIMf9p4Mf4UM4DVXAVkADiOskatfMkdB/edit?gid=1232514839#gid=1232514839)  
        - 🔗 [Tabela de Fatores de Litros por Minuto](https://docs.google.com/spreadsheets/d/1lPafPsnCDoFGbZ9aoqKv3L4ZXcC7VVBo/edit?gid=1791880003#gid=1791880003)  

        Você pode acessá-las para verificar os valores utilizados.
        """)

        dados_formulario = []

        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
            codigo_cc = row['CÓD CC']

            st.markdown(f"#### **{centro_custo}** (Código: {codigo_cc})")
            
            # Dados básicos
            col1, col2 = st.columns(2)
            with col1:
                valor_pontos = st.session_state[form_key].get(f"pontos_o2_{codigo_cc}", "0")
                pontos_o2 = st.text_input(f"Pontos O2", valor_pontos, key=f"pontos_o2_{codigo_cc}")
                st.session_state[form_key][f"pontos_o2_{codigo_cc}"] = pontos_o2
            with col2:
                valor_ocupacao = st.session_state[form_key].get(f"tx_ocupacao_{codigo_cc}", "0")
                tx_ocupacao = st.text_input(f"Tx. Ocupação (%)", valor_ocupacao, key=f"tx_ocupacao_{codigo_cc}")
                st.session_state[form_key][f"tx_ocupacao_{codigo_cc}"] = tx_ocupacao

            # --- SEÇÃO SIMULTANEIDADE ---
            st.markdown("##### 🔄 Simultaneidade")
            col3, col4 = st.columns(2)
            with col3:
                valor_local_simult = st.session_state[form_key].get(f"local_simult_{codigo_cc}", "Selecione um local...")
                try:
                    index_local_simult = (["Selecione um local..."] + todos_locais).index(valor_local_simult)
                except ValueError:
                    index_local_simult = 0

                local_simult = st.selectbox(
                    f"Local para Simultaneidade", 
                    ["Selecione um local..."] + todos_locais, 
                    index=index_local_simult,
                    key=f"local_simult_{codigo_cc}"
                )
                st.session_state[form_key][f"local_simult_{codigo_cc}"] = local_simult

            with col4:
                valor_gas_simult = st.session_state[form_key].get(f"gas_simult_{codigo_cc}", "Selecione um gás...")
                try:
                    index_gas_simult = (["Selecione um gás..."] + todos_gases).index(valor_gas_simult)
                except ValueError:
                    index_gas_simult = 0

                gas_simult = st.selectbox(
                    f"Gás para Simultaneidade", 
                    ["Selecione um gás..."] + todos_gases, 
                    index=index_gas_simult,
                    key=f"gas_simult_{codigo_cc}"
                )
                st.session_state[form_key][f"gas_simult_{codigo_cc}"] = gas_simult

            # --- SEÇÃO LITROS POR MINUTO ---
            st.markdown("##### 💧 Consumo (L/min)")
            col5, col6 = st.columns(2)
            with col5:
                valor_local_litros = st.session_state[form_key].get(f"local_litros_{codigo_cc}", "Selecione um local...")
                try:
                    index_local_litros = (["Selecione um local..."] + todos_locais).index(valor_local_litros)
                except ValueError:
                    index_local_litros = 0

                local_litros = st.selectbox(
                    f"Local para Consumo", 
                    ["Selecione um local..."] + todos_locais, 
                    index=index_local_litros,
                    key=f"local_litros_{codigo_cc}"
                )
                st.session_state[form_key][f"local_litros_{codigo_cc}"] = local_litros

            with col6:
                valor_gas_litros = st.session_state[form_key].get(f"gas_litros_{codigo_cc}", "Selecione um gás...")
                try:
                    index_gas_litros = (["Selecione um gás..."] + todos_gases).index(valor_gas_litros)
                except ValueError:
                    index_gas_litros = 0

                gas_litros = st.selectbox(
                    f"Gás para Consumo", 
                    ["Selecione um gás..."] + todos_gases, 
                    index=index_gas_litros,
                    key=f"gas_litros_{codigo_cc}"
                )
                st.session_state[form_key][f"gas_litros_{codigo_cc}"] = gas_litros


            # --- SEÇÃO TEMPO ---
            st.markdown("##### ⏰ Tempo de Uso")
            col7, col8 = st.columns(2)
            with col7:
                valor_horas_dia = st.session_state[form_key].get(f"horas_dia_{codigo_cc}", "0")
                horas_dia = st.text_input(f"Horas/dia", valor_horas_dia, key=f"horas_dia_{codigo_cc}")
                st.session_state[form_key][f"horas_dia_{codigo_cc}"] = horas_dia
            with col8:
                valor_dias_mes = st.session_state[form_key].get(f"dias_mes_{codigo_cc}", "0")
                dias_mes = st.text_input(f"Dias/Mês", valor_dias_mes, key=f"dias_mes_{codigo_cc}")
                st.session_state[form_key][f"dias_mes_{codigo_cc}"] = dias_mes

            # Mostrar resultado do cálculo se já foi calculado
            if codigo_cc in st.session_state.dados_calculados_gases:
                dados_calc = st.session_state.dados_calculados_gases[codigo_cc]
                st.success(f"✅ **Resultado**: {dados_calc['consumo_total']:.2f} m³")

            # Armazenar dados do centro de custo atual
            dados_cc = {
                'centro_custo': centro_custo,
                'codigo_cc': codigo_cc,
                'pontos_o2': pontos_o2,
                'tx_ocupacao': tx_ocupacao,
                'local_simult': local_simult,
                'gas_simult': gas_simult,
                'local_litros': local_litros,
                'gas_litros': gas_litros,
                'horas_dia': horas_dia,
                'dias_mes': dias_mes
            }
            dados_formulario.append(dados_cc)

            st.markdown("---")

        # Botão de calcular
        calcular_clicked = st.form_submit_button("🔢 Calcular e Validar Todos os Dados", type="primary", use_container_width=True)
        
        if calcular_clicked:
            with st.spinner("Calculando e validando..."):
                st.session_state.dados_calculados_gases = {}
                st.session_state.calculo_realizado_gases = False
                
                todos_calculos_validos = True
                erros_encontrados = []
                sucessos = []
                centros_ignorados = []

                for dados_cc in dados_formulario:
                    codigo_cc = dados_cc['codigo_cc']
                    centro_custo = dados_cc['centro_custo']
                    
                    # Processar valores numéricos
                    pontos_o2_val = processar_entrada_numero(dados_cc['pontos_o2'], permitir_decimal=False)
                    tx_ocupacao_val = processar_entrada_numero(dados_cc['tx_ocupacao'], permitir_decimal=True)
                    horas_dia_val = processar_entrada_numero(dados_cc['horas_dia'], permitir_decimal=True)
                    dias_mes_val = processar_entrada_numero(dados_cc['dias_mes'], permitir_decimal=True)

                    # Se todos os valores estão zerados e não há seleção de gás/local → IGNORAR SILENCIOSAMENTE
                    if (
                        pontos_o2_val == 0 and
                        tx_ocupacao_val == 0 and
                        horas_dia_val == 0 and
                        dias_mes_val == 0 and
                        dados_cc['local_simult'] == "Selecione um local..." and
                        dados_cc['gas_simult'] == "Selecione um gás..." and
                        dados_cc['local_litros'] == "Selecione um local..." and
                        dados_cc['gas_litros'] == "Selecione um gás..."
                    ):
                        centros_ignorados.append(centro_custo)
                        continue

                    # Verificar se valores são válidos
                    if any(val <= 0 for val in [pontos_o2_val, tx_ocupacao_val, horas_dia_val, dias_mes_val]):
                        erros_encontrados.append(f"**{centro_custo}**: Todos os campos numéricos devem ser maiores que zero")
                        todos_calculos_validos = False
                        continue

                    # Verificar combinação de simultaneidade
                    if dados_cc['local_simult'] == "Selecione um local..." or dados_cc['gas_simult'] == "Selecione um gás...":
                        erros_encontrados.append(f"**{centro_custo}**: Selecione Local e Gás para Simultaneidade")
                        todos_calculos_validos = False
                        continue
                        
                    valor_simult, erro_simult = verificar_combinacao_valida(
                        dados_cc['local_simult'], dados_cc['gas_simult'], df_simultaneidade, "simultaneidade"
                    )
                    
                    if erro_simult:
                        if erro_simult == "Não aplicável":
                            erros_encontrados.append(f"**{centro_custo}**: O gás **{dados_cc['gas_simult']}** não é aplicável para **{dados_cc['local_simult']}**")
                        else:
                            erros_encontrados.append(f"**{centro_custo}**: Erro na simultaneidade - {erro_simult}")
                        todos_calculos_validos = False
                        continue

                    # Verificar combinação de litros por minuto
                    if dados_cc['local_litros'] == "Selecione um local..." or dados_cc['gas_litros'] == "Selecione um gás...":
                        erros_encontrados.append(f"**{centro_custo}**: Selecione Local e Gás para Consumo")
                        todos_calculos_validos = False
                        continue
                        
                    valor_litros, erro_litros = verificar_combinacao_valida(
                        dados_cc['local_litros'], dados_cc['gas_litros'], df_litros_wide, "litros"
                    )
                    
                    if erro_litros:
                        if erro_litros == "Não aplicável":
                            erros_encontrados.append(f"**{centro_custo}**: O gás **{dados_cc['gas_litros']}** não é aplicável para **{dados_cc['local_litros']}**")
                        else:
                            erros_encontrados.append(f"**{centro_custo}**: Erro no consumo - {erro_litros}")
                        todos_calculos_validos = False
                        continue

                    # Realizar cálculo final
                    consumo_total, erro_calculo = calcular_consumo_total(
                        pontos_o2_val, tx_ocupacao_val, valor_simult, valor_litros, 
                        horas_dia_val, dias_mes_val
                    )
                    
                    if erro_calculo:
                        erros_encontrados.append(f"**{centro_custo}**: {erro_calculo}")
                        todos_calculos_validos = False
                        continue

                    # Armazenar resultado válido
                    st.session_state.dados_calculados_gases[codigo_cc] = {
                        'centro_custo': centro_custo,
                        'consumo_total': consumo_total,
                        'simultaneidade': valor_simult,
                        'consumo_litros_min': valor_litros,
                        'pontos_o2': pontos_o2_val,
                        'tx_ocupacao': tx_ocupacao_val,
                        'horas_dia': horas_dia_val,
                        'dias_mes': dias_mes_val
                    }
                    
                    sucessos.append(f"**{centro_custo}**: {consumo_total:.3f} m³")

                    # Inicializar o estado de validação seguindo o padrão dos outros formulários
                    validation_key = f"validation_{nome_formulario}_{competencia}_{st.session_state.get('unidade_selecionada', '')}"
                    if validation_key not in st.session_state:
                        st.session_state[validation_key] = {
                            'calculado': False,
                            'valido': False
                        }

                    # Marcar cálculo como realizado se houve pelo menos um sucesso
                    if sucessos:
                        st.session_state.calculo_realizado_gases = True  # Manter para compatibilidade
                        st.session_state[validation_key]['calculado'] = True
                        st.session_state[validation_key]['valido'] = todos_calculos_validos

                # RESULTADO CONSOLIDADO - UMA ÚNICA MENSAGEM
                if erros_encontrados and not sucessos:
                    # Só erros
                    st.error("### ❌ Problemas encontrados nos dados:")
                    for erro in erros_encontrados:
                        st.write(f"• {erro}")
                    st.warning("**Corrija os problemas acima e clique novamente em 'Calcular'**")
                    
                elif erros_encontrados and sucessos:
                    # Erros e sucessos misturados
                    st.warning("### ⚠️ Cálculo parcial realizado:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"**✅ Válidos ({len(sucessos)}):**")
                        for sucesso in sucessos:
                            st.write(f"• {sucesso}")
                    
                    with col2:
                        st.error(f"**❌ Com problemas ({len(erros_encontrados)}):**")
                        for erro in erros_encontrados:
                            st.write(f"• {erro}")
                    
                    st.info("**Corrija os problemas e clique novamente em 'Calcular' para validar todos os dados**")
                    
                elif sucessos and not erros_encontrados:
                    # Só sucessos
                    st.success(f"### ✅ Cálculo realizado com sucesso! ({len(sucessos)} centros de custo)")
                    
                    # Mostrar apenas um resumo compacto
                    total_consumo = sum(dados['consumo_total'] for dados in st.session_state.dados_calculados_gases.values())
                    st.info(f"**Consumo total calculado**: {total_consumo:.3f} m³")
                    
                    # Botão destacado para salvar
                    st.markdown("---")
                    st.success("**🎯 Dados prontos para salvar! Use o botão 'Salvar' no final da página.**")

        # Mostrar resumo detalhado apenas se solicitado
        if st.session_state.get('dados_calculados_gases'):
            with st.expander("📊 Ver Resumo Detalhado dos Cálculos", expanded=False):
                dados_resumo = []
                total_consumo = 0
                
                for codigo_cc, dados in st.session_state.dados_calculados_gases.items():
                    dados_resumo.append({
                        'Centro de Custo': dados['centro_custo'],
                        'Código': codigo_cc,
                        'Consumo (m³)': f"{dados['consumo_total']:.2f}",
                        'Simultaneidade (%)': f"{dados['simultaneidade']:.1f}",
                        'Consumo L/min': f"{dados['consumo_litros_min']:.1f}"
                    })
                    total_consumo += dados['consumo_total']
                
                df_resumo = pd.DataFrame(dados_resumo)
                st.dataframe(df_resumo, use_container_width=True)
                st.info(f"**Total Geral**: {total_consumo:.2f} m³")

        # Preparar dados para retorno se há cálculos válidos
        if st.session_state.get('dados_calculados_gases') and len(st.session_state.dados_calculados_gases) > 0:
            dados_para_retorno = []
            for codigo_cc, dados in st.session_state.dados_calculados_gases.items():
                # Buscar os dados do formulário para incluir nas informações extras
                form_data = st.session_state.get(form_key, {})
                
                dados_para_retorno.append({
                    'Competência': competencia,
                    'Ponderação': ponderacao,
                    'Centro de Custo': dados['centro_custo'],
                    'Quantidade': dados['consumo_total'],
                    # # Campos adicionais para salvar os detalhes
                    # 'Pontos_O2': dados['pontos_o2'],
                    # 'Tx_Ocupacao': dados['tx_ocupacao'],
                    # 'Local_Simult': form_data.get(f"local_simult_{codigo_cc}", "Selecione um local..."),
                    # 'Gas_Simult': form_data.get(f"gas_simult_{codigo_cc}", "Selecione um gás..."),
                    # 'Local_Litros': form_data.get(f"local_litros_{codigo_cc}", "Selecione um local..."),
                    # 'Gas_Litros': form_data.get(f"gas_litros_{codigo_cc}", "Selecione um gás..."),
                    # 'Horas_Dia': dados['horas_dia'],
                    # 'Dias_Mes': dados['dias_mes']
                })
            
            if dados_para_retorno:
                return pd.DataFrame(dados_para_retorno)

        return pd.DataFrame()

    except FileNotFoundError:
        st.error("❌ Arquivo não encontrado! Verifique se os arquivos Excel estão na pasta 'data/'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        return pd.DataFrame()