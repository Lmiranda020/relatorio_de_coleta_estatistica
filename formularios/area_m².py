import streamlit as st #para fazer a interface
import pandas as pd # para manipulação de dados
import re #para trabalhar com regex
from utils.carregar_dados import carregar_dados_salvos

def render_form(competencia): # Função principal que recebe a competência e renderiza todo o formulário, por isso ele vem primeiro, pois ele será aplicado para todo o formulario
    """
    Renderiza o formulário Area Metro com seleção de criticidade
    """
    
    # criar uma caixa de instruções expancivel por isso st.expander e expanded=False para ficar fechada
    # O st.markdown é uma função do streamlit que permite escrever texto formatado usando a sintaxe Markdown. Como é feito no readme.md no git hub
    with st.expander("📋 Instruções - Área Metro (Seleção de Criticidade)", expanded=False): 
        st.markdown("""
        ### Como preencher este formulário:
        
        1. **Digite a área em m²** para cada centro de custo
        2. **Selecione o nível de criticidade** correspondente
        3. As informações serão automaticamente distribuídas para os formulários específicos
        
        | Criticidade           | Exemplos de áreas incluídas                                |
        |------------------------|-------------------------------------------------------------|
        | Área Não Crítica - I   | Consultórios, recepção, áreas administrativas               |
        | Área Semi Crítica      | Enfermarias, salas de observação, medicação, pediatria      |
        | Área Crítica - I       | UTI, centro cirúrgico, emergência, salas de isolamento      |
        
        🧠 **Importante:** Essas informações serão distribuídas automaticamente para os formulários específicos de cada criticidade.
        """)
    
    erro_detectado = False  # crio uma variável que tem o false por enquanto, a ideia é controlar se há erros no preenchimento, ou melhor se existe alguma area que ficou sem a escolha da criticidade apos o usuario informar a area quandrada para algum centro de custo
    
    def processar_entrada_numero(entrada): #crio uma função que vai converter o valor que o usuario colocar
        """
        Processa a entrada do usuário e retorna um número válido
        """
        if not entrada or not entrada.strip(): #aqui eu defino um numero de entrada padrão ou seja 0. Para os casos que não há entrada do valor ou opós tirar os espaços no final e no incio do dado, por isso strip, continuar não existindo dado retornar 0
            return 0
        
        entrada = entrada.strip().replace(",", ".") #aqui primeiro tiro strip da entrada, ou seja se o usuario digitar espaços no inicio ou no final do valor, ele primeiro tira essa espaço e depois aplica o replace trocando virgula por ponto
        
        try: #aqui eu tento aplicar um regex, no valor
            # O 'r' antes da string cria uma **raw string** (string bruta), que diz ao Python para **não interpretar as barras invertidas (\)** como caracteres especiais.
            # Isso é importante porque na linguagem Python:
            #   - '\n' significa nova linha (newline)
            #   - '\t' significa tabulação (tab)
            #   - '\d' NÃO é uma sequência de escape válida no Python puro → daria erro

            # Porém, na **expressão regular (regex)**, usamos muitas sequências como:
            #   - \d → dígito (0-9)
            #   - \s → espaço em branco
            #   - \. → ponto literal

            # Se não colocarmos o 'r', o Python tenta interpretar essas barras **antes mesmo** de passar para o módulo `re`, e isso pode causar erro ou comportamento inesperado. 
            #'^\d+(\.\d+)?$' a ideia é verificar se o que foi digitado é realmente um valor
            '''
            ^ - Início da string
            \d = qualquer dígito (0-9)
            + = uma ou mais vezes
            ( = início do grupo, tudo que estiver dentro do () é considerado como grupo
            \. = ponto literal (escape porque . sozinho significa "qualquer caractere") e com \ é relmente um ponto
            \d+ = um ou mais dígitos após o ponto
            ) = fim do grupo
            ? = o grupo inteiro é opcional (pode ter ou não). Por isso colocamos dentro () pois o usuario pode ou não colocar numero com casas decimais após o ponto ou não, pode ser 15.5 ou 15            $ - Final da string
            $ = siginifica final da string, ou seja, termina com ponto e digitos. Isso garante que 45.abc ou 123. sejá invalido
            '''
            if re.match(r'^\d+(\.\d+)?$', entrada): #se o valor digitado da match com o regex, ele converte o valor para float
                return float(entrada)
            else:
                raise ValueError("Formato de número inválido") #A palavra raise em Python lança (dispara) uma exceção (erro) manualmente
            #ou seja se o valor não passar pela validação, ele vai dar esse erro "Formato de número inválido" ou se não conseguir converter o valor para float
        except (ValueError, TypeError, AttributeError): # aqui ele pega o ValueError acima caso cai lá ou se deu erro de typeError, ou AttributeError
            #ValueError -> acontece quando fazer um conversão incompativel, por exemplo, uma string para float 
            #AttributeError -> acontece quando atribuimos um metodo para um tipo de dado que não possui esse metodos, exemplo, (valor = none) depois atribuimos o metodos strip a ele valor.strip(). Isso vai dar AttributeError, pois estamos atribuindo uma metodo para um tipo de dado que não possui esse metodos aplicavel
            #TypeError -> é quando colocamos o tipo de dado errado a um valor ou variavel. Por exemplo float([1, 2, 3]) ou float({'a': 1}) ou float(None). Não tem como colocar esse valor como float pois são dicionario, listas e none
            st.warning(f"⚠️ Número inválido informado: '{entrada}'. Use apenas números (ex: 15 ou 15,5).") # st.warning é um metodo do streamlit que exibe uma caixa de aviso amarela
            return 0 #então alem de retornar a mesagem ela vai configurar a caixa de entrada com o valor zero
        #a ideia é capturar os erros que pode dar e tratar ele, então alem de monstrar a mensagem, aonde eu chamar essa função, se der erro vai retornar o valor 0 para que continue o processamento do codigo


    def salvar_dados_formulario_especifico(dados, nome_formulario): #aqui eu crio uma função com o nome salvar_dados_formulario_especifico e ele recebera dois parametros (dados, nome_formulario)
        #dados: os dados preenchidos pelo usuário no formulário e nome do fomulario, que é o nome do formulario especifico pelo novel de criticidade
        chave_session = f"dados_{nome_formulario}_{competencia}" # aqui eu crio uma variavel que tera como valor a junção de algumas infomações, ela funcionara com uma chave, basicamente é o nome "dados + nome do formulario + competencia. ALgo como (dados_area_nao_critica_2025/07)
        st.session_state[chave_session] = dados # st.session_state, é o mecanismo do Streamlit para manter variáveis na memória enquanto o app estiver rodando, ou seja ele vai aramazenar os valores na memoria do computador enquanto o app roda para depois eu conseguir pegar essas dados para usar nos outro fomulario, atraves da chave criada.
        '''
        df["coluna"] = valor	            | DataFrame |	                Cria ou modifica uma coluna dentro de uma tabela de dados
        st.session_state["chave"] = dados	| Dicionário do Streamlit |    	Cria uma variável temporária nomeada, fora do DataFrame, que pode ser qualquer tipo de dado (não só tabela)
        '''
    
    try:
        # Carrega a base de centros de custo
        df_centros_custo = pd.read_excel("data/Relatorio Centro de Custo.xlsx") #aqui eu leio o arquivo de centro de custo que será trocado pela API de centro de custo
        
        # Obtém a unidade selecionada do session_state
        unidade_selecionada = st.session_state.get('unidade_selecionada', '') #aqui eu acesso a memoria do streamlit criado no computador e pego (get) o valor da unidade_selecionada. Se essa chave não existir ele atribui o valor ""
        #essa chava é crada no app principal, aqui eu só acesso para pega-la

        # ADICIONAR ESTA LINHA:
        nome_formulario = "Área (m²)"

        if not unidade_selecionada: #aqui eu coloco umm condição caso o uaurio não escolha uma unidade ou se deixar vazia
            st.error("❌ Nenhuma unidade selecionada!") #eu utilizo com o metodo error do streamlit porque ele tem visual próprio, para chamar a atenção que tem alho errado
            return pd.DataFrame() #Interrompe a função atual e retorna um DataFrame vazio. Ou seja, a função  render_form, pois caso o uduario não selecione a unidade o return evita que o restante do código continue sendo executado com dados incorretos. Com base na condição que o usuario não escolhei a unidade
        
        # Você pode usar qualquer um dos três como referência, ou criar uma coluna específica #APAGAR?
        # nome_formulario_referencia = "Área (m²) x Nível de Criticidade (Área Não Crítica - I)" #APAGAR?
        
        # Verifica se existe alguma coluna de área para usar como referência
        # cria uma variavel colunas_area e nela será armazenado uma lista, por isso os []. Sobre a lista:
        # primeiro ele acessa as colunas do arquivo de centro de custo (df_centros_custo.columns)
        # segundo intera sobre cada valor, ou melhor, nome de coluna (for col in df_centros_custo.columns). Esse é col é como se forsse uma variavel temporaria criada, apenas para percorrer a cada elemento
        # terceiro ele vê se as coluna possui  "Área (m²)" e "Criticidade" no nome das colunas 
        # quarto se a condição for verdaeira, ou seja, se o valor possui os nomes especificados, o valor vai ser tornado ao primeiro col
        # e por ultimo o primeiro col vai ser o nome de atende as condições e logo será armazenado como primeiro item da lista, e isso é feito para cada coluna, até chegar na lista completa
        #colunas_area = [col for col in df_centros_custo.columns if "Área (m²)" in col and "Criticidade" in col] #APAGAR TUDO NÃO SENTIDO
        
        #if not colunas_area: #aqui eu coloco uma condição se não encontrar nenhum valor 
        #    st.error("❌ Nenhuma coluna de área encontrada no arquivo Excel!") #vai aparecer essa mensagem
        #    return pd.DataFrame() # e parar o processamento, por isso o return, e retornar um data frame vazio #APAGAR TUDO
        
        # Usa a primeira coluna encontrada como referência
        coluna_referencia = "Área (m²)" #aqui crio uma variavel coluna_referencia com o priemiro valor da lista colunas_area
        
        # Filtra pela unidade e pelo formulário (coluna TRUE)
        # cria um novo dataframe chamado centros_aplicaveis que contem apenas as linhas do dataframe df_centros_custo a partir de uma condição
        centros_aplicaveis = df_centros_custo[
            (df_centros_custo['UNIDADE PLANILHA'] == unidade_selecionada) & # primeiro ele faz um filtro da unidade de acordo com a unidade escolhida
            (df_centros_custo[coluna_referencia] == True) # depois um segundo filtro para na coluna referencia que os valores sejam TRUE, ou seja, os que estão tikados
        ]
        
        if centros_aplicaveis.empty: #essa parte é se caso da erro o filtro, ou seja, não encontre nada. Ou seja, se o data frame centros_aplicaveis está vazio 
            st.warning(f"⚠️ Nenhum centro de custo encontrado para a unidade '{unidade_selecionada}' neste formulário.")
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
                    
                    if not centro_encontrado.empty:
                        codigo_cc = centro_encontrado.iloc[0]['CÓD CC']
                        
                        # Para o campo de área
                        area_key = f"area_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        quantidade = dados.get('quantidade', 0)
                        if quantidade > 0:
                            st.session_state[form_key][area_key] = str(float(quantidade))
                        else:
                            st.session_state[form_key][area_key] = "0"
                        
                        # Para o campo de criticidade (se salvo)
                        criticidade_key = f"criticidade_{codigo_cc}_{competencia}_{unidade_selecionada}"
                        criticidade = dados.get('criticidade', "Selecione...")
                        st.session_state[form_key][criticidade_key] = criticidade

        # Mostra informações no fomulario, com bases nas escolhas e filtros
        st.write(f"**Competência**: {competencia}")
        st.write(f"**Unidade**: {unidade_selecionada}")
        st.write(f"**Centros de Custo encontrados**: {len(centros_aplicaveis)}")
        
        # Dicionários para armazenar dados por criticidade, criei aqui para não deixar dentro do for
        dados_nao_critica = []
        dados_semi_critica = []
        dados_critica = []
        
        # Opções de criticidade, primeiro criei uma lista com as opções
        opcoes_criticidade = [
            "Selecione...",
            "Área Não Crítica - I",
            "Área Semi Crítica", 
            "Área Crítica - I"
        ]

        dados_area_m2 = [] #aqui crio uma variavel com os dados, que são uma lista de valores que antes de preencher está vazia

        # print(f"DEBUG: Tipo de dados_area_m2 inicial: {type(dados_area_m2)}")
        # Para cada centro de custo aplicável, cria campos de input
        # aqui percorro cada indice e linha do dataframe criado centros_aplicaveis
        # o metodo iterrows, é metodo para dataframes que permite iterar sobre cada linha do DataFrame
        for idx, row in centros_aplicaveis.iterrows():
            centro_custo = row['DESCRIÇÃO DE CENTRO DE CUSTO'] # crio uma variavel armazenando o nome do centro de custo daquela linha
            codigo_cc = row['CÓD CC'] # crio uma variavel armazenando o codigo do centro de custo daquela linha
            
            st.write("---") #cria uma linha horizontal na interface
            st.write(f"**{centro_custo}** (Código: {codigo_cc})") #logo abaixo ele monstra um texto com o nome do centro de custo em negrito por isso os **. Depois o codigo numerico dentro do texto Codigo e (), por exemplo, (Codigo: XXXXXX)
            
            # Cria duas colunas: uma para área e outra para criticidade
            col1, col2 = st.columns([1, 1]) #poderia ser tambem st.columns(2). Mas dessa forma permite ajustar a largura de cada coluna, nesse caso 1 1 é 50% e 50%. Mas poderia ser 2, 1 66,67% e 33,33%. Ou 3,1 75% e 25%
            
            with col1: #com a coluna 1
                # entrada_area = st.text_input( # cria um campo de texto para o usuário digitar, e o valor digitado será armazenado na variavel entrada_area
                #     "Área (m²)", # rótulo que aparece acima do campo
                #     value="0", # valor padrão inicial do campo, já aparece preenchido com "0"
                #     placeholder="ex: 40,3, 75,5, 120", # texto cinza que aparece dentro do campo quando vazio, como sugestão
                #     key=f"area_{codigo_cc}_{competencia}_{unidade_selecionada}",  # chave única para identificar o input no Streamlit, usada para armazenar valor no session_state. Não precisar escrever session_state de forma explicita o stramlit entende que deve armazenar apenas por usar o metodo key
                #     # então o input no streamlit permite usar o metodo key que possui como ideia por baixo dos panos de session_state
                #     help="Digite a área em m² (ex: 40, 75,5, 120.0)"  # texto de ajuda que aparece quando o usuário passa o mouse sobre o campo
                # )

                # Pega valores salvos
                area_key = f"area_{codigo_cc}_{competencia}_{unidade_selecionada}"
                criticidade_key = f"criticidade_{codigo_cc}_{competencia}_{unidade_selecionada}"

                valor_area_default = st.session_state[form_key].get(area_key, "0")
                valor_criticidade_default = st.session_state[form_key].get(criticidade_key, "Selecione...")

                entrada_area = st.text_input(
                    "Área (m²)",
                    value=valor_area_default,  # Usa valor salvo
                    placeholder="ex: 40,3, 75,5, 120",
                    key=area_key,
                    help="Digite a área em m² (ex: 40, 75,5, 120.0)"
                )

                # Atualiza session_state
                st.session_state[form_key][area_key] = entrada_area
            
            with col2: #com a coluna 2
                # Encontra o índice da opção salva
                try:
                    index_default = opcoes_criticidade.index(valor_criticidade_default)
                except ValueError:
                    index_default = 0

                criticidade_selecionada = st.selectbox(
                    "Nível de Criticidade",
                    opcoes_criticidade,
                    index=index_default,  # Usa índice da opção salva
                    key=criticidade_key,
                    help="Selecione o nível de criticidade desta área"
                )

                # Atualiza session_state
                st.session_state[form_key][criticidade_key] = criticidade_selecionada

            # Aqui eu aplico a função criada para tratar o valor que o usuário digitou
            quantidade = processar_entrada_numero(entrada_area)


            # Preparo os dados base que serão usados em outros formulários de criticidade.
            # Cria-se um dicionário com as informações essenciais.
            # Por exemplo: Competencia: a compenecia escolhida, Centro de custo: nome do centro de custo da linha, Código: O codigo da linha, Quantidade: O valor que o usuario colocou
            dados_base = {
                'Competência': competencia,
                'Centro de Custo': centro_custo,
                'Código CC': codigo_cc,
                'Quantidade': quantidade
            }


            # Aqui eu adiciono cada linha em um novo DataFrame (na prática, em uma lista que depois vira DataFrame)
            # com os nomes das colunas e os valores que cada campo deve receber.
            # Por isso, alguns campos recebem variáveis e outros textos fixos.
            # Primeiro eu crio um dicionário {}, e adiciono esse dicionário na lista que crie lá em cima, assim eu vou ter uma lista com blocos de dicionário que refere-se a cada linha [{bloco/linha1}, {bloco/linha2...}]
            dados_area_m2.append({
                'Competência': competencia,
                'Centro de Custo': centro_custo,
                'Código CC': codigo_cc,
                'Quantidade': quantidade,
                'Ponderação': "Área (m²)",
                'Criticidade_Selecionada': criticidade_selecionada,  # salva a criticidade escolhida aqui
                'Criticidade': criticidade_selecionada  # Para compatibilidade com carregamento
            })

            if quantidade > 0 and criticidade_selecionada == "Selecione...": #se o usuario colocou o valor mas não selecionou a criticidade, ou seja está com o texto "Selecione"
                st.warning(f"⚠️ Você digitou uma área para o centro de custo '{centro_custo}' (Código {codigo_cc}) mas não selecionou a criticidade.") #vai paracer essa mensagem
                erro_detectado = True #troca o erro_detectado para true
                continue  # continue para pular para a próxima iteração do loop e não executar o restante do código para aquele item. Ou seja vai para o proximo centro de custo
            
            # Se há área informada e criticidade selecionada
            if quantidade > 0 and criticidade_selecionada != "Selecione...": #aqui eu faço ao contrario, se o usuario colocou valor e a criticidade escolhida é diferente do "Selecione", será executado o codigo a baixo
                
                # Dados base para o registro
                dados_criticidade  = { #crio um dicionário, primeiro apenas com os dados bases
                    **dados_base, #se analisar essa variavel, ela lá é um dicionário
                    'Ponderação': criticidade_selecionada  #E aqui crio uma outra chave com a cricicidade escolhida.
                }
                
                # Distribui para o formulário correspondente
                if criticidade_selecionada == "Área Não Crítica - I": #se a a criticidade escolhida for igual essa
                    dados_nao_critica.append(dados_criticidade) #deve adicionar esse dados na lista que até então estava vazia

                elif criticidade_selecionada == "Área Semi Crítica": #mesma logica, mas para outro nivel de criticidade
                    dados_semi_critica.append(dados_criticidade)

                elif criticidade_selecionada == "Área Crítica - I": #mesma logica, mas para outro nivel de criticidade
                    dados_critica.append(dados_criticidade)
                
            if erro_detectado: #se true, ou seja se a pessoa digitou o valor da metragem, mas não escolheu a criticidade
                st.error("❌ Corrija os campos com área preenchida sem criticidade antes de continuar.") #vai aparecer uma mensagem de erro
                return pd.DataFrame() # e rotornar um dataframe vazio
                # RESUMO
                '''
                Quando erro_detectado é True, a mensagem de erro aparece.
                Em seguida, o return faz com que a função pare de executar naquele ponto. Nada depois desse return será executado.
                O valor retornado (um DataFrame vazio) é enviado para quem chamou a função.
                Ou seja retorna para a função render_form(competencia) um dataframe vazio
                '''
        
        # Salva os dados nos formulários específicos
        if dados_nao_critica: #se true ou seja, se existe dado
            df_nao_critica = pd.DataFrame(dados_nao_critica) #ele converter a lista em uma dataframe
            salvar_dados_formulario_especifico(df_nao_critica, "area_nao_critica_i") #depois chama a função salvar_dados_formulario_especifico que é responsavel por salvar os dados na memoria atraves de uma chave, para depois ser utilizado 
        
        if dados_semi_critica: # mesma logica de cima
            df_semi_critica = pd.DataFrame(dados_semi_critica)
            salvar_dados_formulario_especifico(df_semi_critica, "area_semi_critica")
        
        if dados_critica: # mesma logica de cima
            df_critica = pd.DataFrame(dados_critica)
            salvar_dados_formulario_especifico(df_critica, "area_critica_i")

        
        if dados_area_m2: #se is true, ou seja, se há valores
            # print(f"DEBUG: Tipo de dados_area_m2 antes do if: {type(dados_area_m2)}")
            # print(f"DEBUG: Conteúdo de dados_area_m2: {dados_area_m2}")
            df_area_m2 = pd.DataFrame(dados_area_m2) # ele converte para um dataframe 
            # O pandas entende: As chaves dos dicionários viram as colunas da tabela. E os valores viram as linhas correspondentes.
            # Ajusta as colunas para o formato final
            salvar_dados_formulario_especifico(df_area_m2, "area_m2") ## salva o DataFrame no session_state, atraves da função salvar_dados_formulario_especifico

        # Mostra resumo dos dados inseridos
        st.write("---") # Exibe uma linha horizontal (um separador) no app Streamlit
        st.write("**📊 Resumo dos dados inseridos:**") # aparece esse texto com o emoji em negrito por isso o **,ainda dentro do formulario de preenchimento
        
        total_registros = len(dados_nao_critica) + len(dados_semi_critica) + len(dados_critica) #aqui crio uma variavel nomeada como  total_registros e nela será alocado a soma da quantidade de dados que foram inseridos por nivel de criticidade, por exemplo se o usuario escolheu semi critico é 1, depois escolheu critica 1, depois escolheu semi critico agora saõ dois, pois estamos lidando com len (contagem) e assim por diante
        total_area = sum([d['Quantidade'] for d in dados_nao_critica + dados_semi_critica + dados_critica]) #aqui crio outra variavel nomeada como total_area e nela atribuo a soma dos valores inserido pelo isuario. Entretanto o + ele está conctaenando uma lista com a outra, depois com o for d in, ou seja, para cada d, ou seja para cada dicionário,  eu pego o valor da chave 'Quantidade'. O resultando final é uma lista com o valores
        
        col1, col2, col3, col4, col5 = st.columns(5) #aqui eu crio 5 colunas
        with col1:
            st.metric("Total de Registros", total_registros) # o metodo metric exibe um valor numerico ou texto, destacado, geralmente usado para mostrar indicadores-chaves. E utilizo como indicador o valor da função acima que é contagem do len com soma dos três niveis de criticidade
        with col2:
            st.metric("Área Total (m²)", f"{total_area:.1f}") # na coluna 2 criou uma metrica chamada Área Total (m²) e atribuo como valor o total_area, e formato ele apenas com uma casa decimal, o priemiro f é referente ao fstring,  que permite inserir variáveis e fazer formatações diretamente dentro da string
            '''
            Formatação do número:
            : inicia a formatação
            .1 significa uma casa decimal
            f significa float (número decimal)
            '''
        with col3: #aqui crio um idicador também e utilizo como valor o len, ou seja, a contagem de itens que o usuario selecionou com tal criticidade
            st.metric("Não Crítica", len(dados_nao_critica))
        with col4: # mesma logica de cima
            st.metric("Semi Crítica", len(dados_semi_critica))
        with col5: # mesma logica de cima
            st.metric("Crítica", len(dados_critica))
        
        # Mostra detalhes por criticidade
        if total_registros > 0: #aqui ele pega o total de regustro e se for maior que zero ele executa esse codigo
            st.write("**Distribuição por Criticidade:**") # aqui só mostra um texto fixo
            
            if dados_nao_critica: # se true essa variavel, ou seja, se há valor
                st.write(f"🟢 **Área Não Crítica - I**: {len(dados_nao_critica)} registros") # vai escrever esse texto a aparecer a quantidade de registros para esse tipo criticidade
            
            if dados_semi_critica: # mesma logica de cima
                st.write(f"🟡 **Área Semi Crítica**: {len(dados_semi_critica)} registros")
                
            if dados_critica: # mesma logica de cima
                st.write(f"🔴 **Área Crítica - I**: {len(dados_critica)} registros")
        
        # Retorna um DataFrame consolidado para compatibilidade
        # Retorna o DataFrame da área metro quadrado (com ponderação correta)
        if dados_area_m2: # se há valores preenchidos pelo usuario
            df_area_m2_final = pd.DataFrame(dados_area_m2) 
            # print(f"DEBUG: Tipo de df_area_m2_final: {type(df_area_m2_final)}")
            # print(f"DEBUG: Colunas do df_area_m2_final: {df_area_m2_final.columns.tolist()}")
            # Converto novamente a lista de dicionários para DataFrame.
            # Isso é feito pela segunda vez, pois a primeira conversão foi usada apenas para passar o dado
            # a uma função auxiliar (como salvar ou validar), e essa função poderia modificar o DataFrame.
            
            st.session_state[f"dados_area_metro_{competencia}"] = df_area_m2_final.copy()
            # aqui guardo na memoria do computador uma copia do dt, com uma chave para acessa-lo depois
            # a chave é o texto  dados_area_metro_ + (a competencia que o usuario escolheu)
            # Faço uma nova conversão para garantir que estou trabalhando com os dados brutos,
            # sem interferência da função auxiliar chamada anteriormente (ex: colunas extras)

            return df_area_m2_final[["Competência", "Ponderação", "Centro de Custo", "Quantidade"]]
            # depois de guardar ele retorna a base apenas com as colunas passadas
            # a ideia é criar uma copia para caso eu precise dos dados brutos sem o filtro das colunas
        else: 
            # Se não houver dados preenchidos, retorna um DataFrame vazio.
            # No entanto, já com o nome das colunas definidas, o que ajuda a evitar erros posteriores
            # (por exemplo, ao tentar concatenar ou exibir a estrutura esperada).
            return pd.DataFrame(columns=["Competência", "Ponderação", "Centro de Custo", "Quantidade"])
        
    except FileNotFoundError: # essas excessão está ligada ao try a partir da leitura das base
        # esse tipo de erro FileNotFoundError significa que o codigo tentou abrir ou carregar um arquivo mas que não existe no caminho informado
 
        st.error("❌ Arquivo 'Relatorio Centro de Custo.xlsx' não encontrado!")
        # esse st. error um metodo do streamlit que informa um erro em um caixa configurada
        # É comum o usuário esquecer de colocar o arquivo necessário na pasta correta

        return pd.DataFrame()
        # por fim se de esse erro ele retorna um data frame vazio e sai da função
    
    except Exception as e:
        # esse tipo de erro pega qualquer erro generico que der 
        # A variável "e" captura a mensagem detalhada do erro
        # o erro que mostrari no terminal

        st.error(f"❌ Erro ao processar o formulário: {str(e)}")
        # aqui utilizo um metodo de texto do stramelit de erro, que é uma caixa já formatada
        # nela eu mostro o texto fixo "Erro ao processar o formulário" junto com o erro da variavel "e"

        return pd.DataFrame() # e se der esse erro alem de mostrar a mensagem ele vaai retornar um dataframe vazio

# Função auxiliar para recuperar dados salvos de um formulário específico
def obter_dados_formulario_especifico(nome_formulario, competencia):   
    # aqui crio uma função para nomeada como "obter_dados_formulario_especifico" e recebera dois parametros

    chave_session = f"dados_{nome_formulario}_{competencia}"
    # aqui eu crio uma variavel com a palavra dados + nome do formulario + competencia

    return st.session_state.get(chave_session, pd.DataFrame())
    # e retorno da memoria do streamlit esse base que tem a mesma chave criada 
    # se não encontrar a chave deve trazer um valor padrão
    # o valor padrão é um dataframe vazio
    
# Exemplo de como recuperar os dados no formulário específico
def exemplo_uso_formulario_especifico():
    # aqui crio outra função
    """
    Exemplo de como recuperar os dados no formulário específico
    """
    competencia = "2024-01"  # exemplo
    
    # Recupera dados do formulário area_m2
    dados_nao_critica = obter_dados_formulario_especifico("area_nao_critica_i", competencia)
    
    if not dados_nao_critica.empty:
        st.write("Dados vindos do formulário Area Metro:")
        st.dataframe(dados_nao_critica)
    else:
        st.write("Nenhum dado encontrado do formulário Area Metro para Área Não Crítica - I")

