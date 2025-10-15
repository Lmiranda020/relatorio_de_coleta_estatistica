import streamlit as st
import pandas as pd
import os
from datetime import datetime
from api.api_competencia import get_competencias, carregar_tokens_exportacao
from api.api_dados_estatisticas import get_dados_permanentes

def formatar_competencia_payload(ano, mes):
    """
    Formata competência para o payload da API (MM/AAAA)
    """
    return f"{mes:02d}/{ano}" #formata o mês com dois digitos, ou seja, adiciona o zero a esquerda se for necessário

def encontrar_competencia_anterior_valida(competencia_selecionada, unidade_usuario):
    """
    Encontra a última competência anterior válida (FECHADA ou REABERTA)
    Busca recursivamente até encontrar uma competência válida
    """
    try:
        # 1. Buscar dados da API de competências
        df_competencias = get_competencias() #executa a função que está na api de competências, que consome a API e retorna um dataframe com todas as competências da unidade selecionada
        
        if df_competencias.empty: #se o dataframe estiver vazio
            st.error("Não foi possível obter dados da API de competências") #mostrar essa mensagem de erro
            return None #e retorna None, ou seja, nada para onde chamou essa função
        
        # 2. Processar competência selecionada
        ano_selecionado = int(competencia_selecionada.split("/")[1]) # pego a competecia que foi enviada para onde chamou a função
        #para pegar o ano separo a competencia pelo / e pego a segunda parte que é o ano, e converto para inteiro e guardo na variavel 
        
        mes_map = { #crio um dicionario para mapear o nome do mês para o número do mês
            "jan": 1, "fev": 2, "mar": 3, "abr": 4,
            "mai": 5, "jun": 6, "jul": 7, "ago": 8,
            "set": 9, "out": 10, "nov": 11, "dez": 12
        }

        mes_nome = competencia_selecionada.split("/")[0].lower() #pego a primeira parte que é o mês e converto para minusculo

        mes_selecionado = mes_map.get(mes_nome) #pego no dicionario o número do mês correspondente ao nome do mês
        
        if not mes_selecionado: #se não encontrar o mês no dicionario
            st.error(f"Mês '{mes_nome}' não reconhecido") #retorno mensagem de erro
            return None
        
        # 4. LÓGICA CORRIGIDA: Normalizar formato da competenciaDescr para comparação
        def normalizar_competencia_descr(df): #crio outra funçao, dentro dessa propria função
            """
            Normaliza competenciaDescr da API (1/2024) para formato padrão (01/2024), pois o formato da coetencia que traz na API está fora do padrao do payload
            """
            if 'competenciaDescr' in df.columns: #se houver essa colunas no arquivo
                df = df.copy() #faço uma copia do dataframe
                df['competencia_normalizada'] = df['competenciaDescr'].apply(
                    #crio uma novalo coluna que é uma copia da coluna de competenciaDescr, mas aplico uma função para formatar a competenciaDescr
                    lambda x: '/'.join([
                        str(x).split('/')[0].zfill(2),  # Adiciona zero à esquerda no mês
                        str(x).split('/')[1] if len(str(x).split('/')) > 1 else ''
                    ]) if pd.notna(x) and '/' in str(x) else str(x)
                )
            else:
                #agora se não existir a coluna competenciaDescr, faço o seguinte
                # Fallback: criar competencia_normalizada a partir de mes/ano
                df = df.copy() # crio uma copia do dataframe
                df['competencia_normalizada'] = df['mes'].astype(str).str.zfill(2) + '/' + df['ano'].astype(str)
                #crio uma coluna jutando o mes e o ano, e adicionando o zero a esquerda no mês, já existe a coluna mes e ano no arquivo que vem da API
            
            return df #e retorno o dataframe com a nova coluna criada
        
        df_competencias = normalizar_competencia_descr(df_competencias) #executo a função que criei acima, passando o dataframe de competências que veio da API. E passo so o arquivo, pois a cluna é definida na função que chamei 
        #já que a função que executa a api está dentro de um try, se der erro na função, ele já cai no except
        #e atualizo o proprio dataframe de competências com a nova coluna criada

        # 5. NOVA LÓGICA: Buscar competência anterior válida recursivamente
        def buscar_competencia_recursiva(ano_atual, mes_atual): #passo o ano e o mês atual
            """
            Busca recursivamente a primeira competência válida anterior
            """
            # Calcular mês e ano anterior
            if mes_atual == 1: # se o mes atual for janeiro
                mes_anterior = 12 # o anterior é dezembro
                ano_anterior = ano_atual - 1 # e o ano anterior é o ano atual menos 1
            else: # agora se o mes atual não é janeiro, ou seja é qualquer outro mês
                mes_anterior = mes_atual - 1 # o mês anterior é o mês atual menos 1
                ano_anterior = ano_atual # e o ano anterior é o mesmo ano atual
            
            # Formato normalizado para busca (com zero à esquerda)
            competencia_busca = f"{mes_anterior:02d}/{ano_anterior}" #aqui crio a competencia no formato MM/AAAA, para buscar no arquivo que veio da API
            
            st.info(f"Buscando competência: {competencia_busca}") #informo a competencia que está sendo buscada
            
            # Filtrar competências usando a coluna normalizada
            df_ano_mes = df_competencias[ #crio um novo dataframe, filtrando o dataframe de competências, onde a competencia normalizada é igual a competencia que estou buscando
                df_competencias['competencia_normalizada'] == competencia_busca
            ]
            
            if df_ano_mes.empty: # se o novo arquivo estiver vazio, quer dizer que não encontrou a competência que está buscando
                # Se não encontrou nenhuma competência para esse mês/ano
                # Verifica se ainda há anos anteriores para buscar (limite de 1 anos para trás)
                if ano_anterior >= (ano_selecionado - 1): # se o ano anterior for maior ou igual ao ano selecionado menos 
                    st.info(f"Competência {competencia_busca} não encontrada, buscando anterior...")
                    return buscar_competencia_recursiva(ano_anterior, mes_anterior)
                else:
                    st.warning("Não há mais competências anteriores disponíveis")
                    return None
            
            # Verificar status da competência encontrada
            for _, row in df_ano_mes.iterrows(): #para cada linha do arquivo filtrado
                status = str(row['situacao']).upper().strip() #percorrro na coluna de situação, converto para maiusculo e tiro os espaços em branco no final e no começo
                if status in ['FECHADA', 'REABERTA']: #se a situação for fechada ou reaberta
                    st.success(f"Competência válida encontrada: {competencia_busca} (Status: {status})") #mostro essa mensagem de sucesso
                    # Adicionar dados necessários para o payload
                    competencia_dict = row.to_dict() #converto a linha do arquivo em um dicionario
                    competencia_dict['competencia_formatada'] = competencia_busca #adiciono a chave competencia_formatada, que é a competencia que está no formato MM/AAAA
                    return competencia_dict #retorno o dicionario para onde chamou a função
            
            # Se chegou aqui, a competência está ABERTA, buscar a anterior
            st.info(f"Competência {competencia_busca} está ABERTA, buscando anterior...")
            return buscar_competencia_recursiva(ano_anterior, mes_anterior) # que no caso seria a aberta
        
        # Iniciar busca recursiva
        competencia_valida = buscar_competencia_recursiva(ano_selecionado, mes_selecionado)
        
        return competencia_valida
        
    except Exception as e:
        st.error(f"Erro ao buscar competência anterior: {str(e)}")
        st.exception(e)  # Para debug
        return None

