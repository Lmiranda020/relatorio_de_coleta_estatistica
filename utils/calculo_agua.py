# Buscas as bases necessárias que estão salvas
# Somar os funcionários para chegar no total
# ler a base de multiplicação

# Buscas as bases necessárias que estão salvas
# Consolidar funcionários por centro de custo
# Usar dados consolidados para cálculo de água

import pandas as pd
import os
import calendar
from datetime import datetime
import streamlit as st

def obter_dias_do_mes(competencia):
    """
    Extrai o mês e ano da competência e retorna quantos dias tem o mês
    """
    try:
        # Remove espaços e divide pela barra
        partes = competencia.strip().split('/') #split divide pela caracter passado e retona uma lista no final, exemplo, ["mai", "2025"]

        mes_nome = partes[0].strip() # pego o primeiro indice "mai"
        ano = int(partes[1].strip()) # pego o segundo e converto para inteiro "2025"
        
        # Dicionário para converter nome do mês para número
        meses = {
            # Nomes completos
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
            
            # Abreviações
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4,
            'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
            'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
        
        mes_numero = meses.get(mes_nome.lower()) #converto o nome para minusculo, depois busco no dicionario o nome e retorno o numero que correspode ao mês

        if not mes_numero:
            # Se não encontrou, tenta buscar por correspondência parcial
            mes_lower = mes_nome.lower() #converte para minusculo
            for nome_mes, numero in meses.items(): #para cada nome e numero dentro do meu dicionario
                if mes_lower.startswith(nome_mes[:3]) or nome_mes.startswith(mes_lower): #vejo se o inicio do nome convertido para minusculo começa com as tres primeiras letras do meu mes do dicionario, o que estou percorendo dentro do for
                    # ou se o o nome do meu dicionário começao com o mês_lower
                    mes_numero = numero # se em alguns dos caso dar TRUE, retorna o número que deu esse matchm para a variavel mes_numero
                    break # e paro no primeiro para não continuar com a verificação com os outros meses do meu dicionário
            
            if not mes_numero: # se não encontrar
                raise ValueError(f"Mês não reconhecido: {mes_nome}") # raise serve para gerar uma exceção (erro) de propósito. Não deu erro, porem prefiro colocar que o mês não correspondeu com nada então parar a execução do codigo
        
        # Retorna quantos dias tem o mês
        dias = calendar.monthrange(ano, mes_numero)[1]
        #função monthrange que possui no modulo calendar, precisamos imputar o ano e o mês
        # essa função traz uma tupla com dois valores
        #dia da semana do primeiro dia do mês 0 = segunda-feira, 1 = terça-feira, …, 6 = domingo
        #Número de dias do mês (considerando anos bissextos)
        #como ele retorna uma tupla, passo o indece [1] para pegar apenas a qauntidade de dias

        # Debug: mostra o que foi processado
        st.info(f"Competência processada: {mes_nome}/{ano} = {dias} dias")
        
        return dias #retorna a quantidade de dias daquela compentencia aonde foi chamado a função
    
    except Exception as e: #caso de errem alguma parte
        st.error(f"Erro ao processar competência '{competencia}': {str(e)}") #mostra a mensagem com o erro
        return 30  # e retorna 30 como valor padrão

# def buscar_arquivos_colaboradores(output_dir):
#     """
#     Busca arquivos CSV que contêm informações sobre colaboradores
#     """
#     # Palavras-chave para identificar arquivos de colaboradores
#     palavras_chave = [
#         "pessoal",
#         "enfermagem", 
#         "colaboradores",
#         "terceiros"
#     ]
#     palavra_excluir = "total"

#     arquivos_encontrados = [] #cria um lista para armazenar os itens

    
#     # Lista todos os arquivos CSV na pasta
#     if os.path.exists(output_dir): #se existir arquivos no diretorio
#         for arquivo in os.listdir(output_dir): # para cada arquivo nesse diretorio
#             if arquivo.endswith('.csv'): # verfiicar se finaliza com csv
#                 # Verifica se alguma palavra-chave está no nome do arquivo
#                 nome_lower = arquivo.lower() # coloca o nome do arquivo todo minusculo
#                 # Verifica se contém a palavra a ser excluída
#                 if palavra_excluir in nome_lower:
#                     continue  # Pula este arquivo se contém "criticidade"
#                 for palavra in palavras_chave: # verifico se cada palavra da minha lista de palavras chaves
#                     if palavra in nome_lower:
#                         caminho_completo = os.path.join(output_dir, arquivo)
#                         arquivos_encontrados.append({
#                             'arquivo': arquivo,
#                             'caminho': caminho_completo,
#                             'palavra_chave': palavra
#                         })
#                         break  # para na primeira palavra chave que possui no nome do arquivo. E sai desse loop indo para o proximo arquivo no loop "for arquivo in os.listdir(output_dir)"
    
#     return arquivos_encontrados

# def consolidar_funcionarios_por_centro_custo(arquivos_colaboradores, competencia):
#     """
#     Consolida todos os arquivos de funcionários agrupando por centro de custo
#     Soma as quantidades de todos os arquivos para cada centro de custo
#     """
#     todos_dados = []
    
#     st.info("🔄 Processando arquivos de funcionários...")
    
#     #arquivo colaboradores é uma lista, onde cada item é um dicionário
#     for item in arquivos_colaboradores:
#         try:
#             # Lê o arquivo CSV, e aí eu passo o caminho completo do arquivo
#             df = pd.read_csv(item['caminho'], sep=';', encoding='utf-8-sig')
            
#             # Normaliza os nomes das colunas, removendo espaços
#             df.columns = df.columns.str.strip()
            
#             # Verifica se tem a coluna Quantidade, se não tiver mostra o aviso e pula, ou seja, não continua o restante do codigo com esse arquivo, pula para o proximo arquivo, ou seja, o prox item da linha lista
#             if 'Quantidade' not in df.columns:
#                 st.warning(f"Arquivo {item['arquivo']} não possui coluna 'Quantidade' - ignorando")
#                 continue
            
#             # Converte quantidade para numérico (trata vírgulas como separador decimal)
#             df['Quantidade'] = df['Quantidade'].astype(str).str.replace(',', '.', regex=False)
#             df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
#             '''
#             O pd.to_numeric pode gerar int64 ou float64, dependendo dos valores.
#             errors='coerce' transforma valores inválidos em NaN
#             O fillna(0) troca esses NaN por zero
#             '''
            
#             # Remove registros com quantidade zero, filtrando apenas valores maiores que 0
#             df = df[df['Quantidade'] > 0]
            
#             if df.empty: #se a base final for vazia, exemplo, só tinha valores zarados
#                 st.warning(f"Arquivo {item['arquivo']} não possui registros válidos - ignorando") #mostra o aviso e pula para o prox arquivo, não executa as proximas linhas de codigo com esse arquivo
#                 continue
            
#             # Trata centro de custo
#             if 'Centro de Custo' not in df.columns: # se não contiver a coluna de centro de custo
#                 df['Centro de Custo'] = 'Não Informado' # cria uma com valor padrão "Não Informado"
#             else:
#                 df['Centro de Custo'] = df['Centro de Custo'].fillna('Não Informado') #agora se existe a coluna mas possui valores nulos, ou seja, algumas está em branco, preeche com o valor padrão também "Não Informado" 
            
#             # Adiciona competência se não existir
#             if 'Competência' not in df.columns: # se não existe a coluna de compentencia
#                 df['Competência'] = competencia #cria ela com o valor da competencia escolhida
            
#             # Adiciona informação do arquivo de origem para controle
#             # df['Arquivo_Origem'] = item['arquivo'] # adiciona no dataframe uma coluna "Arquivo_Origem" com o valor "arquivo" que é o nome do arquivo
            
#             # Seleciona apenas as colunas necessárias
#             df_selecionado = df[['Competência', 'Centro de Custo', 'Quantidade']]

#             # df_selecionado = df[['Competencia', 'Centro de Custo', 'Quantidade', 'Arquivo_Origem']] #não precisa da coluna de arquivo_origem
            
#             todos_dados.append(df_selecionado) #adiciona o dataframe na lista
    
            
#             st.success(f"✅ {item['arquivo']}: {len(df_selecionado)} registros, {df_selecionado['Quantidade'].sum()} funcionários") # no final informa uma mensagem de sucesso, informando o nomr do arquivo, quantidade de itens e o total de funcionários
            
#         except Exception as e: # caso de algum erro, pega o erro e mostra na tela para o usuario
#             st.error(f"❌ Erro ao processar {item['arquivo']}: {str(e)}")
#             continue # e continua com outro arquivo

#     #terminou o loop paracada item (arquivo)
#     if not todos_dados: # se não contiver nada na lista
#         st.error("Nenhum arquivo foi processado com sucesso") # monstrar uma mensagem de erro
#         return None # retorna none e o detalhe do processamento
    
#     # Concatena todos os dados de todos os arquivos, ele apenas empilha todos os arquivos um embaixo do outro 
#     df_todos = pd.concat(todos_dados, ignore_index=True)
    
#     # Faz uma única consolidação por Centro de Custo, somando as quantidades de todos os arquivos
#     st.info("🔄 Consolidando dados por Centro de Custo...")
    
#     #agora agrupo o dataframe por centro de custo
#     df_consolidado = df_todos.groupby('Centro de Custo').agg({ #agg define como resumir as outras colunas dentro de cada grupo
#         'Quantidade': 'sum',  # Soma as quantidades de todos os arquivos
#         'Competência': 'first' #pego apenas o primeiro
#         # 'Arquivo_Origem': lambda x: '; '.join(sorted(set(x)))  # junta todos os nomes de arquivos (sem repetição), separados por ; (SET -> cria um conjunto com todos os valore, removendo os duplicados; SORTED -> ordena os valores em ordem alfabetica; JOIN -> junta todos com o delmitador )
#         #o x não é uma célula, e sim toda a coluna Arquivo_Origem daquele CENTRO DE CUSTO  eu está sendo agrupado
#     }).reset_index() # reseta o index
    
#     # Adiciona a ponderação fixa para o arquivo consolidado
#     df_consolidado['Ponderação'] = 'Total Colaboradores'
    
#     # Reordena as colunas no padrão esperado
#     #df_consolidado = df_consolidado[['Competencia', 'Centro de Custo', 'Ponderação', 'Quantidade', 'Arquivo_Origem']]
#     df_consolidado = df_consolidado[['Competência', 'Centro de Custo', 'Ponderação', 'Quantidade']]
    
#     st.success(f"✅ Consolidação concluída: {len(df_consolidado)} centros de custo únicos")
#     st.info(f"📊 Total geral de colaboradores: {df_consolidado['Quantidade'].sum()}")
    
#     return df_consolidado

def salvar_arquivo_consolidado(df_consolidado, output_dir, competencia, unidade):
    """
    Salva o arquivo consolidado de funcionários
    """
    try:
        nome_arquivo = f"total_colaboradores_{competencia}.csv".replace("/", "-").replace(" ", "_") #defino o nome do arquivo, substiruindo alguns caracteres para não dar erro
        caminho_arquivo = os.path.join(output_dir, nome_arquivo) #crio o caminho do arquivo, junto com o nome definido
        
        df_consolidado.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig', sep=';') #converto o arquivo para csv, passando o diretorio já com o nome do arquivo
        #por padrão o pandas salva o index, por isso defino como False, para não salvar essa coluna
        '''
        O encoding define como os caracteres são codificados no arquivo.
        utf-8 → padrão moderno que suporta letras acentuadas (á, é, ã, ç…)
        utf-8-sig → é UTF-8 com uma marca especial (BOM) no início do arquivo.
        Isso ajuda programas como Excel a reconhecer corretamente os a
        '''
        
        st.success(f"📁 Arquivo consolidado salvo: {nome_arquivo}") # mostra a mensagem de sucesso
        return caminho_arquivo # e torno o caminho do arquivo
    
    except Exception as e: # se der qualquer erro, por exemplo no momento de salvar
        st.error(f"Erro ao salvar arquivo consolidado: {str(e)}") #monstra a mensagem de erro
        return None # e retorna none para onde foi chamada a função

def carregar_base_consumo_agua(caminho_base):
    """
    Carrega a base Excel com os dados de consumo de água por unidade
    """
    try:
        # Carrega o arquivo Excel
        df_base = pd.read_excel(caminho_base)
        
        # Normaliza os nomes das colunas (remove espaços extras, etc.)
        df_base.columns = df_base.columns.str.strip()
        return df_base
        
    
    except Exception as e:
        st.error(f"Erro ao carregar base de consumo de água: {str(e)}")
        return None

def obter_dados_unidade_com_dias(df_base, unidade, dias_mes):
    """
    Busca os dados da unidade específica na base e multiplica os valores pelos dias do mês
    """
    if df_base is None: # se não tiver base da algum erro
        return None #retorna none para onde foi chamado a função
    
    # Busca a linha da unidade (case insensitive)
    base_filtrada = df_base['UNIDADE'].str.contains(unidade, case=False, na=False) # case=False Faz a busca sem diferenciar maiúsculas e minúsculas. na=False Diz como tratar valores nulos (NaN/None) que é False
    dados_unidade = df_base[base_filtrada].copy()  # .copy() para evitar erros
    
    if dados_unidade.empty: # se retornar uma base vazia, ou seja quer dizer que a unidade não foi encontrada
        st.warning(f"Unidade '{unidade}' não encontrada na base de consumo de água") #retorna uma mensagem de aviso
        return None # e retorna none para onde foi chamado a função
    
    # Multiplica a coluna VALOR pela quantidade de dias
    dados_unidade['VALOR_ORIGINAL'] = dados_unidade['VALOR']  # crio aqui uma coluna nomeada como "valor original" e guardo o valor principal nela para não perde esse dado
    dados_unidade['VALOR'] = dados_unidade['VALOR'] * dias_mes #multiplico o valor pela quantidade de dias
    dados_unidade['DIAS_APLICADOS'] = dias_mes  # Adiciona coluna informativa de quantidade de dias, caso precise
    
    # Retorna como lista de dicionários
    return dados_unidade

    # Usando records → cada linha vira um dicionário
    # Saída:
    # [
    #   {'UNIDADE': 'Hospital A', 'VALOR': 100, 'DIAS_APLICADOS': 30},
    #   {'UNIDADE': 'Hospital B', 'VALOR': 200, 'DIAS_APLICADOS': 30}
    # ]
    # formato prático para trabalhar como JSON ou lista de objetos.

    # Sem records (padrão) → gera um dicionário de listas, organizado por coluna
    # Saída:
    # {
    #   'UNIDADE': {0: 'Hospital A', 1: 'Hospital B'},
    #   'VALOR': {0: 100, 1: 200},
    #   'DIAS_APLICADOS': {0: 30, 1: 30}
    # }
    # formato mais útil se você quiser acessar dados por coluna.

def apenas_dias_uteis(competencia, dias_totais):
    """
    Calcula apenas os dias úteis (excluindo sábados e domingos) de um mês específico
    """
    try:
        # Remove espaços e divide pela barra
        partes = competencia.strip().split('/') #tira os espaços e quebra atraves do caracter, trazendo uma tupla, exemplo, "mai/2025" -> ("mai", 2025)
        mes_nome = partes[0].strip() #pego apenas o indice 0, ou seja, o primeiro que é o mês
        ano = int(partes[1].strip()) #pego o segundo dado, que é o ano e converte para inteiro
        
        # Dicionário para converter nome do mês para número
        meses = {
            # Nomes completos
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
            
            # Abreviações
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4,
            'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
            'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
        
        mes_numero = meses.get(mes_nome.lower()) #converto o nome para minusculo, depois busco no dicionario o nome e retorno o numero que correspode ao mês
        if not mes_numero:
            # Se não encontrou, tenta buscar por correspondência parcial
            mes_lower = mes_nome.lower()  #converte para minusculo
            for nome_mes, numero in meses.items(): #para cada nome e numero dentro do meu dicionario
                if mes_lower.startswith(nome_mes[:3]) or nome_mes.startswith(mes_lower): #vejo se o inicio do nome convertido para minusculo começa com as tres primeiras letras do meu mes do dicionario, o que estou percorendo dentro do for
                    # ou se o o nome do meu dicionário começao com o mês_lower
                    mes_numero = numero # se em alguns dos caso dar TRUE, retorna o número que deu esse matchm para a variavel mes_numero
                    break # e paro no primeiro para não continuar com a verificação com os outros meses do meu dicionário
            
            if not mes_numero: # se não encontrar
                raise ValueError(f"Mês não reconhecido: {mes_nome}") # raise serve para gerar uma exceção (erro) de propósito. Não deu erro, porem prefiro colocar que o mês não correspondeu com nada então parar a execução do codigo
        
        # Conta os dias úteis do mês
        dias_uteis = 0 #defino essa variavel como 0
        

        # Percorre todos os dias do mês, dias totais já vem da outra função
        for dia in range(1, dias_totais + 1): # come do 1 ecolocolo o total mais um, poruq e no range ele pare no anterior ao ultimo, então por isso somo mais um
            data = datetime(ano, mes_numero, dia) # aqui é o ano, o mes e o dia, que vem dor for então o primeiro é o dia 1. e no final retorna um data time "2025-09-01 00:00:00"
            """
            datetime não é só um número, ele sabe o calendário oficial de cada ano/mês
            ou seja, mesmo que você só veja "2025-02-01 00:00:00", o objeto datetime já tem a informação completa de qual dia da semana aquilo é. se é seg, ter, qua, qui, sex...
            """
            # weekday() retorna: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
            # Então dias úteis são de 0 a 4 (Segunda a Sexta)
            if data.weekday() < 5:  # 0, 1, 2, 3, 4 = Segunda a Sexta (aqui a egnte pasa a data e a função weekday nos traz o valor que corresponde o dia da semana )
                dias_uteis += 1 # e soma a variavel se o valor é menor que 5 ou seja sabado, 1 na varaivel, para saber quantos dias uteis tem
        
        # Debug: mostra o que foi processado
        st.info(f"Dias úteis calculados para {mes_nome}/{ano}: {dias_uteis} dias úteis (de {dias_totais} dias totais)") #mensagem informado que naquela competencia possui x dias uteis de um total de dias
        
        return dias_uteis # retorna a quantidade de dias uteis
    
    except Exception as e: # caso se algum erro captura esse erro
        st.error(f"Erro ao calcular dias úteis para '{competencia}': {str(e)}") # e mostra uma mansagem de erro com o erro capturado
        return dias_totais  # Retorna o total como fallback


# def buscar_arquivos_cme(output_dir):
#     """
#     Placeholder para carregar outras bases necessárias no futuro
#     """
    
#     palavra_chave_cme = "cme"

#     # Lista todos os arquivos CSV na pasta
#     if os.path.exists(output_dir):
#         for arquivo in os.listdir(output_dir):
#             if arquivo.endswith('.csv'):
#                 # Verifica se alguma palavra-chave está no nome do arquivo
#                 nome_lower = arquivo.lower()
#                 if palavra_chave_cme in nome_lower:
#                     caminho_completo = os.path.join(output_dir, arquivo)
#                     # Lê o CSV com Pandas e retorna o DataFrame diretamente
#                     base_cme = pd.read_csv(caminho_completo, sep=";", encoding='utf-8-sig')
#                     if "Competencia" in base_cme.columns:
#                         base_cme = base_cme.rename(columns={"Competencia": "Competência"})
#                     return base_cme  # retorna só o primeiro encontrado

#     return None  # caso não encontre nenhum


# def buscar_arquivos_producao(output_dir):
#     """
#     Placeholder para carregar outras bases necessárias no futuro
#     """   
#     palavras_chave_producao = 'produção'

#     # Lista todos os arquivos CSV na pasta
#     if os.path.exists(output_dir):
#         for arquivo in os.listdir(output_dir):
#             if arquivo.endswith('.csv'):
#                 # Verifica se alguma palavra-chave está no nome do arquivo
#                 nome_lower = arquivo.lower()
#                 if palavras_chave_producao in nome_lower:
#                     caminho_completo = os.path.join(output_dir, arquivo)
#                     # Lê o CSV com Pandas e retorna o DataFrame diretamente
#                     base_producao = pd.read_csv(caminho_completo, sep=";", encoding='utf-8-sig')
#                     base_producao["Ponderação"] = base_producao["Ponderação"] = "Produção"
#                     if "Competencia" in base_producao.columns:
#                         base_producao = base_producao.rename(columns={"Competencia": "Competência"})
#                     return base_producao  # retorna só o primeiro encontrado

#     return None  # caso não encontre nenhum

# def buscar_arquivos_area(output_dir):
#     """
#     Placeholder para carregar outras bases necessárias no futuro
#     """
#     # Lista todos os arquivos CSV na pasta

#     palavra_excluir = "criticidade"
#     palavra_chave_area = "área"

#     if os.path.exists(output_dir):
#         for arquivo in os.listdir(output_dir):
#             if arquivo.endswith('.csv'):
#                 # Verifica se alguma palavra-chave está no nome do arquivo
#                 nome_lower = arquivo.lower()

#                 # Verifica se contém a palavra a ser excluída
#                 if palavra_excluir in nome_lower:
#                     continue  # Pula este arquivo se contém "criticidade"

#                 if palavra_chave_area in nome_lower:
#                     caminho_completo = os.path.join(output_dir, arquivo)
#                     # Lê o CSV com Pandas e retorna o DataFrame diretamente
#                     base_area = pd.read_csv(caminho_completo, sep=";", encoding='utf-8-sig')
#                     if "Competencia" in base_area.columns:
#                         base_area = base_area.rename(columns={"Competencia": "Competência"})
#                     return base_area  # retorna só o primeiro encontrado

#     return None  # caso não encontre nenhum


def multiplicacao_das_bases(base_a_ser_multiplicada, base_com_os_valores_p_multiplicar):
    """
    Função genérica que:
    1. Pega a primeira ponderação encontrada na base_a_ser_multiplicada
    2. Busca o valor correspondente na base_com_os_valores_p_multiplicar
    3. Multiplica todas as quantidades da base_a_ser_multiplicada por esse valor
    """
    
    # 1. Pega a primeira ponderação da base a ser multiplicada
    if base_a_ser_multiplicada.empty: #se a base está vazia
        st.error("❌ Base a ser multiplicada está vazia!")
        return base_a_ser_multiplicada # retorna a propria base como ela está
    
    primeira_ponderacao = base_a_ser_multiplicada["Ponderação"].iloc[0] #pela a primeira ponderação
    
    # 2. Busca o valor correspondente na base com valores para multiplicar
    filtro_valor = base_com_os_valores_p_multiplicar["PONDERAÇÃO FORMS"] == primeira_ponderacao #retorna o data frame com essa linha filtrada
    valores_encontrados = base_com_os_valores_p_multiplicar[filtro_valor]["VALOR"] #pega a linha localizada e o valor que possui na coluna "VALOR", POREM AQUI TRAZ UMA SERIE POR ISSO A ABAIXO PRECISA DSEMBRULHAR COM [0]
    
    if valores_encontrados.empty: #Se não encontrou valor retorna 
        st.warning(f"Ponderação '{primeira_ponderacao}' não encontrada na base de valores!")
        return base_a_ser_multiplicada # retorna a propria base como ela está
    
    valor_p_multiplicar = valores_encontrados.iloc[0] #pega o primeiro valor

    # Verificação e conversão
    if base_a_ser_multiplicada["Quantidade"].dtype == object:
        # Se for string, remove pontos (separador de milhares) e troca vírgula por ponto
        base_a_ser_multiplicada["Quantidade"] = (
            base_a_ser_multiplicada["Quantidade"]
            .str.replace('.', '', regex=False)      # Remove pontos (milhares)
            .str.replace(',', '.', regex=False)     # Troca vírgula por ponto (decimal)
            .astype(float)
        )
    else:
        # Se já for numérico, apenas garante que está em float
        base_a_ser_multiplicada["Quantidade"] = base_a_ser_multiplicada["Quantidade"].astype(float)


    base_a_ser_multiplicada["Quantidade"] = (base_a_ser_multiplicada["Quantidade"] * valor_p_multiplicar).round(2)
    
    return base_a_ser_multiplicada

def consolidar_todos_arquivos_agua(df_consolidado_colaboradores, arquivo_cme_multiplicado, arquivo_producao_multiplicado, arquivo_area_multiplicado):
    """
    Consolida todos os arquivos (colaboradores, CME, produção e área) em um único arquivo final de água
    Agrupa por centro de custo e soma as quantidades
    """
    todos_dados_agua = []
    
    # 1. Adiciona dados de colaboradores (já consolidados)
    if df_consolidado_colaboradores is not None and not df_consolidado_colaboradores.empty: #se o arquivo não é none e nem esta vazio
        df_colaboradores_temp = df_consolidado_colaboradores.copy() #crio uma copia
        todos_dados_agua.append(df_colaboradores_temp) #adiciono ele na lista
        st.info(f"✅ Arquivo colaboradores localizado")
    
    # 2. Adiciona dados de CME (se existir)
    if arquivo_cme_multiplicado is not None and not arquivo_cme_multiplicado.empty:
        df_cme_temp = arquivo_cme_multiplicado.copy()
        todos_dados_agua.append(df_cme_temp)
        st.info(f"✅ Arquivo cme localizado")
    
    # 3. Adiciona dados de produção (se existir)
    if arquivo_producao_multiplicado is not None and not arquivo_producao_multiplicado.empty:
        df_producao_temp = arquivo_producao_multiplicado.copy()
        todos_dados_agua.append(df_producao_temp)
        st.info(f"✅ Arquivo produção localizado")
    
    # 4. Adiciona dados de área (se existir)
    if arquivo_area_multiplicado is not None and not arquivo_area_multiplicado.empty:
        df_area_temp = arquivo_area_multiplicado.copy()
        todos_dados_agua.append(df_area_temp)
        st.info(f"✅ Arquivo área localizado")
    
    # 5. Verifica se tem pelo menos um arquivo para processar
    if not todos_dados_agua:
        st.error("❌ Nenhum arquivo válido para consolidar")
        return None
    
    # 6. Concatena todos os dados (empilha um embaixo do outro)
    st.info("🔄 Consolidando todos os dados por Centro de Custo...")
    df_todos_agua = pd.concat(todos_dados_agua, ignore_index=True)
    

    # 7. PADRONIZAÇÃO DOS TIPOS DE DADOS
    def limpar_e_converter_quantidade(valor):
        """
        Converte valores para float, tratando diferentes formatos
        """
        try:
            # Se a instância valor já é inteiro ou float e não é vazio
            if isinstance(valor, (int, float)) and not pd.isna(valor):
                return float(valor)
            
            # Se a instância valor é string
            if isinstance(valor, str):
                # Remove espaços e caracteres comuns
                valor_limpo = valor.strip().replace(' ', '').replace('\t', '')
                
                # Conta quantos pontos e vírgulas existem
                qtd_pontos = valor_limpo.count('.')
                qtd_virgulas = valor_limpo.count(',')
                
                # Caso 1: Apenas vírgula (formato BR: 1500,25)
                if qtd_virgulas > 0 and qtd_pontos == 0:
                    valor_limpo = valor_limpo.replace(',', '.')
                
                # Caso 2: Ponto E vírgula (formato BR: 1.500,25)
                elif qtd_virgulas > 0 and qtd_pontos > 0:
                    valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
                
                # Caso 3: Múltiplos pontos SEM vírgula (formato incorreto: 2.298.44)
                # Assumimos que o último ponto é o decimal
                elif qtd_pontos > 1:
                    partes = valor_limpo.rsplit('.', 1)  # Divide pelo último ponto
                    valor_limpo = partes[0].replace('.', '') + '.' + partes[1]
                    # "2.298.44" -> ["2.298", "44"] -> "2298.44"
                
                # Remove outros caracteres não numéricos (exceto ponto e sinal negativo)
                import re
                valor_limpo = re.sub(r'[^\d\.-]', '', valor_limpo)
                
                if valor_limpo == '' or valor_limpo == '-':
                    return 0.0
                
                return float(valor_limpo)
                
            # Se não for string, int ou float, retorna 0
            return 0.0
            
        except Exception as e:
            # Log do erro para debug
            print(f"Erro ao converter '{valor}': {e}")
            return 0.0
            
            # Se é NaN ou None
            if pd.isna(valor) or valor is None:
                return 0.0
                
            # Caso não consiga converter
            return 0.0
            
        except (ValueError, TypeError):
            return 0.0
    
    try:
        # Aplica a função de limpeza e conversão
        valores_originais = df_todos_agua['Quantidade'].copy() #crio uma copia da coluna
        df_todos_agua['Quantidade'] = df_todos_agua['Quantidade'].apply(limpar_e_converter_quantidade) #aplico na coluna a função de conversão
        
        # Mostra estatísticas da conversão
        total_registros = len(df_todos_agua) #quantidade de itens 
        zeros_apos_conversao = (df_todos_agua['Quantidade'] == 0).sum() #soma quantos zeros possui
        valores_validos = total_registros - zeros_apos_conversao #quantidade de lançamento onde o final não é 0
        
        st.info(f"✅ Conversão realizada:")
        st.info(f"   • Total de registros: {total_registros}")
        st.info(f"   • Valores convertidos com sucesso: {valores_validos}")
        st.info(f"   • Valores que viraram 0: {zeros_apos_conversao}")
        
        # Debug: mostra alguns exemplos de conversão se houver problemas
        if zeros_apos_conversao > 0:
            st.warning("⚠️ Alguns valores foram convertidos para 0. Exemplos:")
            mask_zeros = df_todos_agua['Quantidade'] == 0
            exemplos = valores_originais[mask_zeros].head(5)
            for i, exemplo in enumerate(exemplos):
                st.write(f"   • Valor original: '{exemplo}' → Convertido para: 0")
        
    except Exception as e:
        st.error(f"❌ Erro na padronização dos dados: {e}")
        return None
    
    # 8. Verifica se as colunas necessárias existem
    colunas_necessarias = ['Centro de Custo', 'Quantidade', 'Competência']
    colunas_faltando = [col for col in colunas_necessarias if col not in df_todos_agua.columns]
    
    if colunas_faltando:
        st.error(f"❌ Colunas faltando no DataFrame: {colunas_faltando}")
        st.write("Colunas disponíveis:", list(df_todos_agua.columns))
        return None
    
    # 9. Faz a consolidação final por Centro de Custo, somando as quantidades
    try:
        df_agua_final = df_todos_agua.groupby('Centro de Custo').agg({
            'Quantidade': 'sum',  # Soma as quantidades de todos os tipos de arquivo
            'Competência': 'first'  # Pega apenas o primeiro valor da competência
        }).reset_index()
        
        st.info(f"✅ Agrupamento realizado com sucesso")
        
    except Exception as e:
        st.error(f"❌ Erro no agrupamento: {e}")
        # Mostra informações de debug
        st.write("Tipos de dados antes do agrupamento:")
        st.write(df_todos_agua.dtypes)
        return None
    
    # 10. Adiciona a ponderação fixa para água
    df_agua_final['Ponderação'] = 'Consumo de Água (Litro)'
    
    # 11. Reordena as colunas no padrão esperado
    df_agua_final = df_agua_final[['Competência', 'Centro de Custo', 'Ponderação', 'Quantidade']]
    
    # 12. Informações do resultado final
    st.success(f"✅ Consolidação final concluída: {len(df_agua_final)} centros de custo únicos")
    st.info(f"📊 Total geral de consumo de água: {df_agua_final['Quantidade'].sum():.2f} litros")
    
    df_agua_final['Quantidade'] = df_agua_final['Quantidade'].round(2)

    return df_agua_final

def salvar_arquivo_agua_final(df_agua_final, output_dir, competencia, unidade):
    """
    Salva o arquivo final consolidado de água
    """
    try:
    #     # LISTA DE UNIDADES QUE DEVEM TER CENTROS DE CUSTO EXCLUÍDOS
    #     UNIDADES_COM_EXCLUSAO = [
    #         "HOSPITAL GERAL DE ITAPEVI",
    #         "UPA SAPOPEMBA",
    #         "UPA JARDIM CASQUEIRO",
    #         # Adicione outras unidades conforme necessário
    #     ]
        
        # CENTROS DE CUSTO A SEREM EXCLUÍDOS (somente para unidades da lista)
        CENTROS_CUSTO_EXCLUIR = [
            "SESMT",
            "MANUTENCAO GERAL",
            "centro_custo_3",
            # Adicione os centros de custo específicos aqui
        ]
        
        # PASSO 0: APLICAR FILTRO DE CENTROS DE CUSTO (se aplicável)
        # if unidade in UNIDADES_COM_EXCLUSAO:
        tamanho_original = len(df_agua_final)
            
        # Remove registros com centros de custo da lista de exclusão
        df_agua_final = df_agua_final[
            ~df_agua_final['Centro de Custo'].isin(CENTROS_CUSTO_EXCLUIR)
        ].copy()
        
        registros_excluidos = tamanho_original - len(df_agua_final)
        
        if registros_excluidos > 0:
            st.info(f"🔧 Filtro aplicado: {registros_excluidos} registro(s) de centro(s) de custo excluído(s) para {unidade}")
        
        # PASSO 1: Criar cópia para água quente ANTES de qualquer formatação
        if unidade == "HOSPITAL GERAL DE ITAPEVI":
            # Ajustar a sequência de colunas
            df_agua_final = df_agua_final[['Competência', 'Ponderação', 'Centro de Custo', 'Quantidade']]

            # Cria cópia com valores numéricos (ainda não formatados)
            df_agua_quente_final = df_agua_final.copy()
            df_agua_quente_final['Ponderação'] = 'Consumo de água quente (litro)'
            
            # Salva arquivo de água quente com formatação brasileira
            df_agua_quente_salvar = df_agua_quente_final.copy()
            df_agua_quente_salvar['Quantidade'] = df_agua_quente_salvar['Quantidade'].apply(
                lambda x: f"{float(x):.2f}".replace(".", ",") if pd.notna(x) else "0,00"
            )
            
            nome_arquivo_quente = f"consumo_agua_quente_{competencia}.csv".replace("/", "-").replace(" ", "_")
            caminho_arquivo_quente = os.path.join(output_dir, nome_arquivo_quente)
            df_agua_quente_salvar.to_csv(caminho_arquivo_quente, index=False, encoding='utf-8-sig', sep=';')
            
            # Salva no session_state com valores NUMÉRICOS (não formatados)
            st.session_state['df_agua_quente_final'] = df_agua_quente_final
            st.success(f"📁 Arquivo de água quente salvo: {nome_arquivo_quente}")
        
        
        # PASSO 2: Salvar arquivo de água normal
        df_para_salvar = df_agua_final.copy()
        
        # Converte para formato brasileiro só na hora de salvar
        df_para_salvar['Quantidade'] = df_para_salvar['Quantidade'].apply(
            lambda x: f"{float(x):.2f}".replace(".", ",") if pd.notna(x) else "0,00"
        )
        
        nome_arquivo = f"consumo_agua_{competencia}.csv".replace("/", "-").replace(" ", "_")
        caminho_arquivo = os.path.join(output_dir, nome_arquivo)
        
        st.session_state['resultado_calculo_agua'] = df_agua_final.copy()
        
        df_para_salvar.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig', sep=';')
        
        st.success(f"📁 Arquivo final de água salvo: {nome_arquivo}")
        return caminho_arquivo
    
    except Exception as e:
        st.error(f"Erro ao salvar arquivo final de água: {str(e)}")
        return None


# def realizar_calculo_agua_consolidado(output_dir, competencia, unidade, caminho_base_agua):
#     """
#     Função principal que realiza o cálculo de consumo de água com dados consolidados
#     """
    
#     # Inicializa o resultado
#     resultado = {
#         'sucesso': False,
#         'erros': [],
#         'dados_calculo': {},
#         'dataframe': pd.DataFrame()
#     }
    

#     try:
#         st.info("🔍 Buscando arquivos de colaboradores...") #mostra a mensagem de buscanso as bases
        
#         # 1. Buscar arquivos de colaboradores
#         arquivos_colaboradores = buscar_arquivos_colaboradores(output_dir) #bisca as bases
#         #arquivos colaboradoes me traz uma lista com dicionários de cada arquivo que ele encontrou
        
#         #s não encontrou nada, dá um erro e retorna um dataframe vazio para onde a função foi chamada
#         if not arquivos_colaboradores:
#             resultado['erros'].append("Nenhum arquivo de colaboradores encontrado")
#             st.error("❌ Nenhum arquivo de colaboradores encontrado")
#             return resultado
#             # return pd.DataFrame()   # dataframe vazio
        
#         #mas se retornou algo, ou seja, não cai no if not. Mostra a mensagem de sucesso
#         st.success(f"Encontrados {len(arquivos_colaboradores)} arquivos de colaboradores")
        
#         # 2. Consolidar funcionários por centro de custo
#         st.info("🔄 Consolidando funcionários por centro de custo...") #mostra a mensagem que está iniciado a cololidação dos arquivos de total de funcionários
#         df_consolidado = consolidar_funcionarios_por_centro_custo(arquivos_colaboradores, competencia)
        
#         if df_consolidado is None or df_consolidado.empty:
#             resultado['erros'].append("Falha na consolidação dos dados de funcionários")
#             st.error("❌ Falha na consolidação dos dados de funcionários")
#             return resultado
#             # return pd.DataFrame()   # dataframe vazio
        
#         total_colaboradores = df_consolidado['Quantidade'].sum() #soma o total de colaboradores
     
#         # 3. Salvar arquivo consolidado
#         arquivo_consolidado = salvar_arquivo_consolidado(df_consolidado, output_dir, competencia, unidade)
#         #ele retorna o caminho do arquivo, que é o diretorio mais o nome do arquivo, caso de algum erro no momento de salvar ele retorna none
        
#         if arquivo_consolidado is None: # se for none
#             resultado['erros'].append("Falha ao salvar arquivo consolidado")
#             st.error("❌ Falha ao salvar arquivo consolidado") #monstra  mensagem de erro e retorna um dataframe vazio para onde a função foi chamanda
#             return resultado
#             # return pd.DataFrame()   # dataframe vazio
        
#         # 4. Obter dias do mês
#         dias_mes = obter_dias_do_mes(competencia) # função para saber quantidade de dias que possui a compentencia escolhida
#         #retorna a quantidade de dias, que possui para a competencia escolhida

#         # 5. Carregar base de consumo de água
#         df_base = carregar_base_consumo_agua(caminho_base_agua) #aqui eu passo o diretorio com o arquivo de agua
#         # retorno o dataframe, na função apenas leio o arquivo e removo espaços nas colunas.

#         #se a unidade estiver nessa lista não precisa fazer o calculo de dias uteis, pois elas funcionam 24h
#         unidades_sem_dias_uteis = ["AMA 24H CAPAO REDONDO", "AMA PQ NOVO SANTO AMARO", "HOSPITAL DIA M BOI MIRIM II", "HOSPITAL MOYSES DEUTSCH MBOI MIRIM", "PA JD MACEDONIA ",
#                                    "UPA JD ANGELA", "UPA VERA CRUZ", "PRONTO SOCORRO ARNALDO DE FIGUEIREDO FREITAS", "HOSPITAL GERAL DE ITAPEVI", "HOSPITAL MUNICIPAL EVANDRO FREIRE",
#                                     "HOSPITAL ESTADUAL DE FRANCO DA ROCHA", "HOSPITAL E MATERNIDADE DE SÃO ROQUE", "HOSPITAL E MATERNIDADE MARISKA RIBEIRO", "HOSPITAL DIA CAMPO LIMPO",
#                                       "HOSPITAL DIA M BOI MIRIM I"  ] # ou seja todas as unidades fazem o calculo de todos os dias do mês
#         if unidade not in unidades_sem_dias_uteis: # se a unidade não estiver na lista, ou seja, ela não funciona 24h, faz o calculo de dias úteis
#             dias_mes = apenas_dias_uteis(competencia, dias_mes) #executa o calculo de dias uteis e retorna a mesma variavel com o valor atualizado
        

#         if df_base is None: # se a base de calculo da agua for vazia
#             resultado['erros'].append("Erro ao carregar base de consumo de água")
#             st.error("❌ Erro ao carregar base de consumo de água") #mostra a mensagem de erro
#             return resultado
#             # return pd.DataFrame()   # e retorna um dataframe vazio para onde a função foi chamanda
            
        
#         # 6. Obter dados da unidade
#         dados_unidade = obter_dados_unidade_com_dias(df_base, unidade, dias_mes)

#         #retorna um dicionário com as as colunas
#         #   'UNIDADE': {0: 'Hospital A', 1: 'Hospital A'},
#         #   'PONDERAÇÃO': {0: 'Qtde. Colaborado-res Próprios e Terceiros', 1: 'Qtde. Volumes Esterilizados (sem ponderação)'},
#         #   'DESCRIÇÃO': {0: 'Litros por dia, por colaborador', 1: 'Litros por volume esterilizado'},
#         #   'PONDERAÇÃO FORMS': {0: 'TOTAL_COLABORADORESs', 1: '%_Atuação_CME'},
#         #   'VALOR': {0: 100, 1: 200}, #valor mutiplicado pela quantidade de dias
#         #   'VALOR_ORIGINAL': {0: 100, 1: 200}, #valor original da planilha
#         #   'DIAS_APLICADOS': {0: 30, 1: 30}
        
#         if dados_unidade is None: #se retornar none essa base
#             resultado['erros'].append(f"Dados da unidade '{unidade}' não encontrados")
#             st.error(f"❌ Dados da unidade '{unidade}' não encontrados") #mostra mensagem de erro
#             return resultado
#             # return pd.DataFrame()   # e retorna um dataframe vazio para onde a função foi chamanda
        
#         df_consolidado_multiplicado = None
#         arquivo_cme_multiplcado = None
#         arquivo_producao_multiplcado = None
#         arquivo_area_multiplcado = None

#         if df_consolidado is not None and not df_consolidado.empty:
#             df_consolidado_multiplicado = multiplicacao_das_bases(df_consolidado, dados_unidade)
#             st.info("✅ Arquivo colaboradores encontrado e processado")

#             with st.expander("📊 Ver todos os dados", expanded=False):
#                  st.dataframe(
#                      df_consolidado_multiplicado, 
#                      use_container_width=True, 
#                      hide_index=True
#                  )
#         else:
#             df_consolidado = None
#             st.warning("⚠️ Arquivo colaboradores não encontrado - será ignorado no cálculo")

#         arquivo_cme = buscar_arquivos_cme(output_dir)
#         #retorna a primeir base que ele encontrar a palavra cme, já em formatao de dataframe

#         if arquivo_cme is not None and not arquivo_cme.empty:
#             arquivo_cme_multiplcado = multiplicacao_das_bases(arquivo_cme, dados_unidade)
#             st.info("✅ Arquivo CME encontrado e processado")
#         else:
#             arquivo_cme = None
#             st.warning("⚠️ Arquivo CME não encontrado - será ignorado no cálculo")


#         arquivo_producao = buscar_arquivos_producao(output_dir)
#         #retorna a primeir bae qu ele encontrar a palavra cme, já em formatao de dataframe

#         if arquivo_producao is not None and not arquivo_producao.empty:
#             arquivo_producao_multiplcado = multiplicacao_das_bases(arquivo_producao, dados_unidade)
#             st.info("✅ Arquivo Produção encontrado e processado")
#         else:
#             arquivo_producao = None
#             st.warning("⚠️ Arquivo Produção não encontrado - será ignorado no cálculo")

#         arquivo_area = buscar_arquivos_area(output_dir)
#         #retorna a primeir bae qu ele encontrar a palavra cme, já em formatao de dataframe

#         if arquivo_area is not None and not arquivo_area.empty:
#             arquivo_area_multiplcado = multiplicacao_das_bases(arquivo_area, dados_unidade)
#             st.info("✅ Arquivo Área encontrado e processado")
#         else:
#             arquivo_area = None
#             st.warning("⚠️ Arquivo Área não encontrado - será ignorado no cálculo")

#         # 7. Consolidar todos os arquivos em um único arquivo final de água
#         st.info("🧮 Realizando cálculos de consumo de água...")
        
#         df_agua_final = consolidar_todos_arquivos_agua(
#             df_consolidado_multiplicado, #arquivo total colaboradores
#             arquivo_cme_multiplcado, #arquivo cme
#             arquivo_producao_multiplcado, #arquivo produção
#             arquivo_area_multiplcado #arquivo de area
#         )
        
#         if df_agua_final is None or df_agua_final.empty:
#             st.error("❌ Falha na consolidação final dos dados de água")
#             resultado['erros'].append("...")
#             return resultado           
#             # return pd.DataFrame()
        
#         resultado['sucesso'] = True

#         # 9. Salvar arquivo final de água
#         arquivo_agua_final = salvar_arquivo_agua_final(df_agua_final, output_dir, competencia, unidade)
        
#         if arquivo_agua_final is None:
#             st.error("❌ Falha ao salvar arquivo final de água")
#             resultado['erros'].append("Falha ao salvar arquivo final de água")
#             return resultado
#             # return pd.DataFrame()

#         # 10. Preencher dados do resultado
#         resultado['sucesso'] = True
#         resultado['dataframe'] = df_agua_final
#         resultado['dados_calculo'] = {
#             'Consumo_Total_Litros': df_agua_final['Quantidade'].sum(),
#             'Total_Colaboradores': total_colaboradores,
#             'Centros_Custo_Unicos': len(df_agua_final),
#             'Competência': competencia,
#             'Unidade': unidade,
#             'Dias_Processados': dias_mes,
#             'Arquivo_Salvo': os.path.basename(arquivo_agua_final)
#         }
        
#         # 10. Retornar o DataFrame final
#         st.success(f"🎉 Processo concluído! Arquivo final: {os.path.basename(arquivo_agua_final)}")
#         if resultado['sucesso']:
#             # Chama a função de exibição diretamente aqui
#             exibir_resultado_calculo_consolidado(resultado['dataframe'])
            
#             # Marca no session_state que o cálculo foi realizado
#             st.session_state['calculo_agua_realizado'] = True
            
#             # Força o rerun para limpar as mensagens
#             st.rerun()
#         return resultado
        
#     except Exception as e:
#         resultado['erros'].append(f"Erro geral no processo: {str(e)}")
#         st.error(f"Erro geral no processo de cálculo de água: {str(e)}")
#         return resultado
#         # return pd.DataFrame()  # dataframe vazio

def realizar_calculo_agua_consolidado(output_dir, competencia, unidade, caminho_base_agua):
    """
    VERSÃO ATUALIZADA: Usa dados do session_state ao invés de buscar arquivos
    """
    
    resultado = {
        'sucesso': False,
        'erros': [],
        'dados_calculo': {},
        'dataframe': pd.DataFrame()
    }
    
    try:
        st.info("🔍 Buscando dados de colaboradores na memória...")
        
        # 1. BUSCAR NO SESSION_STATE ao invés do disco
        palavras_chave = ['pessoal', 'enfermagem', 'colaboradores', 'terceiros']
        formularios_data = st.session_state.get('formularios_data', {})
        
        if not formularios_data:
            resultado['erros'].append("Nenhum formulário foi salvo ainda")
            st.error("❌ Nenhum formulário salvo na memória")
            return resultado
        
        # Busca formulários de colaboradores
        dfs_colaboradores = []
        for nome_form, df in formularios_data.items():
            nome_lower = nome_form.lower()
            
            if 'total' in nome_lower:
                continue
            
            for palavra in palavras_chave:
                if palavra in nome_lower:
                    dfs_colaboradores.append({'nome': nome_form, 'dataframe': df.copy()})
                    st.success(f"✅ Encontrado: {nome_form}")
                    break
        
        if not dfs_colaboradores:
            resultado['erros'].append("Nenhum formulário de colaboradores encontrado")
            st.error("❌ Nenhum formulário de colaboradores encontrado")
            return resultado
        
        # 2. CONSOLIDAR (mesmo código que já existe, mas usando dfs_colaboradores)
        todos_dados = []
        for item in dfs_colaboradores:
            df = item['dataframe'].copy()
            df.columns = df.columns.str.strip()
            
            if 'Quantidade' not in df.columns:
                continue
            
            df['Quantidade'] = pd.to_numeric(
                df['Quantidade'].astype(str).str.replace(',', '.'), 
                errors='coerce'
            ).fillna(0)
            
            df = df[df['Quantidade'] > 0]
            
            if df.empty:
                continue
            
            if 'Centro de Custo' not in df.columns:
                df['Centro de Custo'] = 'Não Informado'
            else:
                df['Centro de Custo'] = df['Centro de Custo'].fillna('Não Informado')
            
            if 'Competência' not in df.columns:
                df['Competência'] = competencia
            
            df_selecionado = df[['Competência', 'Centro de Custo', 'Quantidade']]
            todos_dados.append(df_selecionado)
        
        if not todos_dados:
            resultado['erros'].append("Nenhum dado válido processado")
            return resultado
        
        df_todos = pd.concat(todos_dados, ignore_index=True)
        
        df_consolidado = df_todos.groupby('Centro de Custo').agg({
            'Quantidade': 'sum',
            'Competência': 'first'
        }).reset_index()
        
        df_consolidado['Ponderação'] = 'Total Colaboradores'
        df_consolidado = df_consolidado[['Competência', 'Centro de Custo', 'Ponderação', 'Quantidade']]
        
        total_colaboradores = df_consolidado['Quantidade'].sum()
        st.success(f"✅ {len(df_consolidado)} centros de custo, {total_colaboradores:.0f} colaboradores")
        
        # 3. SALVAR (backup)
        nome_arquivo = f"total_colaboradores_{competencia}.csv".replace("/", "-").replace(" ", "_")
        caminho = os.path.join(output_dir, nome_arquivo)
        df_consolidado.to_csv(caminho, index=False, encoding='utf-8-sig', sep=';')
        
        # 4. RESTO DO CÓDIGO (dias, base água, etc.) - MANTÉM IGUAL
        dias_mes = obter_dias_do_mes(competencia)
        df_base = carregar_base_consumo_agua(caminho_base_agua)
        
        unidades_24h = ["AMA 24H CAPAO REDONDO", "HOSPITAL GERAL DE ITAPEVI", ...]  # sua lista
        if unidade not in unidades_24h:
            dias_mes = apenas_dias_uteis(competencia, dias_mes)
        
        dados_unidade = obter_dados_unidade_com_dias(df_base, unidade, dias_mes)
        
        if dados_unidade is None:
            resultado['erros'].append("Dados da unidade não encontrados")
            return resultado
        
        # 5. MULTIPLICAR colaboradores
        df_consolidado_multiplicado = multiplicacao_das_bases(df_consolidado, dados_unidade)
        
        # 6. BUSCAR CME, PRODUÇÃO, ÁREA NA MEMÓRIA (ao invés do disco)
        arquivo_cme_mult = None
        for nome_form, df in formularios_data.items():
            if 'cme' in nome_form.lower() and 'atuação' in nome_form.lower():
                df_cme = df.copy()
                if "Competencia" in df_cme.columns:
                    df_cme = df_cme.rename(columns={"Competencia": "Competência"})
                arquivo_cme_mult = multiplicacao_das_bases(df_cme, dados_unidade)
                st.info("✅ CME encontrado")
                break
        
        arquivo_prod_mult = None
        for nome_form, df in formularios_data.items():
            if 'produção' in nome_form.lower() or 'producao' in nome_form.lower():
                df_prod = df.copy()
                df_prod["Ponderação"] = "Produção"
                if "Competencia" in df_prod.columns:
                    df_prod = df_prod.rename(columns={"Competencia": "Competência"})
                arquivo_prod_mult = multiplicacao_das_bases(df_prod, dados_unidade)
                st.info("✅ Produção encontrada")
                break
        
        arquivo_area_mult = None
        for nome_form, df in formularios_data.items():
            if ('área' in nome_form.lower() or 'area' in nome_form.lower()) and 'criticidade' not in nome_form.lower():
                df_area = df.copy()
                if "Competencia" in df_area.columns:
                    df_area = df_area.rename(columns={"Competencia": "Competência"})
                arquivo_area_mult = multiplicacao_das_bases(df_area, dados_unidade)
                st.info("✅ Área encontrada")
                break
        
        # 7. CONSOLIDAR ÁGUA (mantém igual)
        df_agua_final = consolidar_todos_arquivos_agua(
            df_consolidado_multiplicado,
            arquivo_cme_mult,
            arquivo_prod_mult,
            arquivo_area_mult
        )
        
        if df_agua_final is None or df_agua_final.empty:
            resultado['erros'].append("Falha na consolidação final")
            return resultado
        
        # 8. SALVAR ÁGUA FINAL
        arquivo_final = salvar_arquivo_agua_final(df_agua_final, output_dir, competencia, unidade)
        
        if arquivo_final is None:
            resultado['erros'].append("Falha ao salvar")
            return resultado
        
        # 9. RESULTADO
        resultado['sucesso'] = True
        resultado['dataframe'] = df_agua_final
        resultado['dados_calculo'] = {
            'Consumo_Total_Litros': df_agua_final['Quantidade'].sum(),
            'Total_Colaboradores': total_colaboradores,
            'Centros_Custo_Unicos': len(df_agua_final),
            'Competência': competencia,
            'Unidade': unidade,
            'Dias_Processados': dias_mes,
            'Arquivo_Salvo': os.path.basename(arquivo_final)
        }
        
        st.success(f"🎉 Concluído! {os.path.basename(arquivo_final)}")
        exibir_resultado_calculo_consolidado(resultado['dataframe'])
        st.session_state['calculo_agua_realizado'] = True
        st.rerun()
        
        return resultado
        
    except Exception as e:
        resultado['erros'].append(f"Erro: {str(e)}")
        st.error(f"❌ Erro: {str(e)}")
        st.exception(e)
        return resultado

def exibir_resultado_calculo_consolidado(df_resultado):
    """
    Função que recebe um DataFrame e exibe os resultados de forma organizada
    """
    if df_resultado.empty:
        st.error("❌ Nenhum resultado para exibir - DataFrame vazio")
        return
    
    # Calcula as métricas do DataFrame
    consumo_total = df_resultado['Quantidade'].sum()
    centros_custo = len(df_resultado)
    
    # Exibe métricas principais
    st.success("✅ Cálculo de água realizado com sucesso!")
    
    def formatar_brasileiro(numero):
        # Formata com vírgulas americanas primeiro
        formatado = f"{numero:,.2f}"
        # Troca vírgula por um caractere temporário
        formatado = formatado.replace(",", "TEMP")
        # Troca ponto por vírgula (decimal brasileiro)
        formatado = formatado.replace(".", ",")
        # Troca o temporário por ponto (milhares brasileiro)
        formatado = formatado.replace("TEMP", ".")
        return formatado

    col1, col2 = st.columns(2)
    with col1:
        st.metric("💧 Consumo Total", f"{formatar_brasileiro(consumo_total)} L")
    with col2:
        st.metric("🏢 Centros de Custo", f"{centros_custo}")
    
    # # 🔝 Top 5 Centros de Custo por Consumo
    # df_top5 = df_resultado.nlargest(5, 'Quantidade').copy()
    # df_top5['Quantidade'] = df_top5['Quantidade'].apply(lambda x: f"{x:,.2f} L")
    
    # with st.expander("🔝 Top 5 Centros de Custo por Consumo", expanded=False):
    #     st.dataframe(
    #         df_top5[['Centro de Custo', 'Quantidade']], 
    #         use_container_width=True,
    #         hide_index=True
    #     )
    
    # # 📊 Tabela completa
    # df_completo = df_resultado.copy()
    # df_completo['Quantidade'] = df_completo['Quantidade'].apply(lambda x: f"{x:,.2f} L")
    
    # with st.expander("📊 Ver todos os dados", expanded=False):
    #     st.dataframe(
    #         df_completo, 
    #         use_container_width=True, 
    #         hide_index=True
    #     )
    
    return True

