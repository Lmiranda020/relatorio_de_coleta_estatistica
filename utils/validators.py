"""
Funções de validação de dados
"""
import pandas as pd
import re
import streamlit as st

def normalizar_nome_arquivo(nome_formulario): # crio uma função que recebe o nome do formulário e retorna o nome do arquivo normalizado
        # Remove caracteres especiais e converte para minúsculas
        nome_normalizado = nome_formulario.lower() # coloca tudo em letra minuscula
        
        # Substitui espaços e caracteres especiais 
        nome_normalizado = nome_normalizado.replace(" ", "_")
        nome_normalizado = nome_normalizado.replace("-", "_")
        nome_normalizado = nome_normalizado.replace("á", "a")
        nome_normalizado = nome_normalizado.replace("é", "e")
        nome_normalizado = nome_normalizado.replace("í", "i")
        nome_normalizado = nome_normalizado.replace("ó", "o")
        nome_normalizado = nome_normalizado.replace("ú", "u")
        nome_normalizado = nome_normalizado.replace("ã", "a")
        nome_normalizado = nome_normalizado.replace("õ", "o")
        nome_normalizado = nome_normalizado.replace("ç", "c")
        
        # Substitui todos os caracteres que não são letras, números ou underscore por _
        import re # importa o regex
        nome_normalizado = re.sub(r'[^\w]', '_', nome_normalizado)
        # o r serve para ler o valor como uma string bruta, ou seja, sem interpretar caracteres especiais, pois existe comandos especificos do regex que usam caracteres especiais, como \w, que representa qualquer letra, número ou underscore, ou \n que representa uma quebra de linha, por exemplo
        # [] indica o inicio e o fim do CONJUNTO de caracteres que serão substituídos
        # ^: dentro de [...], significa negação (ou seja, “tudo que não está aqui”)
        # \w: representa qualquer letra, número ou underscore
        # resumo: tudo que não esteja aqui e não for letra, número ou underscore, será substituído por _
        # aonde ele vai fazer isso? na string nome_normalizado
        # e por fim retorna a variavel o nome tratado, ou seja, atualizado

        # Remove underscores duplicados
        nome_normalizado = re.sub(r'_+', '_', nome_normalizado)
        # _+: o caractere _ repetido uma ou mais vezes
        # +: quantificador que significa “um ou mais”
        # será substituído por um único underscore _
        # aqui não precisa de [] porque não estamos lidando com um conjunto de caracteres, mas sim com um único caractere que é o underscore

        # Remove underscores no início e fim
        nome_normalizado = nome_normalizado.strip('_') # remove o _ no início e no fim da string
        
        return nome_normalizado # retorna o nome normalizado para onde chamar essa função

def validar_quantidade_ou_tempo(df, coluna="Quantidade"): # crio uma função, que recebe um DataFrame e o nome da coluna a ser validada, que por padrão é "Quantidade"
        quant_str = df[coluna].fillna("").astype(str).str.strip()
        # Aqui eu pego a coluna do DataFrame, preencho valores ausentes com string vazia, converto para string e removo espaços em branco no início e no fim
        # e armazeno o resultado na variavel quant_str

        # Regex para verificar se o valor estão no  formato HH:MM:SS (24h), ou seja em horas
        padrao_tempo = re.compile(r"^\d{1,2}:\d{2}:\d{2}$") # Quando  usa re.compile(),  está criando um "objeto de função regex", ou seja, algo que você pode guardar em uma variável e depois usar como se fosse uma função
        """
        ^	Início da string
        \d{1,2}	Um ou dois dígitos (ex: 8, 12)
        :	Dois-pontos literal (separador de tempo)
        \d{2}	Dois dígitos (ex: 05, 30, 59) — para minutos e segundos
        :	Outro dois-pontos
        \d{2}	Dois dígitos novamente
        $	Final da string
        """

        def eh_valido(valor): # crio outra função que recebe um valor
            if valor == "": # se o valor for vazio, retorna False para onde foi chamado a função
                return False
            if padrao_tempo.match(valor): # se o valor corresponder ao padrão de tempo, retorna True, ou seja, é um valor válido
                return True 
            try: # agora ele tenta converter o valor, casos ele não seja um tempo e nem vazio
                # Tenta converter número com vírgula ou ponto
                float(valor.replace(",", ".")) # substitui vírgula por ponto para converter para float
                return True # se der certo, retorna True, ou seja, é um valor válido
            except: # se der erro na conversão, ou seja, se o valor não for um número válido
                return False #retorna False, ou seja, é um valor inválido

        validos = quant_str.apply(eh_valido) # pega a coluna do dataframe que está com as quantidades e aplica a função eh_valido em cada valor, retornando uma série de booleanos (True ou False) indicando se cada valor é válido ou não

        if not validos.all(): # se nem todos os valores são válidos, ou seja, se houver pelo menos um valor inválido, ou seja FALSE
            invalidos = df.loc[~validos, coluna] # pega as linhas do DataFrame onde os valores são inválidos, ou seja, onde validos é False
            return False, invalidos # retorna False e os valores inválidos encontrados na coluna especificada
        else: # agora se todos os valores são válidos, ou seja, se validos é True para todos os valores
            # Converte os valores válidos
            def converte_valor(v): # cria uma função que recebe um valor v
                if padrao_tempo.match(v): # se o valor corresponder ao padrão de tempo, ou seja, estiver no formato HH:MM:SS
                    return v  # mantém string do tempo
                num = float(v.replace(",", ".")) # se não for um tempo, tenta converter o valor para float, substituindo vírgula por ponto
                # Retorna como int se for inteiro, senão float
                return int(num) if num.is_integer() else num # se o valor for um número inteiro, retorna como int, caso contrário retorna como float

            df[coluna] = quant_str.apply(converte_valor) # e por fim aplica a função converte_valor em cada valor da coluna especificada do DataFrame, convertendo os valores válidos para o formato correto (int ou float)
            return True, df # retorna True e o DataFrame atualizado com os valores convertidos