def buscar_unidade_id_e_token(unidade_usuario): #crio uma função para buscar o id e o token da unidade do usuário
    """
    Busca o ID da unidade e token a partir do nome da unidade
    """
    try:
        # Carrega dados das unidades (mesmo arquivo usado na API de competências)
        from config.constants import get_token_unidades_exportacao
        df_unidades = carregar_tokens_exportacao
        
        # Busca a unidade que contém o nome do usuário
        unidade_match = df_unidades[ #verifico na coluna nome, se algum contem o nome da unidade do usuário e retorno para a variavel unidade_match
            df_unidades['nome'].str.contains(unidade_usuario, case=False, na=False)
        ]
        
        if not unidade_match.empty: # se não estiver vazio, ou seja, se encontrou a unidade
            ultima_unidade = unidade_match.iloc[-1] # vou trazer a ultima linha 
            return ultima_unidade['id'], ultima_unidade['token'] # e ai retorno o id e o token dessa unidade
        else: # se não encontrar a unidade
            st.error(f"Unidade '{unidade_usuario}' não encontrada no arquivo de configuração") # retorna um erro informando que não encontrou a unidade
            return None, None
            
    except Exception as e: #agora se dar erro, no momento de executar o try
        st.error(f"Erro ao buscar dados da unidade: {str(e)}") # retorna essa mensagem de erro
        return None, None

