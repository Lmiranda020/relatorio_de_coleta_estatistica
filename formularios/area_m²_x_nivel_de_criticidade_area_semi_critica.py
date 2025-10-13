import streamlit as st
import pandas as pd
import re
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia): #crio uma função, que rece um argumento como nomeado com o parametro "competencia"
    def obter_dados_area_metro(competencia): # aqui crio outra função que recebe outro parametro também nomeado como competencia
        # e quando eu chamar essa função ele vai fazer a logica d alinha de baixo

        return st.session_state.get(f"dados_area_metro_{competencia}", pd.DataFrame()) 
        # a função retorna uma base da memoria do streamlir que possui como chave p texto "dados_area_m2_" + a competencia
        # caso não encontre essa chave ele vai retornar um dataframe vazio

    def processar_entrada_numero(entrada): 
        # crio outra função que vai receber um argumento nomeado como "entrada"

        if not entrada or not entrada.strip():
        # se esse argumento ou parametro, não exista ou não exista apos remover os espaços
        
            return 0
        # retornar o zero

        entrada = entrada.strip().replace(",", ".") 
        # Mas se ele existe, que é o pensamento logico ao contrario da condição acima
        # ele vai pegar o argumento passado para o parametro
        # remover os espaços do começo e no final da strig
        # depois faz um replace, substituindo virgula por ponto

        try:
        # aqui eu tento fazer algo com o argumento

            return float(entrada)
        # vou retornar esse valor convertido em string

        except ValueError: 
        # se de um ValueErros, que significa erro de conversão
        # por exemplo, tenta converter uma string para float
        
            st.warning(f"⚠️ Número inválido informado: '{entrada}'. Use apenas números (ex: 15 ou 15,5).")
        # se der esse erro vai aparecer uma mensagem no formarto warning do streamlit
        # que é uma caixa já formatada

            return 0
        # além de aparecer a mensagem
        # ele vai retornar 0 aonde a função for chamada

    with st.expander("📋 Instruções - Área Semi Crítica", expanded=False):
        st.markdown("""
        ### Como preencher este formulário:

        1. **Automaticamente** – puxando do formulário "Área Metro"
                    
        2. **Manual** – digitando os valores diretamente
                    
        | Criticidade            | Exemplos de áreas incluídas                                 |
        |------------------------|-------------------------------------------------------------|
        | Área Não Crítica - I   | Consultórios, recepção, áreas administrativas               |
        | Área Semi Crítica      | Enfermarias, salas de observação, medicação, pediatria      |
        | Área Crítica - I       | UTI, centro cirúrgico, emergência, salas de isolamento      |

        🧠 Esses dados são usados no rateio proporcional de custos de Higiene e Limpeza.
        """)

    try:
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx")
        # aqui leio o arquivo de centro de custo

        unidade = st.session_state.get('unidade_selecionada', '')
        # aqui recupero na memoria do streamlit a unidade
        # a linha de codigo que armazena ela na memoria é no app principal
        # então utilizo a chave unidade_selecionada para recuperar essa informação
        # se não encotrar ess achave ele retorna ""
        # mas se achar, armazena ela na variavel "unidade"

        if not unidade: 
        # se não tiver dado, ou seja se for vazio

            st.error("❌ Nenhuma unidade selecionada.")
        # mostra uma messagem no formato streamlit erro, que é uma caixa já formatad

            return pd.DataFrame()
        # e por ultimo retorna um dataframe vazio aonde for chamado essa função

        nome_formulario = "Área (m²) x Nível de Criticidade (Área Semi Crítica)"
        # aqui defino a variavel com o nome do formulario

        if nome_formulario not in df_centros_custo.columns:
        # se não existir o nome do formulario na base de centro de custo

            st.error(f"❌ Formulario '{nome_formulario}' não encontrado na base de centro de custo.")
        # vai aparecer essa mensagem com o nome do fomrulário

            return pd.DataFrame()
        # e vai retornar para aonde chamar essa função um dataframe vazio

        centros_aplicaveis = df_centros_custo[
        # crio um datafreme com um filtro, a partir da condição abaixo

            (df_centros_custo['UNIDADE PLANILHA'] == unidade) &
        # primeiro filtro na coluna UNIDADE PLANILHA  o que é o memso valor da unidade escolhida

            (df_centros_custo[nome_formulario] == True)
        # depois filtro apenas na coluna que correspode ao mesmo nome da variavel do nome do formulario, o que é TRUE oou seja o que está ticado
        ]

        if centros_aplicaveis.empty: 
        # se o dataframe filtrado for vazio, ele vai aplica a logica a baixo

            st.warning(f"Nenhum centro de custo encontrado para a unidade '{unidade}'.")
        # vai aparecer essa mensagem

            return pd.DataFrame()
        # além da mensagem vai retornar um dataframe vazio, para onde for chamado a função

        dados_area_metro = obter_dados_area_metro(competencia)
        # aqui crio uma variavel e chamo a execução da função
        # que vai retornar o dataframe da area metro quadrado

        importar_automatico = st.checkbox(
        # crio uma variavel e nela vou armazenar um valor boleano
        # para o checkbox primeiro preciso infomar o texto e depois o valor

            "Deseja importar os dados automaticamente da Área Metro?",
            value=False # vai iniciar desmarcada
        )

        if importar_automatico:
        # se TRUE, ou seja se o uduario flegar essa caixa

            if dados_area_metro.empty:
        # mas se a base dados estiver vazia

                st.warning("⚠️ Nenhum dado disponível do formulário Área Metro.")
        # vai aparecer essa mensagem

                return pd.DataFrame()
        # além da mensagem vai retornar um data frame vazio para a função que ela foi chamada, no caso a render_form, que é função principal, a função mãe
        # as outras são funções aninhada, ou seja, função filha

            dados_formulario = []
        # crio uma variavel com uma lista vazia

            for _, row in centros_aplicaveis.iterrows(): 
        # _ é uma convensão para indicar que é um valor que não será utilizado
        # para cada indice pode ser e linha na base centro aplicaveis, que é o data frame filtrado
        # o metodo iterrows, é metodo para dataframes que permite iterar sobre cada linha do DataFrame

                centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
        # crio uma variavel armazenando o nome do centro de custo daquela linha

                codigo_cc = row['CÓD CC']
        # crio uma variavel armazenando o codigo do centro de custo daquela linha

                linha_dados = dados_area_metro[
        # ai eu crio uma nova variavel, apartir da base de dados

                    (dados_area_metro['Código CC'] == codigo_cc) &
        # verifico se exite na coluna de código cc o mesmo codigo que estou interando na linha

                    (dados_area_metro['Criticidade_Selecionada'] == "Área Semi Crítica")
        # e verifico também se existe na coluna de criticidade o nome que coloquei
        #para conseguir fazer um filtro e alocar essa linha na variavel criada
                    ]
                if not linha_dados.empty:
        # se a linha não é vazia, ou seja se tem dado

                    quantidade = linha_dados.iloc[0]['Quantidade']
        # acesso uma linha pelo indice posicional .iloc
        # acesso apenas a primeiro linha
        # então primeiro eu chamo o metodo e depois eu informo qual a posiçao que eu quero
        # e por ultimo informo a coluna que é a de qualidade

                else: 
            # agora se é vazio o linha_dados

                    quantidade = 0 
            # a quantidade será zero

                dados_formulario.append({
            # adicioo um dicionário na lista vazia

                    'Competência': competencia,
            #competencia é a competecia escolhida

                    'Ponderação': "Área Semi Crítica",
            # a ponderação é o texto que passei

                    'Centro de Custo': centro_custo,
            # o centro de custo, é o centro de custo que percorri na linha

                    'Código CC': codigo_cc,
            # o codifo é a mesma coisa do centro de custo

                    'Quantidade': quantidade
            # quantidade é quantidade que trouxe do arquivo area_M2 ou zero para os casos que não localizar
                })

            st.success("✅ Dados importados com sucesso.")
        # vai aparecer a mensagem de sucesso

            return pd.DataFrame(dados_formulario).drop(columns=['Código CC'])
        # retorno um o dataframe que foi adicionando as linhas, sem a coluna de Código CC

        else:
        # agora se a variave continua FALSE, ou seja se o usuario não flegar a caixa

        # PRIMEIRO: Carrega dados salvos
            dados_salvos = carregar_dados_salvos(competencia, unidade, nome_formulario)

            # SEGUNDO: Gerenciamento do session_state
            form_key = f"form_data_{nome_formulario}_{competencia}_{unidade}"
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
                            # ✅ CORREÇÃO: Usar a mesma chave do st.text_input
                            field_key = f"nao_critica_{competencia}_{codigo_cc}_{unidade}"
                            quantidade = dados.get('quantidade', 0)
                            
                            if isinstance(quantidade, (int, float)) and quantidade > 0:
                                st.session_state[form_key][field_key] = str(float(quantidade))
                            else:
                                st.session_state[form_key][field_key] = "0"

            dados_formulario = []
        # crio uma variavel com uma lista vazia

            # TERCEIRO: Criar os campos com os valores carregados
            for _, row in centros_aplicaveis.iterrows():
        # para cada linha da base de centro de custo
                centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO']
                codigo_cc = row['CÓD CC']
                
                # Define a chave do campo
                field_key = f"nao_critica_{competencia}_{codigo_cc}_{unidade}"
                
                # ✅ CORREÇÃO: Pega o valor salvo ou usa "0" como padrão
                valor_default = st.session_state[form_key].get(field_key, "0")
        
        # crio uma caixa para receber um input do usuario, com o nome do centro de custo e codigo
                entrada = st.text_input(
                    f"{centro_custo} (Código: {codigo_cc})",
                    value=valor_default,  # ✅ Usa o valor carregado
                    key=field_key  # ✅ Mantém a mesma chave
                )
                
                # ✅ CORREÇÃO: Atualiza o session_state com o valor atual
                st.session_state[form_key][field_key] = entrada
                
        # com o valor da entrada do usuario aplico a fomula
                quantidade = processar_entrada_numero(entrada)
        
        # depois adicono ela a lista vazia, como blocos de dicionário
                dados_formulario.append({
                    'Competência': competencia,
                    'Ponderação': "Área Semi Crítica",
                    'Centro de Custo': centro_custo,
                    'Código CC': codigo_cc,
                    'Quantidade': quantidade
                })
                                    
            return pd.DataFrame(dados_formulario).drop(columns=['Código CC'])

    except FileNotFoundError: #"Erro de Arquivo Não Encontrado", é quando o arquivo que estou tentando ler não existe ou seja não encontrou o caminho do arquivo ou o arquivo não existe
        # aqui eu trato o erro de arquivo não encontrado, que é quando o arquivo que estou tentando ler não existe ou seja não encontrou o caminho do arquivo ou o arquivo não existe
        st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!") #st é o streamlit, que é a biblioteca que estou usando, error é um formato de texto que já vem formatado para aparecer como erro
        return pd.DataFrame() # além de mostrar a mensagem de erro, retorna um dataframe vazio para a função que chamou, no caso a função render_form

    except Exception as e: #Se acontecer qualquer erro (qualquer exceção), capture esse erro e chame ele de "e"
        """
        Exception → "exceção" (nome genérico para erro)
        as e → "como e", ou seja, o erro será armazenado na variável e para você poder examinar ou imprimir
        """
        st.error(f"❌ Erro ao processar o formulário: {str(e)}") # aqui a mesma coisa de cima, a diferença é que estou imprimindo o erro que aconteceu, que é o que está armazenado na variavel e, convertendo para string com str(e) para poder imprimir
        return pd.DataFrame() # e por ultimo retorna um dataframe vazio para a função que chamou, no caso a função render_form