def filtrar_formularios_permanentes(dados_api, lista_formularios_permanentes):
    """
    Filtra os dados da API para manter apenas formulários permanentes
    VERSÃO OTIMIZADA - foca na coluna 'criterioDeRateioDescr'
    """
    dados_filtrados = {}
    
    try:
        # Verificar estrutura da API
        if not dados_api or not isinstance(dados_api, dict):
            st.warning("Dados da API estão vazios ou em formato incorreto")
            return {}
        
        if 'items' not in dados_api:
            st.error("Chave 'items' não encontrada nos dados da API")
            st.info(f"Chaves disponíveis: {list(dados_api.keys())}")
            return {}
        
        items = dados_api['items']
        
        if not items or not isinstance(items, list):
            st.warning("Lista 'items' está vazia ou em formato incorreto")
            return {}
        
        st.info(f"📊 Total de itens na API: {len(items)}")
        
        
        # Filtrar por cada formulário permanente
        for formulario_permanente in lista_formularios_permanentes:
            st.info(f"🔍 Filtrando: {formulario_permanente}")
            
            itens_filtrados = []
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                # BUSCAR ESPECIFICAMENTE NA COLUNA 'criterioDeRateioDescr'
                criterio_descr = item.get('criterioDeRateioDescr', '')
                criterio_limpo = str(criterio_descr).strip()
                formulario_limpo = formulario_permanente.strip()

                # LÓGICA ESPECÍFICA para formulários de área
                if formulario_limpo == "Área (m²)":
                    # Para "Área (m²)" - busca EXATA, sem "x Nível de Criticidade"
                    if (criterio_limpo.lower() == "área (m²)" and 
                        "criticidade" not in criterio_limpo.lower()):
                        itens_filtrados.append(item)
      
                # Para formulários de área, busca pelo critério geral
                elif "Área (m²) x Nível de Criticidade" in formulario_permanente:
                    if "Área (m²) x Nível de Criticidade" in str(criterio_descr):
                        itens_filtrados.append(item)
                
                else:
                    # Para outros formulários - comparação exata
                    if criterio_limpo.lower() == formulario_limpo.lower():
                        itens_filtrados.append(item)
    
                    # # Para outros formulários, busca específica
                    # if formulario_permanente.lower().strip() in str(criterio_descr).lower().strip():
                    #     itens_filtrados.append(item)
            
            if itens_filtrados:
                dados_filtrados[formulario_permanente] = itens_filtrados
                st.success(f"✅ {formulario_permanente}: {len(itens_filtrados)} itens encontrados")
            else:
                st.warning(f"⚠️ {formulario_permanente}: Nenhum item encontrado")
                dados_filtrados[formulario_permanente] = []
        
        # DEBUG: Mostrar todos os critérios disponíveis na API
        with st.expander("🔎 Debug: Critérios de Rateio disponíveis"):
            criterios_unicos = sorted(set(
                item.get('criterioDeRateioDescr', '') 
                for item in items 
                if item.get('criterioDeRateioDescr')
            ))
            for criterio in criterios_unicos:
                st.write(f"• {criterio}")
        
        return dados_filtrados
        
    except Exception as e:
        st.error(f"Erro ao filtrar formulários permanentes: {str(e)}")
        return {}

def converter_dados_para_dataframe(dados_formulario, nome_formulario, competencia_escolhida):
    """
    Converte dados da API para DataFrame no formato esperado pelo sistema
    VERSÃO OTIMIZADA - baseada na estrutura real da API
    """
    try:
        if not dados_formulario:
            st.warning(f"Dados vazios para o formulário: {nome_formulario}")
            return pd.DataFrame()
        
        # Se já é DataFrame, retorna
        if isinstance(dados_formulario, pd.DataFrame):
            return dados_formulario
        
        # Se é lista de dicts (formato esperado da API)
        if isinstance(dados_formulario, list) and dados_formulario:
            if isinstance(dados_formulario[0], dict):
                df = pd.DataFrame(dados_formulario)
                
                # CRIAR DATAFRAME COM APENAS COLUNAS ESSENCIAIS
                df_final = pd.DataFrame()
                
                # Colunas obrigatórias
                df_final['Código CC'] = df.get('codigoContabil', 'N/A')
                df_final['Quantidade'] = df.get('valor', '0').astype(str)  #.str.replace('.', ',') # manter ponto para evitar confusão com milhares, e não deixo com vasrias virgulas
                df_final['Centro de Custo'] = df.get('centroDeCustoDescr', 'N/A')
                df_final['Ponderação'] = df.get('criterioDeRateioDescr', 'N/A')
                # COMPETÊNCIA: sempre a escolhida pelo usuário
                df_final['Competência'] = competencia_escolhida

                #coloccar o dataframe final com as colunas na ordem correta
                df_final = df_final[['Competência', 'Ponderação', 'Centro de Custo', "Quantidade"]]

                return df_final

            else:
                st.warning(f"Formato de lista não reconhecido para: {nome_formulario}")
                return pd.DataFrame()
        

        # Se é dict simples
        elif isinstance(dados_formulario, dict):
            df = pd.DataFrame([dados_formulario])

            # Mesmo processo para dict único
            df_final = pd.DataFrame()
            df_final['Código CC'] = df.get('codigoContabil', 'N/A')
            df_final['Quantidade'] = df.get('valor', '0').astype(str)
            df_final['Competência'] = competencia_escolhida

            return df
        
        else:
            st.warning(f"Formato de dados não reconhecido para: {nome_formulario}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao converter dados do formulário '{nome_formulario}': {str(e)}")
        return pd.DataFrame()

def converter_dados_para_dataframe_sem_filtro_criticidade(dados_formulario, nome_formulario, competencia_escolhida):
    """
    Versão da conversão SEM filtro por tipo de criticidade - pega todos os dados
    """
    try:
        if not dados_formulario:
            st.warning(f"Dados vazios para o formulário: {nome_formulario}")
            return pd.DataFrame()
        
        # Se já é DataFrame, retorna
        if isinstance(dados_formulario, pd.DataFrame):
            return dados_formulario
        
        # Se é lista de dicts (formato esperado da API)
        if isinstance(dados_formulario, list) and dados_formulario:
            if isinstance(dados_formulario[0], dict):
                df = pd.DataFrame(dados_formulario)
                
                # CRIAR DATAFRAME COM APENAS COLUNAS ESSENCIAIS - SEM FILTRO
                df_final = pd.DataFrame()
                
                # Colunas obrigatórias
                df_final['Código CC'] = df.get('codigoContabil', 'N/A')
                df_final['Quantidade'] = df.get('valor', '0').astype(str)
                df_final['Centro de Custo'] = df.get('centroDeCustoDescr', 'N/A')
                df_final['Ponderação'] = df.get('criterioDeRateioDescr', 'N/A')
                df_final['Competência'] = competencia_escolhida

                # Reordenar colunas
                df_final = df_final[['Competência', 'Ponderação', 'Centro de Custo', "Quantidade"]]

                return df_final
            else:
                st.warning(f"Formato de lista não reconhecido para: {nome_formulario}")
                return pd.DataFrame()
        
        # Se é dict simples
        elif isinstance(dados_formulario, dict):
            df = pd.DataFrame([dados_formulario])
            
            df_final = pd.DataFrame()
            df_final['Código CC'] = df.get('codigoContabil', 'N/A')
            df_final['Quantidade'] = df.get('valor', '0').astype(str)
            df_final['Centro de Custo'] = df.get('centroDeCustoDescr', 'N/A')
            df_final['Ponderação'] = df.get('criterioDeRateioDescr', 'N/A')
            df_final['Competência'] = competencia_escolhida
            
            df_final = df_final[['Competência', 'Ponderação', 'Centro de Custo', "Quantidade"]]
            return df_final
        
        else:
            st.warning(f"Formato de dados não reconhecido para: {nome_formulario}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao converter dados do formulário '{nome_formulario}': {str(e)}")
        return pd.DataFrame()

def salvar_dados_permanentes_individuais(dados_filtrados, competencia_selecionada, unidade, output_dir): #função para salvar os dados permanentes em arquivos individuais
    """
    Salva dados permanentes em arquivos individuais
    """
    arquivos_salvos = [] #crio uma lista vazia para guardar os nomes dos arquivos salvos
    
    try:
        for nome_formulario, dados in dados_filtrados.items(): #para cada nome de formulário e dados no dicionario de dados filtrados
            if not dados: # se os dados estiverem vazios
                st.warning(f"Dados vazios para formulário: {nome_formulario}") #mostra essa mensagem de aviso
                continue #e pula para o próximo formulário

            # LÓGICA CORRIGIDA: Verificar se é formulário de criticidade da API
            if "Área (m²) x Nível de Criticidade" in nome_formulario:
                st.info(f"Processando formulário de criticidade da API: {nome_formulario}")
                
                # Converter dados SEM tentar filtrar por tipo (pega todos os dados)
                df = converter_dados_para_dataframe_sem_filtro_criticidade(dados, nome_formulario, competencia_selecionada)
                
                if not df.empty:
                    # Salvar apenas UM arquivo com nome identificável
                    nome_arquivo = f"Area_Criticidade_API_{competencia_selecionada}.csv".replace("/", "-").replace(" ", "_")
                    caminho_arquivo = os.path.join(output_dir, nome_arquivo)
                    
                    # Salva arquivo CSV único
                    df.to_csv(caminho_arquivo, index=False, encoding="utf-8-sig", sep=";")
                    arquivos_salvos.append(caminho_arquivo)
                    
                    # *** CORREÇÃO PRINCIPAL ***
                    # Inicializar formularios_data se não existir
                    if 'formularios_data' not in st.session_state:
                        st.session_state['formularios_data'] = {}
                    
                    # Lista CORRIGIDA dos três formulários de criticidade
                    formularios_criticidade = [
                        "Área (m²) x Nível de Criticidade (Área Crítica - I)",
                        "Área (m²) x Nível de Criticidade (Área Semi Crítica)", 
                        "Área (m²) x Nível de Criticidade (Área Não Crítica - I)"
                    ]
                    
                    # Marcar todos os três como preenchidos com o mesmo DataFrame
                    for form_criticidade in formularios_criticidade:
                        st.session_state['formularios_data'][form_criticidade] = df.copy()
                    
                    st.success(f"Arquivo único de criticidade salvo: {nome_arquivo} ({len(df)} registros)")
                    st.success(f"✅ Marcados como processados: {len(formularios_criticidade)} formulários de criticidade")
                    
                    # Listar quais foram marcados
                    for form in formularios_criticidade:
                        st.info(f"• {form}")
                
            else:
                    
                # Converte para DataFrame, se há dados, para isso chama a função que criei acima, passo o nome do formulário e os dados
                # CORREÇÃO: Passar a competencia_selecionada como terceiro parâmetro
                df = converter_dados_para_dataframe(dados, nome_formulario, competencia_selecionada)
                
                if df.empty:#agora se o dataframe estiver vazio
                    st.warning(f"DataFrame vazio após conversão para formulário: {nome_formulario}") #mostra essa mensagem de aviso
                    continue #e pula para o próximo formulário
                
                # # Substitui ponto por vírgula na coluna Quantidade se existir
                # if 'Quantidade' in df.columns: # mas se exitir a coluna Quantidade, apos converter os dados para um dataframe
                #     df['Quantidade'] = df['Quantidade'].astype(str).str.replace('.', ',') #substituo o ponto por vírgula, e converto para string
                
                # Nome do arquivo
                nome_arquivo = f"{nome_formulario}_{competencia_selecionada}.csv".replace("/", "-").replace(" ", "_") #crio o nome do arquivo, juntando o nome do formulário com a competência, substituindo a barra por traço e os espaços por underline
                caminho_arquivo = os.path.join(output_dir, nome_arquivo) #crio o caminho do arquivo, juntando o diretório de saída com o nome do arquivo
                
                # Salva arquivo CSV
                df.to_csv(caminho_arquivo, index=False, encoding="utf-8-sig", sep=";") #salvo o arquivo em formato CSV, sem o índice, com codificação utf-8-sig e separador ponto e vírgula
                arquivos_salvos.append(caminho_arquivo) #adiciono o caminho do arquivo na lista de arquivos salvos
                
                # Salva no session_state para consolidação
                if 'formularios_data' not in st.session_state: #se não existir a chave formularios_data no session_state
                    st.session_state['formularios_data'] = {} #crio a chave como um dicionario vazio
                st.session_state['formularios_data'][nome_formulario] = df #adiciono o dataframe na chave formularios_data, com o nome do formulário como chave e o dataframe como valor
                
                st.success(f"Dados permanentes salvos: {nome_arquivo} ({len(df)} registros)") #mostra essa mensagem de sucesso, informando o nome do arquivo e a quantidade de registros
        
        return arquivos_salvos #no final retorno a lista de arquivos salvos, para onde chamou a função
        
    except Exception as e: #caso de algum erro na hora de executar o try
        st.error(f"Erro ao salvar dados permanentes: {str(e)}") #mostra essa mensagem de erro
        return [] # e retonna uma lista vazia para onde chamou a função
    


def processar_dados_permanentes_completo():
    """
    Função principal que executa todo o fluxo dos dados permanentes
    VERSÃO CORRIGIDA com normalização de formatos
    """
    try:
        # Pegar variáveis do session_state
        formularios_permanentes = st.session_state.get('formularios_permanentes_para_API', [])
        formularios_para_add = "Nº de Colaboradores (Médicos + Não Médicos)"
        formularios_permanentes.append(formularios_para_add)
        competencia_selecionada = st.session_state.get('competencia_usuario', '')
        unidade_usuario = st.session_state.get('unidade_usuario', '')
        output_dir = st.session_state.get('output_dir', 'formularios_preenchidos')
        
        if not all([formularios_permanentes, competencia_selecionada, unidade_usuario]): #se alguma dessas variaveis estiver vazia
            st.error("Dados insuficientes para processar dados permanentes") #mostra essa mensagem de erro
            return False #e retorna False, para onde chamou essa função
        
        st.info(f"Processando {len(formularios_permanentes) - 1} formulários permanentes...") #mostra essa mensagem informando a quantidade de formulários permanentes que serão processados
        st.info(f"Competência selecionada: {competencia_selecionada}") #mostra essa mensagem informando a competência selecionada
        
        # 1. Encontrar competência anterior válida (com nova lógica recursiva e normalização)
        with st.spinner("Buscando competência anterior válida..."): #mostra essa mensagem enquanto executa a função que está dentro do with
            competencia_valida = encontrar_competencia_anterior_valida( #aqui é a função que vai executar a api de competências e buscar a competência anterior válida, que são as funções que criei acima
                competencia_selecionada, #passo a competência selecionada
                unidade_usuario #e a unidade do usuário
            )
        
        if not competencia_valida: #se não encontrar a competência válida, ou seja se retornar none
            st.error("Não foi encontrada competência anterior válida") #mostra essa mensagem de erro
            st.info("Verifique se existem competências anteriores com status FECHADA ou REABERTA")#mostra essa mensagem de informação
            return False #e retorna False, para onde chamou essa função
        
        # Mostrar detalhes da competência encontrada
        competencia_formatada = competencia_valida.get('competencia_formatada', 'N/A') # ele buscar na variavel competencia_valida, a chave competencia_formatada, se não encontrar retorna N/A
        status_competencia = competencia_valida.get('situacao', 'N/A') # ele buscar na variavel competencia_valida, a chave situacao, se não encontrar retorna N/A
        st.success(f"Competência válida: {competencia_formatada} (Status: {status_competencia})") #mostra essa mensagem de sucesso, informando a competência válida e o status da competência
        
        # 2. Buscar ID da unidade e token
        unidade_id, token = buscar_unidade_id_e_token(unidade_usuario) #chama a função que criei acima, para buscar o id e o token da unidade do usuário
        #retorna o id e o token da unidade do usuário, e guarda nas variaveis unidade_id e token
        if not unidade_id or not token: #se não encontrar o id ou o token
            st.error("Não foi possível obter dados da unidade") #mostra essa mensagem de erro
            return False #e retorna False, para onde chamou essa função
        
        # ADICIONE ESTA LINHA:
        st.session_state['unidade_id'] = unidade_id
        
        # 3. Preparar payload para API (já no formato correto)
        payload_data = {
            'competencia_formatada': competencia_formatada,  # Já vem normalizada
            'unidade_id': unidade_id
        }
        
        st.info(f"Consultando dados da competência: {competencia_formatada}") #mostra essa mensagem informando a competência que está sendo consultada
        
        # 4. Buscar dados permanentes via API
        with st.spinner("Consultando API de dados permanentes..."): #mostra essa mensagem enquanto executa a função que está dentro do with
            # Adicionar token à competencia_valida
            competencia_valida['token'] = token
            competencia_valida['unidade_id'] = unidade_id
            
            #a competencia_valida é um dicionario, que contém todas as informações da competência válida encontrada, incluindo o token e o id da unidade
            #as outras infomações de competencia_valida são as mesmas que vieram da API de competências, que são necessárias para a API de dados permanentes
            #ele também é um dicionario, que contém todas as informações da competência válida encontrada, incluindo o token e o id da unidade
            dados_api = get_dados_permanentes(competencia_valida, payload_data)
            #aqui eu chamo a função que está na api de dados estatísticos, que consome a API de dados permanentes, passando a competencia_valida e o payload_data
        
        if not dados_api:
            st.error("Não foi possível obter dados da API de dados permanentes")
            return False
        
        st.success("Dados obtidos da API com sucesso")
        
        # Debug: mostra estrutura dos dados recebidos
        with st.expander("Estrutura dos dados recebidos (Debug)"):
            st.write("Chaves principais:", list(dados_api.keys()) if isinstance(dados_api, dict) else "Não é dict")
            st.write("Primeiros dados:", str(dados_api)[:500] + "..." if len(str(dados_api)) > 500 else str(dados_api))
        
        # 5. Filtrar apenas formulários permanentes
        dados_filtrados = filtrar_formularios_permanentes(dados_api, formularios_permanentes)
        
        if not dados_filtrados:
            st.warning("Nenhum formulário permanente encontrado nos dados da API")
            return False
        
        # 6. Salvar arquivos individuais
        arquivos_salvos = salvar_dados_permanentes_individuais(
            dados_filtrados,
            competencia_selecionada,  # Salva com a competência atual, não a anterior
            unidade_usuario,
            output_dir
        )
        
        if arquivos_salvos:
            st.success(f"Processamento concluído! {len(arquivos_salvos)} arquivos salvos")
            with st.expander("Arquivos gerados"):
                for arquivo in arquivos_salvos:
                    st.write(f"📄 {os.path.basename(arquivo)}")

            # === NOVA SEÇÃO: SALVAR HISTÓRICO DO PROCESSAMENTO ===
            if 'historico_processamento_api' not in st.session_state:
                st.session_state['historico_processamento_api'] = []

            # Criar registro do processamento atual
            registro_processamento = {
                'timestamp': datetime.now(),
                'competencia_selecionada': competencia_selecionada,
                'competencia_anterior_utilizada': competencia_formatada,
                'status_competencia': status_competencia,
                'formularios_processados': list(dados_filtrados.keys()),
                'total_arquivos': len(arquivos_salvos),
                'arquivos_gerados': [os.path.basename(arquivo) for arquivo in arquivos_salvos]
            }

            # === SALVAR HISTÓRICO DO PROCESSAMENTO ===
            if 'historico_processamento_api' not in st.session_state:
                st.session_state['historico_processamento_api'] = []

            # Criar registro do processamento atual
            registro_processamento = {
                'timestamp': datetime.now(),
                'competencia_selecionada': competencia_selecionada,
                'competencia_anterior_utilizada': competencia_formatada,
                'status_competencia': status_competencia,
                'formularios_processados': list(dados_filtrados.keys()),
                'total_arquivos': len(arquivos_salvos),
                'arquivos_gerados': [os.path.basename(arquivo) for arquivo in arquivos_salvos]
            }

            # Salvar no histórico (manter apenas os últimos 5 processamentos)
            st.session_state['historico_processamento_api'].append(registro_processamento)
            if len(st.session_state['historico_processamento_api']) > 5:
                st.session_state['historico_processamento_api'] = st.session_state['historico_processamento_api'][-5:]

            return True
        else:
            st.warning("Nenhum arquivo foi gerado")
            return False
            
    except Exception as e:
        st.error(f"Erro no processamento dos dados permanentes: {str(e)}")
        st.exception(e)  # Para debug, mostra o stack trace completo
        return False
    