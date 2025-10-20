import streamlit as st #para fazer a interface
import pandas as pd #para manipular os dados
import re #para fazer regex
import os #para manipular arquivos e pastas, a biblioteca serve para interagir com o sistema operacional
import importlib.util #para importar dinamicamente os módulos dos formulários
import time #para fazer delay nas mensagens
from PIL import Image #para manipular imagens
from pathlib import Path #para manipular caminhos de arquivos
from config.constants import (
    DEPARA_UNIDADES, 
    FORM_DIR,
    competencias,
    imagem_cejam,
    imagem_sus
)
from auth.login import mostrar_tela_login
from components.header import mostrar_header_usuario
from utils.validators import normalizar_nome_arquivo, validar_quantidade_ou_tempo
from utils.file_utils import get_desktop_path
import smtplib
from email.message import EmailMessage
import sqlite3
from components.ajuda_modal_tela_home import  adicionar_botao_ajuda_sidebar, modal_ajuda
from components.ajuda_modal_tela_login import botao_ajuda_login_simples
from components.painel_tickets_user import  mostrar_meus_tickets
from components.painel_suporte import  mostrar_painel_suporte
from components.modal_cadastro_senha import modal_cadastro_senha
from data.manager_postgre import DatabaseManagerPostgres
from streamlit.components.v1 import html
import datetime
from components.dados_permanentes import processar_dados_permanentes_completo
from utils.calculo_agua import realizar_calculo_agua_consolidado, exibir_resultado_calculo_consolidado
from api.api_envio_de_dados_estatistica import enviar_consolidado_para_api, obter_competencia_usuario
from api.api_envio_de_dados_produção import enviar_producao_para_api, registrar_no_banco
from api.api_ponderacao import de_para_ponderacao
from api.api_produto import de_para_produto
try:
    from data.limpeza_base_de_para_rpa_vs_kpih import (
        armazenar_unidade_id_na_sessao,
    )
    from api.api_centro_custo import (
        consumir_api_unidade_especifica,
    )
    API_CENTRO_CUSTO_DISPONIVEL = True
except ImportError as e:
    st.warning(f"Módulos de API de centro de custo não encontrados: {e}")
    API_CENTRO_CUSTO_DISPONIVEL = False
from components.modal_feedback_pos_envio import modal_feedback_sucesso
from utils.file_utils import criar_zip_formularios, get_tamanho_legivel
import zipfile
from io import BytesIO
import tempfile

# === FUNÇÃO PARA ARMAZENAR ID DA UNIDADE QUANDO PROCESSAR DADOS PERMANENTES ===
def processar_dados_permanentes_com_id():
    """
    Versão modificada que armazena o ID da unidade na sessão após processar dados permanentes.
    """
    try:
        # Chama a função original de processamento
        from components.dados_permanentes import processar_dados_permanentes_completo
        
        sucesso = processar_dados_permanentes_completo()
        
        if sucesso:
            # Após sucesso, armazenar o ID da unidade na sessão
            if 'unidade_id' in st.session_state:
                st.info(f"ID da unidade já está na sessão: {st.session_state['unidade_id']}")
            else:
                # Buscar ID da unidade baseado no nome da unidade
                try:
                    from components.dados_permanentes import buscar_unidade_id_e_token
                    unidade_usuario = st.session_state.get('unidade_usuario', '')
                    
                    if unidade_usuario:
                        unidade_id, _ = buscar_unidade_id_e_token(unidade_usuario)
                        
                        if unidade_id:
                            armazenar_unidade_id_na_sessao(unidade_id)
                        else:
                            st.warning("Não foi possível obter ID da unidade")
                    
                except Exception as e:
                    st.warning(f"Erro ao obter ID da unidade: {e}")
        
        return sucesso
        
    except Exception as e:
        st.error(f"Erro ao processar dados permanentes: {e}")
        return False


def carregar_dados_salvos(competencia, unidade_selecionada, nome_formulario):
    """
    Carrega dados salvos anteriormente para a competência, unidade e formulário específico
    """
    try:
        # Verifica se existe dados salvos no session_state
        if 'formularios_data' not in st.session_state:
            return {}
        
        # Verifica se o formulário específico foi salvo
        if nome_formulario not in st.session_state['formularios_data']:
            return {}
        
        # Pega o DataFrame salvo do formulário
        df_salvo = st.session_state['formularios_data'][nome_formulario]
        
        # Converte o DataFrame em um dicionário para facilitar o acesso
        dados_salvos = {}
        
        for _, row in df_salvo.iterrows():
            codigo_cc = row['Código CC']
            
            # Para formulários simples com quantidade numérica
            dados_salvos[codigo_cc] = {
                'quantidade': str(row['Quantidade']) if 'Quantidade' in row else '0'
            }
        
        return dados_salvos
        
    except Exception as e:
        # Em caso de erro, retorna dicionário vazio
        return {}

# Estados dos modais de senha
if "modal_cadastro_senha" not in st.session_state:
    st.session_state.modal_cadastro_senha = False
    
if "modal_recuperar_senha" not in st.session_state:
    st.session_state.modal_recuperar_senha = False

if "primeiro_acesso" not in st.session_state:
    st.session_state.primeiro_acesso = False

# Inicializa o sistema de login no session_state
if 'usuario_logado' not in st.session_state: # se a chave 'usuario_logado' não existir no session_state, ou seja, se o usuário não estiver logado
    # o que não vai estar, pois é a primeira vez que o aplicativo é executado
    st.session_state['usuario_logado'] = False # criar uma chave usuario_logado como FALSO
    st.session_state['email_usuario'] = None # criar uma chave email_usuario com o valor vazio
    st.session_state['unidade_usuario'] = None # criar uma chave unidade_usuario com o valor vazio

def mostrar_configuracoes_logado(): #Cria uma função para mostrar as configurações do usuário logado
    col1 = st.columns(1)[0] # cria uma coluna única para o selectbox de competência, ou seja, a coluna 1 terá apenas uma parte

    with col1: # com a coluna 1
        competencia_selecionada = st.selectbox("Selecione a competência:", competencias)
        st.session_state['competencia_usuario'] = competencia_selecionada # cria um selectbox para o usuário escolher a competência, ou seja, o mês e ano que ele deseja preencher os formulários
    return st.session_state['unidade_usuario'], competencia_selecionada # retorna para onde chamar a função, a unidade que já foi salva no momento do login e a competência selecionada
    # perceba que a unidade eu não faço nada so retorno para onde chamar a afunção, a unidade está na memoria do stremelit

# Cria o diretório no desktop do usuário
# desktop_path = get_desktop_path() # primeiro eu chamo a função que retorna o caminho do desktop do usuário e armazena na variavel desktop_path
# OUTPUT_DIR = os.path.join(desktop_path, "formularios_preenchidos") # aqui eu faço um join do caminho do desktop com o nome da pasta que eu quero criar, ou seja, "formularios_preenchidos" e armazena em uma falsa constante OUTPUT_DIR

# No Streamlit Cloud, usa pasta temporária
OUTPUT_DIR = tempfile.mkdtemp(prefix="formularios_")

if not st.session_state['usuario_logado']: # se não estiver logado, ou seja, se não existir a chave usuario_logado no session_state

    if not st.session_state['usuario_logado']:
        if st.session_state.get("modal_cadastro_senha", False):
            modal_cadastro_senha()
            st.stop()
        else:
            mostrar_tela_login()
            if not st.session_state.get("modal_cadastro_senha", False):
                botao_ajuda_login_simples()


elif st.session_state['email_usuario'] == "custos@cejam.org.br":
    # Header do usuário logado
    mostrar_header_usuario() # monstra a parte inicial do sistema, ou seja, o cabeçalho com as informações do usuário logado e o botão de logout


    mostrar_painel_suporte()


else: # agora se estiver logado, ou seja, se a chave usuario_logado for VERDADEIRO
    # ou seja o usuario colocou o emial e senha, passou pela verificação e agora a chave usuario_logado é VERDADEIRO
    # Mensagem temporária de sucesso ao criar/encontrar a pasta

# Inicializa a chave no session_state se ela ainda não existir
    if "mensagem_pasta_exibida" not in st.session_state:
        st.session_state["mensagem_pasta_exibida"] = False

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # makedirs é uma função do módulo os que cria uma pasta
        # e o exist_ok=True significa que se a pasta já existir, não vai dar erro
        # OUTPUT_DIR é a variável que contém o caminho da pasta que eu quero criar, junto com o nome da pasta "formularios_preenchidos"
        # if not st.session_state["mensagem_pasta_exibida"]:
        #     msg = st.success(f"✅ Pasta criada/encontrada em: {OUTPUT_DIR}")
        #     # A mensagem de sucesso é exibida na interface do usuário, informando que a pasta foi criada
        #     time.sleep(3)
        #     # a mesangem de sucesso é exibida por 3 segundos
        #     msg.empty()
        #     # depois a mensagem é removida da interface do usuário

        #     # Marca que a mensagem já foi exibida
        #     st.session_state["mensagem_pasta_exibida"] = True
    except Exception as e:
        st.error(f"❌ Erro ao criar pasta no desktop: {str(e)}")
        # se der erro ao criar a pasta, ele captura a exceção e mostra uma mensagem de erro
        OUTPUT_DIR = "formularios_preenchidos"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # cria a pasta localmente, ou seja, na mesma pasta onde o script está rodando
        st.warning(f"⚠️ Usando pasta local como alternativa: {OUTPUT_DIR}")
        # mostra uma mensagem de aviso informando que está usando a pasta local como alternativa
        
    # Header do usuário logado
    mostrar_header_usuario() # monstra a parte inicial do sistema, ou seja, o cabeçalho com as informações do usuário logado e o botão de logout
    
    # Cria 3 colunas: esquerda (logo CEJAM), centro (título), direita (logo SUS)
    col_esq, col_centro, col_dir = st.columns([1, 6, 1]) # 1 ,6, 1 significa que a coluna esquerda terá 1 parte, a do meio terá 6 partes e a da direita terá 1 parte, ou seja, a coluna do meio será maior que as outras duas

    # Logo CEJAM
    with col_esq: # com a coluna esquerda, eu vou colocar a logo do CEJAM
        if os.path.exists(imagem_cejam): # se existir a imagem do CEJAM, eu vou exibir ela
            # path é um metodo de caminho
            # os.path.exists() verifica se o caminho existe, ou seja, se a imagem do CEJAM está no caminho especificado
            st.image(Image.open(imagem_cejam), width=100)
            # st.image é um método do streamlit que exibe uma imagem na interface do usuário
            # Image é uma classe usada para abrir, editar e manipular imagens dentro do Python, da biblioteca PIL (Python Imaging Library). Ela não exibe nada visualmente, só carrega e trata a imagem na memória.
            # Image.open() é um método da classe Image que abre uma imagem a partir de um caminho especificado, nesse caso, o caminho da imagem do CEJAM
            # Se a imagem existir, ela é aberta e exibida com uma largura de 100 pixels
        else:
            st.warning("Logo CEJAM não encontrada.")
            # se a imagem não existir, eu vou mostrar uma mensagem de aviso

        # Título
    with col_centro: # com a coluna do meio, eu vou colocar o título do aplicativo
        st.markdown( # é um método do streamlit que permite escrever texto formatado em Markdown
            # porem eu vou usar o unsafe_allow_html=True, que permite usar HTML dentro do Markdown, pois preciso centralizar o título, e o markdown não permite centralizar o texto
            "<h1 style='text-align: center;'>Relatório de Coleta</h1>",
            # Cria um título de nível 1 (<h1>)
            # Com alinhamento central via CSS: style='text-align: center;
            unsafe_allow_html=True
        )

        # Logo SUS
    with col_dir: # segue mesmo raciocínio da coluna esquerda, mas agora com a logo do SUS
        if os.path.exists(imagem_sus):
            st.image(Image.open(imagem_sus), width=100)
        else:
            st.warning("Logo SUS não encontrada.")
        

    # Aqui vai o conteúdo principal do app, criar um link com um video e o manual do aplicativo
    col1, col2 = st.columns([1, 1]) # cria duas colunas, a primeira com 1 parte e a segunda com 6 partes, ou seja, a segunda coluna é maior que a primeira
    with col1: # com a coluna 1
        st.markdown("### 📖 Manual do Usuário")
        st.markdown("[Clique aqui para acessar o manual completo](https://docs.google.com/document/d/1wIQeDLxCjGB1isiwhQCp9CnXX94HB-UC)")

    with col2: # com a coluna 2 link com o vídeo
        st.markdown("### 🎥 Vídeo Explicativo")
        st.markdown("[Clique aqui para assistir ao vídeo explicativo](https://www.loom.com/share/your-video-id)")

    # Mostra onde os arquivos serão salvos
    st.info("💡 **Dica:** Após consolidar, você poderá baixar todos os formulários em formato ZIP.")
    # msg1 = st.info(f"📁 **Arquivos serão salvos em:** {OUTPUT_DIR}")
    # Aguarda 3 segundos e remove a mensagem
    # time.sleep(3)
    # msg1.empty()
    # comentei pois vou manter essa mensagem na tela, para o usuário saber onde os arquivos serão salvos

    # carrega o mapeamento de unidades a partir do arquivo Excel
    df_mapeamento = pd.read_excel(DEPARA_UNIDADES)
    col_formulario = df_mapeamento.columns[0] # armazena o nome da primeira coluna do DataFrame, que é o nome "Formulário", ou seja o cabeçalho do DataFrame
    col_permanente = "Permanente?" # crio uma variavel que armazena o nome da coluna que indica se o formulário é permanente ou não

    assert col_permanente in df_mapeamento.columns, "'Permanente?' precisa estar na planilha"
    # O assert é uma verificação de segurança (checagem) no Python. Ele serve para garantir que uma condição seja verdadeira
    # então eu vejo se a variavel col_permanente está nas colunas do DataFrame df_mapeamento
    # se não estiver ele vai apresentar a mensagem de erro "'Permanente?' precisa estar na planilha"


    # Seção de seleção de configurações
    st.markdown("---") # cria uma linha horizontal para separar as seções
    st.markdown("## 📋 Configurações") # cria como se fosse um título

    unidade, competencia = mostrar_configuracoes_logado() # aqui eu chamo a função que cria uma coluna 
    # com essa coluna eu defino o selectbox de competência, ou seja, o mês e ano que o usuário deseja preencher os formulários
    # e retorna a unidade do usuário logado e a competência selecionada

    competencia_normalizada = competencia.replace("/", "-").replace(" ", "_")
    OUTPUT_DIR_COMPETENCIA = os.path.join(OUTPUT_DIR, competencia_normalizada)
    # Cria a subpasta da competência
    try:
        os.makedirs(OUTPUT_DIR_COMPETENCIA, exist_ok=True)
        # Atualiza o OUTPUT_DIR para usar a nova subpasta
        OUTPUT_DIR = OUTPUT_DIR_COMPETENCIA
    except Exception as e:
        st.error(f"❌ Erro ao criar subpasta da competência: {str(e)}")


    # Armazena a unidade selecionada no session_state para os formulários
    if unidade: # se true, ou melhor se essa variael não é none, porque none é false
        st.session_state['unidade_selecionada'] = unidade # é criado uma nova chave na memoria do Streamlit, chamada 'unidade_selecionada', que armazena a unidade do usuário que vem da bse em excel login_unidade.xlsx

    alteracao_permanente = st.radio( # cria um radio button, que é um botão de opção, onde o usuário pode escolher apenas uma opção
        "Há alguma alteração nos dados permanentes este mês?", # esse é o texto que aparece acima do radio button
        ["Não", "Sim"], # aqui eu defino as opções que o usuário pode escolher, nesse caso "Não" e "Sim"
        index=0 # index=0 significa que a opção "Não" será selecionada por padrão, se fosse index=1, a opção "Sim" seria selecionada por padrão
    )

    
    # Lista de formulários finais e formulários permanentes com alteração
    formularios_para_unidade = []  # crio uma lista vazia que vai armazenar os formulários aplicáveis para a unidade selecionada
    formularios_permanentes_para_escolher = [] # crio uma lista vazia que vai armazenar os formulários permanentes para a unidade selecionada
    formularios_permanentes_para_API = [] # cria uma lista vazia que vai armazenar os formulários permanentes que serão enviados para a API, ou seja, que não tem alteração permanente

    for i, row in df_mapeamento.iterrows(): # para cada index i e linha row no DataFrame df_mapeamento, vou interar sobre cada linha do DataFrame
        nome_formulario = row[col_formulario] # armazena o nome do formulário na variavel nome_formulario, que é o valor da primeira coluna do DataFrame
        eh_permanente = row[col_permanente] == True # verifica se o formulário é permanente, comparando o valor da coluna "Permanente?" com True, o resultado é um booleano (True ou False)
        aplicavel = row[unidade] == True # verifica se o formulário é aplicável para a unidade selecionada, comparando o valor da coluna correspondente à unidade com True, o resultado é um booleano (True ou False)

    #  Primeiro: separar os formulários permanentes com alteração
        if aplicavel: # se o valor é TRUE
            if not eh_permanente: # se o formulário não é permanente, ou seja é Falso
                # Se não é permanente, entra direto
                formularios_para_unidade.append(nome_formulario) # adiciona o nome do formulário à lista formularios_para_unidade

            elif eh_permanente and alteracao_permanente == "Não": # se o formulário é permanente e o usuário indicou que não há alteração permanente
                formularios_permanentes_para_API.append(nome_formulario) # ele adiciona à lista de permanentes para API, ou seja, que não tem alteração permanente
                
            elif eh_permanente and alteracao_permanente == "Sim": # se o formulário é permanente e o usuário indicou que há alteração permanente
                # Se é permanente e o usuário disse que há alteração,
                formularios_permanentes_para_escolher.append(nome_formulario) # adiciona à lista para ele escolher depois

    # 3. ADICIONAR SEÇÃO DE PROCESSAMENTO DA API
    # Adicionar APÓS a definição das listas, ANTES da "Interface para seleção":
        
    selecionados = []  # Inicializa como lista vazia
    # Interface para seleção de formulários permanentes (se houver)
    if alteracao_permanente == "Sim" and formularios_permanentes_para_escolher: # se alteração permanente for "Sim" e houver formulários permanentes para escolher
        st.markdown("### Formulários permanentes com alteração") # aparecece o título "Formulários permanentes com alteração"

        selecionar_todos = st.checkbox("Selecionar todos os formulários permanentes") # cria uma caixa de seleção para o usuário escolher se quer selecionar todos os formulários permanentes

        selecionados = st.multiselect( # cria um multiselect, que é uma caixa de seleção onde o usuário pode escolher vários itens
            "Escolha os formulários que deseja alterar:", # aqui é o texto que aparece acima da caixa de seleção
            formularios_permanentes_para_escolher, # aqui é a lista de formulários permanentes para escolher, que foi criada acima
            default=formularios_permanentes_para_escolher if selecionar_todos else None # se o usuário selecionar a opção "Selecionar todos os formulários permanentes", o valor padrão será a lista de formulários permanentes para escolher, caso contrário será None
        # default define quais opções estarão selecionadas por padrão quando o componente aparecer na interface
        )

        # NOVA LÓGICA CORRIGIDA: Separar os selecionados dos não selecionados
        if formularios_permanentes_para_escolher:  # Só executa se há formulários para escolher
            nao_selecionados = [f for f in formularios_permanentes_para_escolher if f not in selecionados]
            
        # Os não selecionados voltam para API
        formularios_permanentes_para_API.extend(nao_selecionados)

        # Adiciona os formulários selecionados à lista final (para preenchimento manual)
        formularios_para_unidade.extend(selecionados)
            # append() é um método do Python que adiciona um unico item ao final de uma lista, exmeplo:
        
            # lista = [1, 2, 3]
            # lista.append([4, 5])
            # print(lista)
            # Resultado: [1, 2, 3, [4, 5]]
        

            # # extend() é um método do Python que  adiciona os elementos da outra lista individualmente, exemplo:
        
            # lista = [1, 2, 3]
            # lista.extend([4, 5])
            # print(lista)
            # Resultado: [1, 2, 3, 4, 5]
        

        
            # Use .append(x) para adicionar um único elemento.

            # Use .extend([x, y, z]) para adicionar vários elementos de uma vez (ou seja, de uma lista).
        

    # === PROCESSAMENTO DE DADOS PERMANENTES VIA API ===
    if formularios_permanentes_para_API: # se houver formulários permanentes para API, ou seja, se a lista não estiver vazia
        st.markdown("---")
        st.markdown("### 🔄 Processamento de Dados Permanentes")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Identificados {len(formularios_permanentes_para_API)} formulários permanentes para buscar da competência anterior:")
            for form in formularios_permanentes_para_API:
                st.write(f"• {form}")
            
            # NOVA LÓGICA: Verifica quais formulários da lista atual já foram processados
            formularios_ja_processados = []
            formularios_nao_processados = []

            for form in formularios_permanentes_para_API:
                if form in st.session_state.get('formularios_data', {}):
                    formularios_ja_processados.append(form)
                else:
                    formularios_nao_processados.append(form)

            # Status mais detalhado
            if len(formularios_ja_processados) == len(formularios_permanentes_para_API):
                st.success("✅ Todos os dados permanentes da lista atual já foram processados")
            elif len(formularios_ja_processados) > 0:
                st.info(f"✅ {len(formularios_ja_processados)} já processados | ⏳ {len(formularios_nao_processados)} pendentes")
                with st.expander("Ver detalhes"):
                    if formularios_ja_processados:
                        st.write("**Já processados:**")
                        for form in formularios_ja_processados:
                            st.write(f"• {form}")
                    if formularios_nao_processados:
                        st.write("**Pendentes:**")
                        for form in formularios_nao_processados:
                            st.write(f"• {form}")
            else:
                st.warning("⏳ Clique no botão ao lado para processar os dados permanentes")

        with col2:
            # NOVA LÓGICA: Botão habilitado se há formulários não processados na lista atual
            # ou se o usuário quer reprocessar (mesmo que já tenha processado antes)
            tem_formularios_nao_processados = len(formularios_nao_processados) > 0
            
            # Opção para reprocessar todos (mesmo os já processados)
            reprocessar_todos = st.checkbox("🔄 Reprocessar todos", 
                                        help="Marque para reprocessar também os formulários já processados")
            
            # Determina se o botão deve estar habilitado
            if reprocessar_todos:
                botao_habilitado = True
                texto_botao = "🔄 Reprocessar Todos"
                help_text = "Reprocessará todos os formulários da lista, incluindo os já processados"
            elif tem_formularios_nao_processados:
                botao_habilitado = True
                texto_botao = f"🔄 Processar ({len(formularios_nao_processados)})"
                help_text = f"Processará {len(formularios_nao_processados)} formulários pendentes"
            else:
                botao_habilitado = False
                texto_botao = "✅ Processados"
                help_text = "Todos os formulários da lista atual já foram processados"
            
            if st.button(texto_botao, type="primary", disabled=not botao_habilitado, help=help_text):
                
                # Se for reprocessar, limpa os dados dos formulários permanentes antes
                if reprocessar_todos:
                    st.info("🔄 Reprocessando todos os formulários...")
                    # Remove os formulários permanentes já processados da memória
                    for form in formularios_permanentes_para_API:
                        if form in st.session_state['formularios_data']:
                            del st.session_state['formularios_data'][form]
                else:
                    st.info(f"🔄 Processando {len(formularios_nao_processados)} formulários pendentes...")
                
                # Chama a função de processamento original (sem parâmetros extras)
                sucesso = processar_dados_permanentes_completo()
                
                if sucesso:
                    # Atualiza a flag geral apenas se TODOS os formulários da API foram processados
                    todos_processados = all(f in st.session_state.get('formularios_data', {}) for f in formularios_permanentes_para_API)
                    st.session_state['dados_permanentes_processados'] = todos_processados
                    
                    if todos_processados:
                        st.success("✅ Todos os dados permanentes foram processados com sucesso!")
                    else:
                        st.success(f"✅ {len(formularios_permanentes_para_API)} formulários processados com sucesso!")
                    
                    st.rerun()  # Recarrega para atualizar interface
                else:
                    st.error("❌ Erro no processamento. Tente novamente.")

    # Armazenar no session_state para uso nas funções de API
    #movi ela para o final, para garantir que as listas estejam completas
    #formularios_permanentes_para_API esteja completamente definida (seja pelo caso "Não" ou pelo caso "Sim" após a seleção do usuário)
    st.session_state['formularios_permanentes_para_API'] = formularios_permanentes_para_API
    st.session_state['output_dir'] = OUTPUT_DIR
    
    # Inicializa o armazenamento dos dados dos formulários no session_state
    if 'formularios_data' not in st.session_state: # se não existir a chave 'formularios_data' no session_state, ou seja, se não tiver nenhum formulário salvo na memória com essa chave
        st.session_state['formularios_data'] = {} # cria um dicionário vazio para armazenar os dados dos formulários preenchidos, ou seja, os dados que o usuário vai preencher nos formulários

    # Só mostra as abas se há formulários para mostrar
    # Verifica se tem formulários manuais OU se dados permanentes foram processados
    dados_permanentes_processados = st.session_state.get('dados_permanentes_processados', False)
    tem_formularios_manuais = len(formularios_para_unidade) > 0
    tem_formularios_api = len(formularios_permanentes_para_API) > 0

    if tem_formularios_manuais or (tem_formularios_api and dados_permanentes_processados):

        aba_formularios, aba_tickets = st.tabs(["📝 Formulários", "🎫 Meus Tickets"])
        with aba_tickets:
            mostrar_meus_tickets(st.session_state['email_usuario'])

        with aba_formularios:
            # st.markdown("---") # cria uma linha horizontal para separar as seções
            st.markdown("## 📝 Formulários") # cria um título para a seção de formulários
            
            
            st.markdown("""
            <style>
                .floating-nav {
                    position: fixed;
                    right: 20px;
                    bottom: 20px;
                    z-index: 9999;
                }
                
                .nav-btn {
                    display: block;
                    width: 55px;
                    height: 55px;
                    margin-bottom: 10px;
                    border-radius: 50%;
                    border: none;
                    background-color: #87CEEB;
                    color: #2c3e50;
                    font-size: 18px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 3px 12px rgba(0,0,0,0.15);
                    text-decoration: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .nav-btn:hover {
                    background-color: #5DADE2;
                    transform: scale(1.1);
                }
            </style>

            <div class="floating-nav">
                <a href="#inicio-formularios" class="nav-btn" title="Início dos formulários">↑</a>
                <a href="#final-formularios" class="nav-btn" title="Final dos formulários">↓</a>
            </div>

            <div id="inicio-formularios"></div>
            """, unsafe_allow_html=True)
                    
            # === SIDEBAR COM LISTA DE FORMULÁRIOS ===
            with st.sidebar: # é um container especial que permite adicionar inputs, botões, textos, etc., na lateral esquerda da tela.
                st.markdown("### 📋 Lista de Formulários") # cria apenas um texto
                
                # Busca por formulários
                busca = st.text_input("🔍 Buscar formulário:", placeholder="Digite para filtrar...")
                # cria um texto input para o usuario escrever os formularios
                # placeholder é um texto que aparece dentro do campo de texto, mas desaparece quando o usuário começa a digitar
                # e por fim armazena o que o usuário digitar na variável busca
                
                # Filtro por status
                filtro_status = st.selectbox( # cria um selectbox, que é um campo de seleção onde o usuário pode escolher uma opção e armazena o valor selecionado na variável filtro_status
                    "📊 Filtrar por status:", # titulo
                    ["Todos", "Pendentes", "Completos", "Com Erro"], # opções disponíveis no selectbox
                    index=0 # por padrão é o valor 0 que é "Todos" que será selecionado inicialmente
                )

                # Progress bar geral - VERSÃO ATUALIZADA COM API
                formularios_salvos = len(st.session_state.get('formularios_data', {}))
                total_formularios_manual = len(formularios_para_unidade)
                total_formularios_api = len(st.session_state.get('formularios_permanentes_para_API', []))

                # Calcula total considerando processamento da API
                if st.session_state.get('dados_permanentes_processados', False):
                    total_formularios = total_formularios_manual + total_formularios_api
                    #Garantir que não conte duplicado
                    formularios_completos = len(set(st.session_state.get('formularios_data', {}).keys()).intersection(set(formularios_para_unidade + st.session_state.get('formularios_permanentes_para_API', []))))
                else:
                    total_formularios = total_formularios_manual
                    #Contar apenas os formulários manuais que realmente foram salvos
                    formularios_completos = len([f for f in formularios_para_unidade if f in st.session_state.get('formularios_data', {})])
                    
                progresso = (formularios_completos / total_formularios) * 100 if total_formularios > 0 else 0

                st.metric("Progresso Geral", f"{formularios_completos}/{total_formularios}")
                st.progress(progresso / 100)

                # Breakdown detalhado se houver formulários da API
                if total_formularios_api > 0:
                    st.markdown("**Detalhes:**")
                    status_api = "✅ Processados" if st.session_state.get('dados_permanentes_processados', False) else "⏳ Pendentes"
                    st.write(f"📝 Manuais: {len([f for f in formularios_para_unidade if f in st.session_state.get('formularios_data', {})])}/{total_formularios_manual}")
                    st.write(f"🔄 Via API: {total_formularios_api} ({status_api})")

                    # === NOVA SEÇÃO: HISTÓRICO DO PROCESSAMENTO API ===
                    if st.session_state.get('dados_permanentes_processados', False):
                        with st.expander("📋 Detalhes do Processamento API"):
                            if 'historico_processamento_api' in st.session_state and st.session_state['historico_processamento_api']:
                                ultimo_processamento = st.session_state['historico_processamento_api'][-1]
                                
                                # Salva a última competência em uma chave separada
                                st.session_state['competencia_anterior_utilizada'] = ultimo_processamento['competencia_anterior_utilizada']

                                st.markdown("**Informações da Competência:**")
                                st.write(f"• **Competência selecionada:** {ultimo_processamento['competencia_selecionada']}")
                                st.write(f"• **Competência anterior utilizada:** {ultimo_processamento['competencia_anterior_utilizada']}")
                                st.write(f"• **Status:** {ultimo_processamento['status_competencia']}")
                                st.write(f"• **Processado em:** {ultimo_processamento['timestamp'].strftime('%d/%m/%Y às %H:%M')}")
                                
                                st.markdown("---")
                                
                                st.markdown("**Formulários processados:**")
                                for form in ultimo_processamento['formularios_processados']:
                                    st.write(f"✅ {form}")
                                
                                st.markdown("---")
                                
                                st.write(f"**Total de arquivos gerados:** {ultimo_processamento['total_arquivos']}")
                                
                                if ultimo_processamento['arquivos_gerados']:
                                    with st.expander("📁 Ver arquivos gerados"):
                                        for arquivo in ultimo_processamento['arquivos_gerados']:
                                            st.write(f"📄 {arquivo}")
                            else:
                                st.info("Histórico de processamento não disponível")

                st.markdown("---") # cria uma linha horizontal para separar as seções
                
                # Lista de formulários com status
                formularios_filtrados = [] # cria um formulario vazia
                for nome_formulario in formularios_para_unidade: # para cada formulario da lista
                    # Aplicar busca
                    if busca and busca.lower() not in nome_formulario.lower(): # se o usuário digitou algo na busca e esse texto não estiver contido no nome do formulário, ou seja, se o texto da busca não estiver no nome do formulário
                        continue # apenas continue, ou seja, não adiciona esse formulário à lista de formulários filtrados
                        
                    # Determinar status
                    if nome_formulario in st.session_state['formularios_data']: # se o nome do formulário estiver nos dados dos formulários preenchidos na memória, ou seja, se o usuário já preencheu esse formulário
                        status = "✅" # status é completo
                        status_text = "Completo"
                    else: # se não estiver nos dados dos formulários preenchidos na memória, ou seja, se o usuário ainda não preencheu esse formulário
                        status = "⏳" # status é pendente
                        status_text = "Pendente"
                    
                    # Aplicar filtro de status
                    if filtro_status == "Pendentes" and status != "⏳": # se o usuario seleciona a opção "Pendentes" e o status do formulário não for pendente, ou seja, se o status não for "⏳"
                        continue # continue, ou seja, não adiciona esse formulário à lista de formulários filtrados
                    elif filtro_status == "Completos" and status != "✅": # se o usuário seleciona a opção "Completos" e o status do formulário não for completo, ou seja, se o status não for "✅"
                        continue # continue
                    elif filtro_status == "Com Erro" and status != "❌": # agora se o usuário seleciona a opção "Com Erro" e o status do formulário não for erro, ou seja, se o status não for "❌"
                        continue # continue
                    # Não é sobre mostrar quem bate, e sim pular quem não bate
                        
                    formularios_filtrados.append((nome_formulario, status, status_text)) # por fim, adiciona o nome do formulário, 
                    #o status e o texto do status à lista de formulários filtrados, ou seja, a lista que será exibida na sidebar
                
                # Seleção do formulário ativo
                if 'formulario_ativo' not in st.session_state: # se não contem essa chave na memoria, ou seja, se o usuário ainda não selecionou nenhum formulário ativo
                    st.session_state['formulario_ativo'] = formularios_para_unidade[0] if formularios_para_unidade else None
                    # cria a chave 'formulario_ativo' no session_state e define o primeiro formulário da lista como ativo
                    # ou seja, o primeiro formulário que a unidade precisa preencher
                    # aqui ele vai criar a chave e definir como o primeiro formulario como o formualrio ativo para preencher
                
                st.markdown("**Selecione um formulário:**") # cria um texto
                
                for nome_formulario, status, status_text in formularios_filtrados: 
                    # para cada formulário filtrado, que contém o nome do formulário, o status e o texto do status
                    # Destaca o formulário ativo
                    if nome_formulario == st.session_state['formulario_ativo']: 
                    # se o nome do formulário for igual ao formulário ativo na memória
                        button_style = "🎯" #coloca na interface esse simbolo
                    else: #senão
                        button_style = "" # deixa vazio, ou seja, não coloca nada na interface
                    
                    if st.button(f"{status} {button_style} {nome_formulario}", key=f"btn_{nome_formulario}"):
                    # st.button() cria um botão, por padrão o botão quando criado possui o valor False
                    # o padrão do botão vai ser o status, ou seja o emoji, o emoji do ativo caso for o caso, e o nome do formulário
                    # e quando clicado ele passa a ser True, e a condição if é atendida
                    # se a condição if for atendida, ou seja, se o usuário clicar no botão
                        st.session_state['formulario_ativo'] = nome_formulario # o formulario passara a ser o formulario ativo, ou seja, o formulario que o usuário vai preencher
                        
                        st.rerun() # recarrega a página para atualizar a interface com o formulário selecionado

                st.markdown("---") # cria uma linha horizontal para separar as seções

                st.info("Os botões a seguir ficarão disponíveis conforme você for avançando no processo.")

                # Inicializa as chaves de controle se não existirem
                if 'calculo_agua_realizado' not in st.session_state:
                    st.session_state['calculo_agua_realizado'] = False

                # Inicializa a chave 'consolidar' se não existir
                if 'consolidar' not in st.session_state:
                    st.session_state['consolidar'] = False

                # Verifica se tudo está pronto para consolidar
                manuais_completos = len([f for f in formularios_para_unidade if f in st.session_state.get('formularios_data', {})]) == total_formularios_manual
                api_completa = not total_formularios_api or st.session_state.get('dados_permanentes_processados', False)
                todos_formularios_prontos = manuais_completos and api_completa

                # BOTÃO 1: Cálculo de Consumo de Água
                if st.button("💧 Realizar Cálculo de Água", disabled=not todos_formularios_prontos):
                    if todos_formularios_prontos:
                        try:
                            from config.constants import CAMINHO_BASE_AGUA
                            
                            resultado = realizar_calculo_agua_consolidado(
                                output_dir=OUTPUT_DIR,
                                competencia=competencia,
                                unidade=unidade,
                                caminho_base_agua=CAMINHO_BASE_AGUA
                            )
                            
                            # Se deu erro, mostra os erros (o sucesso já foi tratado na função)
                            if not resultado['sucesso'] and resultado['erros']:
                                st.error("❌ Erros encontrados durante o cálculo:")
                                for erro in resultado['erros']:
                                    st.error(f"• {erro}")
                                    
                        except Exception as e:
                            st.error(f"❌ Erro inesperado no cálculo de água: {str(e)}")
                # Após o rerun, exibe apenas o resultado salvo (se existir)
                if st.session_state.get('calculo_agua_realizado') and st.session_state.get('resultado_calculo_agua') is not None:
                    exibir_resultado_calculo_consolidado(st.session_state['resultado_calculo_agua'])

                # BOTÃO 2: Consolidar Todos (habilitado após cálculo de água)
                consolidar_habilitado = todos_formularios_prontos and st.session_state['calculo_agua_realizado']

                
                # Botão de consolidação na sidebar
                if st.button("🔄 Consolidar Todos", disabled=not consolidar_habilitado):
                    if consolidar_habilitado:
                # if st.button("🔄 Consolidar Todos", disabled=formularios_salvos != total_formularios): # cria um botão com o nome "Consolidar Todos"
                    # O botão só estará habilitado qaundo a quantidade de formularios salvo for o mesmo que o total disponivel
                    # ou seja, desabilitado enquanto a quantidade for diferente do total de formulários disponíveis para a unidade
                    # mas se quantidade for a mesma do total, o botão será habilitado
                    # se o usuário clicar no botão, ou seja, se a condição if for atendida
                        st.session_state['consolidar'] = True # cria uma chave 'consolidar' no session_state e define como True, ou seja, o usuário quer consolidar todos os formulários preenchidos
                        # Após st.success("Arquivo consolidado gerado com sucesso!")
                        st.rerun() # recarrega a página para atualizar a interface
                    else:
                        if not todos_formularios_prontos:
                            st.warning("Complete todos os formulários primeiro.")
                        elif not st.session_state['calculo_agua_realizado']:
                            st.warning("Realize o cálculo de água primeiro.")

                # BOTÃO 3: Enviar para KPIH (habilitado após consolidação)
                envio_habilitado = consolidar_habilitado and st.session_state['consolidar']

                # Adicione esta função no seu arquivo principal (antes da consolidação)
                def recarregar_dados_da_memoria():
                    """
                    Retorna os dados dos formulários que já estão na memória (session_state)
                    NÃO busca arquivos do disco - usa apenas o que já foi salvo na sessão
                    """
                    return st.session_state.get('formularios_data', {}).copy()

                def validar_consolidado_para_envio():
                    """
                    Valida se o arquivo consolidado está pronto para envio
                    Verifica se todas as ponderações estão preenchidas
                    """
                    # dados_formularios = st.session_state.get('formularios_data', {})
                    # st.info("🔄 Recarregando arquivos CSV atualizados do disco...")
                    dados_formularios = recarregar_dados_da_memoria()

                    # Atualiza o session_state com os dados recarregados
                    st.session_state['formularios_data'].update(dados_formularios)
                    
                    # Verifica cada formulário salvo
                    problemas_encontrados = []
                    
                    for nome_form, df in dados_formularios.items():
                            
                        # Verifica se há ponderações vazias em registros com quantidade > 0
                        if 'Ponderação' in df.columns and 'Quantidade' in df.columns:
                            df_com_dados = df[df['Quantidade'].astype(str) != "0"].copy()
                            
                            if not df_com_dados.empty:
                                ponderacoes_vazias = df_com_dados[
                                    (df_com_dados['Ponderação'].isna()) | 
                                    (df_com_dados['Ponderação'] == "") |
                                    (df_com_dados['Ponderação'].str.contains("API indisponível|Sem match", na=False))
                                ]
                                
                                if not ponderacoes_vazias.empty:
                                    problemas_encontrados.append({
                                        'formulario': nome_form,
                                        'registros_problematicos': len(ponderacoes_vazias)
                                    })
                    

                    return len(problemas_encontrados) == 0, problemas_encontrados
                
                consolidado_valido, problemas_ponderacao = validar_consolidado_para_envio()
                envio_habilitado = consolidar_habilitado and st.session_state['consolidar'] and consolidado_valido

                # Botão de envio para KPIH - só habilitado após consolidação
                # ============================================================================
                # SUBSTITUA A SEÇÃO DE ENVIO PARA KPIH NO SEU ARQUIVO PRINCIPAL
                # Localização: Por volta da linha 700 do documento 1
                # ============================================================================

                # Botão de envio para KPIH - só habilitado após consolidação
                if st.button("🚀 Enviar dados para KPIH", disabled=not st.session_state['consolidar']):
                    if envio_habilitado:
                        try:
                            # === SEÇÃO 1: EXECUTAR API DE CENTRO DE CUSTO ===
                            st.info("📡 Iniciando envio de mapeamento de centro de custo...")
                            
                            from api.api_centro_custo import consumir_api_unidade_especifica
                            
                            if 'unidade_id' not in st.session_state:
                                st.error("❌ ID da unidade não encontrado. Execute primeiro o processo de dados permanentes.")
                                st.stop()
                            
                            # Executa o envio do mapeamento de centro de custo
                            sucesso_centro_custo = consumir_api_unidade_especifica()

                            if not sucesso_centro_custo:
                                st.error("❌ Falha no envio do mapeamento de centro de custo")
                                st.stop()
                            
                            st.success("✅ Mapeamento de centro de custo enviado com sucesso!")
                            
                            # === PONDERAÇÃO ===
                            st.info("📡 Iniciando envio de mapeamento de ponderação...")
                            sucesso_ponderacao = de_para_ponderacao()
                            
                            if not sucesso_ponderacao:
                                st.error("❌ Falha no envio de ponderação")
                                st.stop()
                            
                            st.success("✅ Mapeamento de ponderação enviado com sucesso!")
                            
                            # === PRODUTO ===
                            st.info("📡 Iniciando envio de mapeamento de produtos...")
                            sucesso_produto = de_para_produto()
                            
                            if not sucesso_produto:
                                st.error("❌ Falha no envio de produtos")
                                st.stop()
                            
                            st.success("✅ Mapeamento de produtos enviado com sucesso!")
                            
                            # ============================================================
                            # === ENVIO DAS APIS COM DETECÇÃO DE ERROS PARCIAIS ===
                            # ============================================================
                            
                            st.divider()
                            st.subheader("📊 Enviando Dados para KPIH")
                            
                            # === ESTATÍSTICAS ===
                            st.info("📈 Enviando estatísticas...")
                            sucesso_estatisticas, dados_extras_estatisticas, analise_estatisticas = enviar_consolidado_para_api()

                            if not sucesso_estatisticas:
                                st.error("❌ Falha crítica no envio de estatísticas")
                                st.stop()
                            
                            # === PRODUÇÃO ===
                            st.info("📦 Enviando produção...")
                            sucesso_producao, dados_extras_producao = enviar_producao_para_api()
                            
                            if not sucesso_producao:
                                st.error("❌ Falha crítica no envio de produção")
                                st.stop()
                            
                            # ============================================================
                            # === ANÁLISE CONSOLIDADA DE ERROS ===
                            # ============================================================
                            
                            # Verifica se QUALQUER das APIs teve erros parciais
                            tem_erros_estatisticas = analise_estatisticas.get('parcial', False)
                            tem_erros_producao = dados_extras_producao.get('analise_envio_producao', {}).get('total_rejeitados', 0) > 0
                            
                            tem_erros_parciais = tem_erros_estatisticas or tem_erros_producao
                            
                            # ============================================================
                            # === REGISTRO NO BANCO ===
                            # ============================================================
                            
                            st.divider()
                            st.subheader("💾 Registrando no Sistema")
                            
                            # Combinar dados extras de ambas as APIs
                            dados_extras_completos = {
                                **dados_extras_estatisticas,
                                **dados_extras_producao,
                                'timestamp_registro_banco': datetime.datetime.now().isoformat()
                            }
                            
                            # Determinar status final
                            if tem_erros_parciais:
                                status_final = 'enviado_api_parcial'
                            else:
                                status_final = 'enviado_api_sucesso'
                            
                            # Obter dados da sessão
                            email_usuario = st.session_state.get('email_usuario')
                            unidade_usuario = st.session_state.get('unidade_usuario', 'Unidade_Desconhecida')
                            competencia_usuario = obter_competencia_usuario()
                            
                            # Registrar no banco
                            preenchimento_id = registrar_no_banco(
                                email_usuario=email_usuario,
                                unidade_usuario=unidade_usuario,
                                competencia_usuario=competencia_usuario,
                                dados_extras=dados_extras_completos,
                                status_envio=status_final
                            )
                            
                            if not preenchimento_id:
                                st.error("❌ Dados enviados para API, mas erro ao registrar no sistema local")
                                st.warning("Entre em contato com o suporte técnico")
                                st.stop()
                            
                            st.session_state['ultimo_preenchimento_id'] = preenchimento_id
                            
                            # ============================================================
                            # === DEFINE FLAGS PARA EXIBIÇÃO POSTERIOR ===
                            # ============================================================
                            
                            if tem_erros_parciais:
                                st.session_state['envio_teve_erros_parciais'] = True
                                st.session_state['mostrar_modal_feedback'] = False
                                st.info("⚠️ Envio concluído com ressalvas. Veja detalhes abaixo após recarregar...")
                            else:
                                st.session_state['envio_teve_erros_parciais'] = False
                                st.session_state['mostrar_modal_feedback'] = True
                                st.success("✅ Envio 100% concluído! Recarregando...")
                            
                            # Aguarda 2 segundos para o usuário ver a mensagem
                            import time
                            time.sleep(2)
                            
                            # Recarrega para exibir resultados salvos
                            st.rerun()
                                            
                        except ImportError as import_err:
                            st.error(f"❌ Erro ao importar módulos: {import_err}")
                            st.warning("Verifique se todos os arquivos estão no local correto")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao processar envio: {str(e)}")
                            st.exception(e)
                    
                    else:
                        # Mensagens de validação
                        if not todos_formularios_prontos:
                            st.warning("⚠️ Complete todos os formulários primeiro.")
                        elif not st.session_state['calculo_agua_realizado']:
                            st.warning("⚠️ Realize o cálculo de água primeiro.")
                        elif not st.session_state['consolidar']:
                            st.warning("⚠️ Consolide os dados primeiro.")
                        elif not consolidado_valido:
                            st.error("❌ Dados não podem ser enviados - ponderações em branco detectadas:")
                            for problema in problemas_ponderacao:
                                st.write(f"• {problema['formulario']}: {problema['registros_problematicos']} registro(s) com ponderação vazia")
                            st.info("💡 Volte aos formulários com problema e corrija as ponderações antes de enviar.")
                        
                        if 'unidade_id' not in st.session_state:
                            st.info("💡 Dica: Execute primeiro o processo de dados permanentes para configurar a unidade.")

                # ============================================================================
                # EXIBIÇÃO DE RESULTADOS SALVOS (APÓS RERUN)
                # Este bloco fica FORA do if st.button() e é executado sempre que a página carrega
                # ============================================================================

                # Verifica se há resultados de envio salvos no session_state
                if 'resultado_envio_estatisticas' in st.session_state or 'resultado_envio_producao' in st.session_state:
                    st.divider()
                    st.subheader("📊 Resultado do Envio")
                    
                    tem_algum_erro = False
                    
                    # === ESTATÍSTICAS ===
                    if 'resultado_envio_estatisticas' in st.session_state:
                        resultado_est = st.session_state['resultado_envio_estatisticas']
                        analise_est = resultado_est.get('analise', {})
                        
                        if analise_est.get('parcial', False):
                            tem_algum_erro = True
                            st.warning("⚠️ **ENVIO PARCIAL DE ESTATÍSTICAS**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("✅ Aceitos", analise_est.get('total_aceitos', 0))
                            with col2:
                                st.metric("❌ Rejeitados", analise_est.get('total_rejeitados', 0))
                            
                            erros_est = analise_est.get('erros_detalhados', [])
                            if erros_est:
                                with st.expander("❌ **VER ERROS DE ESTATÍSTICAS**", expanded=False):
                                    st.error(f"**{len(erros_est)} registro(s) rejeitado(s):**")
                                    
                                    for i, erro in enumerate(erros_est, 1):
                                        if isinstance(erro, dict):
                                            # 🔥 CORREÇÃO: Tenta várias chaves possíveis
                                            motivo = (
                                                erro.get('mensagem') or  # ← Formato português
                                                erro.get('message') or   # ← Formato inglês
                                                erro.get('erro') or      # ← Alternativa
                                                str(erro)                # ← Fallback
                                            )
                                            
                                            indice = erro.get('indice', '?')
                                            
                                            st.markdown(f"""
                                            **Registro #{i}:**
                                            - 📍 **Índice:** {indice}
                                            - ❌ **Motivo:** {motivo}
                                            """)
                                            
                                            if i < len(erros_est):
                                                st.divider()
                                        else:
                                            # Se não for dict, exibe como string
                                            st.markdown(f"""
                                            **Registro #{i}:**
                                            - ❌ **Motivo:** {str(erro)}
                                            """)
                                            
                                            if i < len(erros_est):
                                                st.divider()
                        else:
                            st.success("✅ Estatísticas enviadas com sucesso!")
                            st.success(f"📊 Total: {analise_est.get('total_aceitos', 0)} registros")
                    
                    # === PRODUÇÃO ===
                    if 'resultado_envio_producao' in st.session_state:
                        resultado_prod = st.session_state['resultado_envio_producao']
                        analise_prod = resultado_prod.get('analise', {})
                        
                        if analise_prod.get('parcial', False):
                            tem_algum_erro = True
                            st.warning("⚠️ **ENVIO PARCIAL DE PRODUÇÃO**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("✅ Aceitos", analise_prod.get('total_aceitos', 0))
                            with col2:
                                st.metric("❌ Rejeitados", analise_prod.get('total_rejeitados', 0))
                            
                            erros_prod = analise_prod.get('registros_com_erro', [])
                            if erros_prod:
                                with st.expander("❌ **VER ERROS DE PRODUÇÃO**", expanded=False):
                                    st.error(f"**{len(erros_prod)} registro(s) rejeitado(s):**")
                                    
                                    for i, erro in enumerate(erros_prod, 1):
                                        motivo = erro.get('motivo', 'Erro desconhecido')
                                        
                                        st.markdown(f"""
                                        **Registro #{i}:**
                                        - ❌ **Motivo:** {motivo}
                                        """)
                                        
                                        if i < len(erros_prod):
                                            st.divider()
                        else:
                            st.success("✅ Produção enviada com sucesso!")
                            st.success(f"📦 Total: {analise_prod.get('total_aceitos', 0)} registros")
                    
                    st.divider()
                    
                    # === INSTRUÇÕES E AÇÕES ===
                    if tem_algum_erro:
                        st.markdown("### 🔧 Como Resolver os Erros?")
    
                        # Cria duas colunas para as opções
                        col_opcao1, col_opcao2 = st.columns(2)
                        
                        with col_opcao1:
                            st.info("""
                            **📝 OPÇÃO 1: Corrigir Dados**
                            
                            Se você digitou algo errado ou o valor está incorreto, siga:
                            
                            1️⃣ Identifique qual formulário tem erro
                            
                            2️⃣ Clique no formulário na barra lateral
                            
                            3️⃣ Edite o valor problemático
                            
                            4️⃣ Salve o formulário novamente
                            
                            5️⃣ Refaça:
                            - Cálculo de Água 💧
                            - Consolidar 📊
                            - Enviar para KPIH 🚀
                            
                            💡 **Dica:** Os dados aceitos já estão no sistema. Corrija apenas os rejeitados.
                            """)
                        
                        with col_opcao2:
                            st.warning("""
                            **🎫 OPÇÃO 2: Abrir Ticket de Suporte**
                            
                            Se o dado está **correto** e o sistema deveria aceitar, solicite configuração:
                            
                            ✅ Quando usar:
                            - O centro de custo existe mas não foi cadastrado
                            - O produto/ponderação é válido mas não está configurado
                            - O sistema rejeitou um valor legítimo
                            
                            ❌ Não use para:
                            - Erros de digitação
                            - Valores incorretos que você pode corrigir
                            
                            📌 **Ao abrir o ticket, informe:**
                            - Centro de Custo rejeitado
                            - Produto/Ponderação rejeitado
                            - Quantidade informada
                            - Print do erro (se possível)
                            """)
                        
                    else:
                        # Se não há erros, mostra modal de feedback
                        st.session_state['mostrar_modal_feedback'] = True

                    # ============================================================================
                    # EXIBE O MODAL DE FEEDBACK (SOMENTE QUANDO SUCESSO TOTAL)
                    # ============================================================================
                    if st.session_state.get('mostrar_modal_feedback', False) and not tem_algum_erro:
                        feedback_fechado = modal_feedback_sucesso()
                        
                        if feedback_fechado:
                            st.session_state['mostrar_modal_feedback'] = False
                            
                            # Limpa resultados após fechar modal
                            if 'resultado_envio_estatisticas' in st.session_state:
                                del st.session_state['resultado_envio_estatisticas']
                            if 'resultado_envio_producao' in st.session_state:
                                del st.session_state['resultado_envio_producao']
                            
                            st.success("✅ Processo finalizado!")

                st.markdown("---")
                # Status visual dos botões (mantém como está)
                st.markdown("### 📊 Status do Processo")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if todos_formularios_prontos:
                        st.success("✅ Formulários")
                    else:
                        st.info("⏳ Formulários")

                with col2:
                    if st.session_state['calculo_agua_realizado']:
                        st.success("✅ Cálculo Água")
                    else:
                        st.info("⏳ Cálculo Água")

                with col3:
                    if st.session_state['consolidar']:
                        st.success("✅ Consolidado")
                    else:
                        st.info("⏳ Consolidado")

                adicionar_botao_ajuda_sidebar()

                # Na área principal do app, após a sidebar
                if st.session_state.get("abrir_modal_ajuda", False):
                    modal_ajuda()
                    # Reseta o estado após o modal ser renderizado
                    st.session_state.abrir_modal_ajuda = False

            # === ÁREA PRINCIPAL COM FORMULÁRIO ATIVO ===
            if st.session_state.get('formulario_ativo'): # se existir a chave 'formulario_ativo' no session_state, ou seja, se o usuário já selecionou um formulário ativo
                nome_formulario = st.session_state['formulario_ativo'] # pego o valor que está na chave que é o nome do formulário ativo
                # e armazeno ela na variavel nome_formulario

                # Header do formulário ativo
                col1, col2, col3 = st.columns([6, 1, 1]) # crio tres colunas
                # a primeira coluna terá 6 partes, a segunda e terceira terão 1 parte cada
                
                with col1: # com a coluna 1, eu vou colocar o nome do formulário ativo
                    # Status do formulário atual
                    if nome_formulario in st.session_state['formularios_data']: # se o nome do formulario for o valor armazenado na chave 'formularios_data'
                        st.success(f"✅ **{nome_formulario}** - Já preenchido") # crio uma mensagem de sucesso informando que o formulário já foi preenchido
                    else: # se não estiver na memoria
                        st.info(f"⏳ **{nome_formulario}** - Aguardando preenchimento") # cria uma mensagem informando que o formulário está aguardando preenchimento
                
                with col2: # com a coluna 2 
                    # Navegação - Anterior
                    indice_atual = formularios_para_unidade.index(nome_formulario)
                    # aqui eu busco o índice do formulário ativo na lista de formulários para a unidade
                    # ou seja, eu vejo qual é o índice do formulário ativo na lista de formulários
                    if indice_atual > 0: # se o índice atual for maior que 0, ou seja, se não for o primeiro formulário da lista
                        if st.button("⬅️ Ant."): # cria um botão com o nome "Anterior"
                            st.session_state['formulario_ativo'] = formularios_para_unidade[indice_atual - 1]
                        # se o usuário clicar no botão "Anterior"
                            # o formulário ativo passará a ser o formulário anterior na lista
                            st.rerun() # carrega a página para atualizar a interface com o formulário selecionado
                    else: # se não for maior que 0, ou seja, se for o primeiro formulário da lista
                        st.write("")  # a coluna ficará vazia, ou seja, não terá nada na coluna 2
                
                with col3: # com a coluna 3
                    # Navegação - Próximo
                    if indice_atual < len(formularios_para_unidade) - 1:
                        # se o índice atual for menor que o tamanho da lista de formulários menos 1, ou seja, se não for o último formulário da lista
                        if st.button("➡️ Próx."): # cria uma botão com o nome "Próximo"
                            st.session_state['formulario_ativo'] = formularios_para_unidade[indice_atual + 1]
                        # se o usuário clicar no botão "Próximo"
                            # o formulário ativo passará a ser o próximo formulário na lista
                            st.rerun() # carrega a página para atualizar a interface com o formulário selecionado
                    else: # se não for menor que o tamanho da lista de formulários menos 1, ou seja, se for o último formulário da lista
                        st.write("")  # a coluna ficará vazia, ou seja, não terá nada na coluna 3
                
                st.markdown("---") # cria uma linha horizontal para separar as seções
                
                # Renderiza o formulário selecionado
                modulo_nome = normalizar_nome_arquivo(nome_formulario) # aplico a função normalizar_nome_arquivo para garantir que o nome do formulário esteja no formato correto para ser usado como nome de módulo
                caminho = os.path.join(FORM_DIR, f"{modulo_nome}.py") # cria um caminho para o arquivo do formulário, juntando o diretório dos formulários com o nome do módulo e a extensão .py

                if os.path.exists(caminho): # se existir o caminho do arquivo do formulário, ou seja, se o arquivo do formulário existir na pasta dos formulários
                    try: # tenta carregar o arquivo
                        # Carrega o módulo
                        # eu faço isso pois preciso que os fomulario sejam carregados como modulos para que eles sejam executados dentro desse app
                        spec = importlib.util.spec_from_file_location(modulo_nome, caminho)
                        # A especificação de importação é um conjunto de instruções que diz ao Python:
                        # Esse é o módulo que eu quero importar, ele está nesse caminho, e aqui está como você deve carregá-lo.
                        modulo = importlib.util.module_from_spec(spec)
                        # Cria um objeto módulo vazio com base na especificação spec
                        # ouseja, cria o objeto módulo "vazio", pronto para receber o conteúdo do arquivo formulario
                        spec.loader.exec_module(modulo)
                        # Executa o arquivo .py e carrega o código Python real dentro do objeto modulo
                        # a diferente dos outros import
                        # é que esse a gente defino quando importar e de onde importar

                        # Verificar se o formulário já foi preenchido
                        formulario_ja_preenchido = nome_formulario in st.session_state['formularios_data']

                        if formulario_ja_preenchido:
                            # Mostrar dados já preenchidos                       
                            # Mostrar os dados salvos
                            with st.expander("👀 Ver dados preenchidos"):
                                df_salvo = st.session_state['formularios_data'][nome_formulario]
                                st.dataframe(df_salvo)
                            
                            # Opcional: botão para editar/repreenchr
                            if st.button("✏️ Editar este formulário"):
                                st.session_state[f'editando_{nome_formulario}'] = True  # ✅ Apenas marca como "editando"
                                st.rerun()
                                
                       
                        if not formulario_ja_preenchido or st.session_state.get(f'editando_{nome_formulario}', False):
        
                            # Se está editando, mostra uma mensagem
                            if st.session_state.get(f'editando_{nome_formulario}', False):
                                st.info("✏️ **Modo de Edição** - Os dados salvos foram carregados para edição")                 
                            # Cria um formulário individual
                            with st.form(key=f"form_{modulo_nome}"): #porque usar o st.form, sem ele toda vez que o usuario interagir com as inteface, se ja escolhendo alguma opção ou digitando algo, o codigo será processado a cada interação
                                # agora quando fazemos um formulario com o st.form toda vez que o usuario vai interagindo o stramalit salva na memoria dele, e depois do usuario dando um ok, clicando em algo, ele executa todo o codigos
                                
                                # Renderiza o formulário
                                # aqui eu chamo a função dos formulario, atraves do modulo e passo a competencia escolhida pelo usuario
                                # como argumento, possui a função tem um parametro
                                df_formulario = modulo.render_form(competencia)

                                # NOVA LÓGICA: Lista de formulários que precisam de validação antes de salvar
                                FORMULARIOS_COM_VALIDACAO = [
                                    f"% de Resíduos",
                                    "Consumo de Gases Medicinais (m³)",
                                    "% Atuação CME",
                                    f"% de Atuação SCIH/CCIH",
                                    f"% de Consumo Caldeira",
                                    f"% CONSUMO GERADOR",
                                    "Produção"
                                ]
                                
                                validation_key = f"validation_{nome_formulario}_{competencia}_{st.session_state.get('unidade_selecionada', '')}"
                                
                                # Determina se o botão salvar deve estar habilitado
                                botao_salvar_habilitado = True  # Por padrão, habilitado
                                mensagem_desabilitado = ""
                                
                                if nome_formulario in FORMULARIOS_COM_VALIDACAO:
                                    # Para formulário de resíduos, verifica se foi validado
                                    validation_state = st.session_state.get(validation_key, {})

                                    # Para PRODUCAO, verifica se há ponderações vazias
                                    if nome_formulario == "Produção":
                                        if validation_key not in st.session_state or not validation_state.get('calculado', False):
                                            botao_salvar_habilitado = False
                                            mensagem_desabilitado = "Clique em 'Verificar e Validar Ponderações' antes de salvar"
                                        elif validation_state.get('erro') == 'ponderacao_vazia':
                                            botao_salvar_habilitado = False
                                            problemas = validation_state.get('registros_problematicos', 0)
                                            mensagem_desabilitado = f"Corrija as {problemas} ponderações vazias antes de salvar"
                                        elif validation_state.get('valido'):
                                            botao_salvar_habilitado = True
                                    
                                    # Para outros formulários (mantém a lógica existente)
                                    else:
                                    
                                        if not validation_state.get('calculado', False):
                                            # Se não foi calculado ainda
                                            botao_salvar_habilitado = False
                                            mensagem_desabilitado = "Clique em 'Calcular' antes de salvar"
                                        elif not validation_state.get('valido', False):
                                            # Se foi calculado mas tem erros
                                            botao_salvar_habilitado = False
                                            mensagem_desabilitado = "Corrija os erros antes de salvar"
                                    
                                # Botões do formulário
                                col1, col2, col3 = st.columns([3, 1, 2]) # crio três colunas com tamanhos iguais, cada recebe 2 partes iguais

                                with col1: # com a coluna 1 
                                    # Mostra mensagem explicativa se o botão estiver desabilitado
                                    if not botao_salvar_habilitado and mensagem_desabilitado:
                                        st.info(f"💡 {mensagem_desabilitado}")
                                    
                                    submitted = st.form_submit_button(
                                        f"💾 Salvar {nome_formulario}", 
                                        type="primary", 
                                        use_container_width=True,
                                        disabled=not botao_salvar_habilitado
                                    
        )
                                    # crio um botão, como o nome salvar
                                    # dentro de um with st.form(...), você coloca todos os componentes do formulário (inputs, seletores, caixas de texto etc.)
                                    # O st.form_submit_button() é o botão responsável por "enviar" os dados de um formulário criado com st.form no Streamlit
                                    # use_container_width=True é uma paremetro dentro do streamli para que o botão ocupe toda a largura disponível do "container" onde ele está
                                
                                with col2:
                                    if st.session_state.get(f'editando_{nome_formulario}', False):
                                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                            if f'editando_{nome_formulario}' in st.session_state:
                                                del st.session_state[f'editando_{nome_formulario}']
                                            # Limpa também o estado de validação se existir
                                            if validation_key in st.session_state:
                                                del st.session_state[validation_key]
                                            st.rerun()

                                # with col3:
                                #     if st.form_submit_button("🗑️ Limpar Formulário", use_container_width=True):
                                #         # Apaga os dados salvos do formulário
                                #         if nome_formulario in st.session_state['formularios_data']:
                                #             del st.session_state['formularios_data'][nome_formulario]
                                        
                                #         # Sai do modo edição (senão ele recarrega os dados antigos)
                                #         if f'editando_{nome_formulario}' in st.session_state:
                                #             del st.session_state[f'editando_{nome_formulario}']

                                #         # Apaga os valores dos widgets do formulário
                                #         for key in list(st.session_state.keys()):
                                #             if key.startswith(f"{nome_formulario}_"):  # todas as chaves do formulário
                                #                 del st.session_state[key]

                                #          # Apaga também o dicionário principal usado no render_form
                                #         form_key = f"form_data_{nome_formulario}_{competencia}_{st.session_state.get('unidade_selecionada','')}"
                                #         if form_key in st.session_state:
                                #             del st.session_state[form_key]

                                #         st.warning("Formulário limpo!")
                                #         time.sleep(1)
                                #         st.rerun()
                            
                                if submitted: # se clicar no botão salvar
                                    if not df_formulario.empty and "Quantidade" in df_formulario.columns:
                                    # e se o formulario não for vazio e possui a coluna quantidade no formulario
                                        valido, resultado = validar_quantidade_ou_tempo(df_formulario, "Quantidade")
                                        # aplico a função validar_quantidade_ou_tempo
                                        # onde eu passo como argumento o dataframe e o nome quantidade
                                        if not valido: # se não trazer o True, quer dizer que possui valor invalido
                                            st.warning("⚠️ Valores inválidos na coluna Quantidade:") # aparece a mensagem
                                            for idx, val in resultado.items(): # para cada indice e valor do dataframe, percorre para saber qual é o a linha que está com o valor invalido
                                                st.write(f"Linha {idx + 2}: valor '{val}' inválido") 
                                            # retorna uma mesnagem informando a linha e o valor
                                        else: # agora s enão valor invalido
                                            df_formulario = resultado # o resultado com a coluna converrtido é retornado para a variavel df_formulario
                                            # Remove as linhas que adicionam colunas extras
                                            # df_formulario["Unidade"] = unidade
                                            # df_formulario["Formulário"] = nome_formulario
                                            
                                            st.session_state['formularios_data'][nome_formulario] = df_formulario
                                            # aqui eu adiciono ao dicionário que estava vazio uma outra chave que vai correpoder ao df_formulario
                                            # exemplo:
                                            # formularios_data = {"formulario1": {"valor": 1000,"data": "22/03/2025"}, "formulario2": {"valor": 5000,"data": "23/03/2025"}}

                                            # ✅ ADICIONE ESTAS LINHAS:
                                            st.session_state['consolidar'] = False
                                            st.session_state['calculo_agua_realizado'] = False
                                            # st.info("⚠️ Dados atualizados - você precisará consolidar e calcular água novamente")
                                            
                                            if f'editando_{nome_formulario}' in st.session_state:
                                                del st.session_state[f'editando_{nome_formulario}']

                                            # Remove também qualquer chave de validação se existir
                                            validation_key = f"validation_{nome_formulario}_{competencia}_{st.session_state.get('unidade_selecionada', '')}"
                                            if validation_key in st.session_state:
                                                del st.session_state[validation_key]
                                            
                                            arquivo_individual = os.path.join(
                                                OUTPUT_DIR, # esse é o cmainho do diretorio mais a pasta formulario_preenchidos
                                                f"{nome_formulario}_{competencia}.csv".replace("/", "-").replace(" ", "_")
                                                # e ai eu faço um join com o nome do formulario + a completencia
                                                # .replace("/", "-").replace(" ", "_") no nome do arquivo é para garantir que o nome do arquivo seja válido e seguro para o sistema de arquivos do computador
                                                # e no final teremos no varaivel o caminho completo da pasta mais o nome do arquivo
                                            )
                                            
                                            # Salva o arquivo
                                            try: # vou tentar...
                                                # Substitui ponto por vírgula na coluna Quantidade
                                                # if 'Quantidade' in df_formulario.columns: # se existir a coluna quantidade no dataframe
                                                #     df_formulario['Quantidade'] = df_formulario['Quantidade'].astype(str).str.replace('.', ',')
                                                df_formulario = df_formulario[df_formulario['Quantidade'] != "0"].copy()
                                                # substituo ponto por virgula
                                                df_formulario.to_csv(arquivo_individual, index=False, encoding="utf-8-sig", sep=";")
                                                # converto o data frame para csv csem o index com o separador ;
                                                # e informo o caminho que sera salvo o arquivo
                                                st.success(f"✅ {nome_formulario} salvo com sucesso!") # mensagem para confirmar que o arquivo foi salvo 
                                                st.info(f"📁 Arquivo salvo: {arquivo_individual}") # depois informo aode foi salvo
                                                
                                                # IMPORTANTE: Limpa a flag consolidação aqui
                                                st.session_state['consolidar'] = False

                                                # Auto-navegar para o próximo formulário pendente
                                                proximo_pendente = None # crio uma variavel
                                                for form in formularios_para_unidade: # para cada formulario que está no formularios_para_unidade
                                                    if form not in st.session_state['formularios_data']: # se o formulario nao estiver na memoria do streamlit
                                                        # ele armazena o nome do formulario na varaivel proximo_pendente
                                                        proximo_pendente = form
                                                        break # e sai do loop
                                                
                                                if proximo_pendente: # se existir valor aqui, ou seja se for TRUE
                                                    st.info(f"⏭️ Avançando para: {proximo_pendente}") # mostra essa mensagem, que está vanaçando para o proximo formulario
                                                    
                                                    # Configura para o próximo render
                                                    st.session_state['formulario_ativo'] = proximo_pendente
                                                    
                                                    # NOVA ABORDAGEM: Simular clique no botão flutuante
                                                    html("""
                                                        <script>
                                                        function scrollToTop() {
                                                            // Primeiro tenta encontrar o elemento âncora
                                                            const elemento = parent.document.getElementById('inicio-formularios');
                                                            
                                                            if (elemento) {
                                                                elemento.scrollIntoView({
                                                                    behavior: 'smooth',
                                                                    block: 'start'
                                                                });
                                                            } else {
                                                                // Fallback: scroll para o topo da página
                                                                parent.window.scrollTo({
                                                                    top: 0,
                                                                    behavior: 'smooth'
                                                                });
                                                            }
                                                        }
                                                        
                                                        // Executa após um pequeno delay
                                                        setTimeout(scrollToTop, 500);
                                                        </script>
                                                        """, height=0)
                                                    
                                                    time.sleep(1)  # Pausa visual
                                                    st.rerun()
                                                                                                    
                                                else: # se não, ou seja se não contiver um proximo formulario
                                                    st.success("🎉 Todos os formulários foram preenchidos!") # essa mensagem é exibida

                                            #o if não daria erro, o erro mais provavel seria em salvar o arquivo, por isso é o erro que defini        
                                            except Exception as save_error: 
                                                st.error(f"❌ Erro ao salvar arquivo: {str(save_error)}")
                                    else: # agora se o data frame está vazio ou não possui a coluna de quantidade
                                        # vai dar esse erro
                                        st.warning(f"⚠️ Formulário retornou dados vazios ou com estrutura incorreta.")
                            
                    except Exception as e: # aqui é o erro que vai dar quando tentar carregar o formulario
                        # ou melhor, carregar o modulo, importar e executar
                        st.error(f"❌ Erro ao carregar formulário {nome_formulario}: {str(e)}")
                else: # se o arquivo do formulario não existir, vai dar esse erro
                    st.error(f"❌ Formulário não encontrado: {caminho}")

            def recarregar_dados_processados(output_dir, competencia):
                """
                Recarrega os dados dos arquivos processados para garantir que a consolidação 
                use as versões mais atualizadas
                """
                dados_recarregados = {}
                
                # Lista de arquivos para verificar
                arquivos_para_verificar = [
                    f"Area_Criticidade_API_{competencia}.csv",
                    # Adicione outros arquivos que possam ter sido processados
                ]
                
                for arquivo in arquivos_para_verificar:
                    caminho_arquivo = os.path.join(output_dir, arquivo)
                    if os.path.exists(caminho_arquivo):
                        try:
                            df = pd.read_csv(caminho_arquivo, sep=';')
                            # Mapeia o nome do arquivo para o nome usado na session_state
                            if 'Area_Criticidade_API' in arquivo:
                                nome_formulario = 'Area_Criticidade_API'
                            # Adicione outros mapeamentos conforme necessário
                            else:
                                nome_formulario = arquivo.replace('.csv', '').replace(f'_{competencia}', '')
                            
                            dados_recarregados[nome_formulario] = df
                            
                        except Exception as e:
                            st.warning(f"Erro ao recarregar {arquivo}: {e}")
                
                return dados_recarregados
            
            st.markdown("---") # cria uma linha 

            # === CONSOLIDAÇÃO (se solicitada) ===
            if st.session_state.get('consolidar', False): # ele verifica se existi esse consolidar na memoria
                from utils.tratativa_criticidade_api import tratativa_criticidade_api

                # # *** PASSO 1: REMOVER VERSÃO ANTIGA DO SESSION_STATE ***
                # # Remove a versão desatualizada ANTES da tratativa
                # if 'Area_Criticidade_API' in st.session_state.get('formularios_data', {}):
                #     del st.session_state['formularios_data']['Area_Criticidade_API']
                

                # Cole isso no seu arquivo principal, ANTES da linha:
                # debig para ver os formulario que traz da api e quais estão sendo salvo na memoria do streamlit

                st.markdown("### 🔍 DEBUG - Formulários na Memória")
                formularios_data = st.session_state.get('formularios_data', {})

                st.write(f"**Total:** {len(formularios_data)} formulários")

                for nome in formularios_data.keys():
                    st.write(f"- `{nome}`")

                st.markdown("---")
                # PASSO 2: Executar tratativa de criticidade
                resultado_tratativa_criticidade_api = tratativa_criticidade_api(OUTPUT_DIR, competencia_normalizada)
                
                # if resultado_tratativa_criticidade_api:
                #     st.info("✅ Tratativa de criticidade concluída")

                #     # PASSO 3: RECARREGAR APENAS A VERSÃO ATUALIZADA
                #     arquivo_criticidade = os.path.join(OUTPUT_DIR, f"Area_Criticidade_API_{competencia_normalizada}.csv")

                #     if os.path.exists(arquivo_criticidade):
                #         try:
                #             df_criticidade_atualizado = pd.read_csv(arquivo_criticidade, sep=';')
                #             # Valida que a ponderação foi realmente atualizada
                #             ponderacoes_preenchidas = df_criticidade_atualizado['Ponderação'].notna().sum()
                            
                #             if ponderacoes_preenchidas > 0:
                #                 # Adiciona APENAS a versão atualizada ao session_state
                #                 st.session_state['formularios_data']['Area_Criticidade_API'] = df_criticidade_atualizado
                #             else:
                #                 st.warning("⚠️ Arquivo de criticidade não possui ponderações atualizadas")
                #         except Exception as e:
                #             st.error(f"Erro ao recarregar dados de criticidade: {e}")

                #     else:
                #         st.warning(f"⚠️ Arquivo de criticidade não encontrado: {arquivo_criticidade}")

                    
                if st.session_state.get('consolidar', False) and resultado_tratativa_criticidade_api:
                    # se a condição for atendida ou seja se for TRUE:
                    st.markdown("---") # cria uma linha 
                    st.markdown("## 📊 Consolidação Final") # cria esse texto
                    
                    #NOVA VALIDAÇÃO - adicionar antes do if st.session_state['formularios_data']:
                    dados_formularios = st.session_state.get('formularios_data', {})

                    # Verifica pendências - NOVA LÓGICA incluindo cálculo de água
                    formularios_manuais_pendentes = [f for f in formularios_para_unidade if f not in dados_formularios]
                    api_pendente = (
                        len(formularios_permanentes_para_API) > 0 and 
                        not st.session_state.get('dados_permanentes_processados', False)
                    )
                    calculo_agua_pendente = not st.session_state.get('calculo_agua_realizado', False)
                    
                    # Verificações em ordem de prioridade
                    if formularios_manuais_pendentes:
                        st.warning(f"⚠️ Formulários manuais pendentes: {', '.join(formularios_manuais_pendentes)}")
                        st.session_state['consolidar'] = False
                        st.info("Complete todos os formulários antes de consolidar.")
                        
                    elif api_pendente:
                        st.warning("⚠️ Dados permanentes ainda não foram processados")
                        st.session_state['consolidar'] = False
                        st.info("Processe os dados permanentes antes de consolidar.")
                        
                    elif calculo_agua_pendente:
                        st.warning("⚠️ Cálculo de água ainda não foi realizado")
                        st.session_state['consolidar'] = False
                        st.info("Realize o cálculo de consumo de água antes de consolidar.")
                        
                    elif dados_formularios:
                        st.success("✅ Todos os pré-requisitos foram atendidos. Iniciando consolidação...")
                        
                        # CONSOLIDAR POR ORDEM DE PRIORIDADE
                        dfs_para_consolidar = []
                        formularios_consolidados = []  # Para rastreamento

                        # === NOVA LÓGICA: Identificar origem dos dados de criticidade ===
                        dados_criticidade_vieram_da_api = 'Area_Criticidade_API' in st.session_state['formularios_data']

                        # Lista de formulários de criticidade MANUAIS
                        formularios_criticidade_manuais = [
                            "Área (m²) x Nível de Criticidade (Área Crítica - I)",
                            "Área (m²) x Nível de Criticidade (Área Semi Crítica)",
                            "Área (m²) x Nível de Criticidade (Área Não Crítica - I)"
                        ]

                        # === REGRA 1: Se vieram da API, ignorar os manuais ===
                        formularios_a_ignorar = ["Produção", "Area_Criticidade_API", "Nº de Colaboradores (Médicos + Não Médicos)"]  # Sempre ignora Produção e criticidade para usar os 3 filtrados

                        if dados_criticidade_vieram_da_api:
                            st.info("🔄 Dados de criticidade vieram da API - usando as 3 versões filtradas")
                        else:
                            st.info("✏️ Dados de criticidade preenchidos manualmente - usando as 3 versões")

                        # === PROCESSAMENTO DOS FORMULÁRIOS ===
                        st.markdown("#### 📋 Processando formulários...")

                        for nome, df in st.session_state['formularios_data'].items():
                            # Pula os formulários da lista de ignorados
                            if nome in formularios_a_ignorar:
                                st.info(f"  ⏭️ Pulando: {nome}")
                                continue
                            
                            df_limpo = df.copy()
                            df_limpo = df_limpo[df_limpo['Quantidade'].astype(str) != "0"].copy()
                            
                            if not df_limpo.empty:
                                dfs_para_consolidar.append(df_limpo)
                                formularios_consolidados.append(nome)
                                st.success(f"  ✅ Adicionado: {nome} ({len(df_limpo)} registros)")
                            else:
                                st.warning(f"  ⚠️ Sem dados válidos: {nome}")

                        # === ADICIONA CÁLCULO DE ÁGUA ===
                        st.markdown("#### 💧 Processando cálculo de água...")

                        if st.session_state.get('resultado_calculo_agua') is not None:
                            df_agua = st.session_state['resultado_calculo_agua'].copy()
                            df_agua = df_agua[df_agua['Quantidade'] != 0].copy()
                            
                            if not df_agua.empty:
                                df_agua['Quantidade'] = df_agua['Quantidade'].apply(lambda x: f"{x:.2f}".replace(".", ","))
                                dfs_para_consolidar.append(df_agua)
                                formularios_consolidados.append("Consumo_Agua")
                                st.success(f"  ✅ Água: {len(df_agua)} registros")
                            else:
                                st.warning("  ⚠️ Dados de água sem registros válidos")

                        if st.session_state.get('df_agua_quente_final') is not None:
                            df_agua_quente_final = st.session_state['df_agua_quente_final'].copy()
                            df_agua_quente_final = df_agua_quente_final[df_agua_quente_final['Quantidade'] != 0].copy()
                            
                            if not df_agua_quente_final.empty:
                                df_agua_quente_final['Quantidade'] = df_agua_quente_final['Quantidade'].apply(lambda x: f"{x:.2f}".replace(".", ","))
                                dfs_para_consolidar.append(df_agua_quente_final)
                                formularios_consolidados.append("Consumo_Agua_Quente")
                                st.success(f"  ✅ Água Quente: {len(df_agua_quente_final)} registros")
                            else:
                                st.warning("  ⚠️ Dados de água quente sem registros válidos")

                        # === CONSOLIDAÇÃO FINAL ===
                        st.markdown("---")
                        st.markdown("#### 🎯 Gerando arquivo consolidado...")

                        if dfs_para_consolidar:
                            df_final = pd.concat(dfs_para_consolidar, ignore_index=True)
                            
                            # Caminho para salvar
                            arquivo_consolidado = os.path.join(
                                OUTPUT_DIR, 
                                f"CONSOLIDADO_{unidade}_{competencia}.csv".replace("/", "-").replace(" ", "_")
                            )
                            
                            try:
                                # Filtros finais
                                tamanho_antes_filtro = len(df_final)
                                df_final = df_final[df_final['Quantidade'].astype(str) != "0"].copy()
                                df_final = df_final[df_final['Ponderação'] != "Nº de Colaboradores (Médicos + Não Médicos)"]
                                tamanho_depois_filtro = len(df_final)
                                
                                if tamanho_antes_filtro != tamanho_depois_filtro:
                                    st.info(f"🧹 Filtros aplicados: {tamanho_antes_filtro - tamanho_depois_filtro} registros removidos")
                                
                                # Salva o arquivo
                                df_final.to_csv(arquivo_consolidado, index=False, encoding="utf-8-sig", sep=";")
                                
                                st.success("✅ Consolidação concluída com sucesso!")
                                
                                # === RESUMO DETALHADO ===
                                st.markdown("### 📈 Resumo da Consolidação")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Formulários", len(formularios_consolidados))
                                with col2:
                                    st.metric("Registros", len(df_final))
                                with col3:
                                    duplicatas = df_final.duplicated().sum()
                                    if duplicatas > 0:
                                        st.metric("Duplicatas", duplicatas, delta="⚠️")
                                    else:
                                        st.metric("Duplicatas", 0, delta="✅")
                                with col4:
                                    origem_criticidade = "API" if dados_criticidade_vieram_da_api else "Manual"
                                    st.metric("Criticidade", origem_criticidade)
                                
                                st.info(f"📁 Arquivo salvo: {os.path.basename(arquivo_consolidado)}")
                                
                                # Lista dos formulários consolidados
                                with st.expander("📋 Formulários consolidados neste arquivo"):
                                    for i, form in enumerate(formularios_consolidados, 1):
                                        st.write(f"{i}. {form}")
                                
                                # Preview (opcional, colapsado por padrão)
                                with st.expander("👀 Ver preview dos dados"):
                                    st.dataframe(df_final.head(20))
                                
                            except Exception as consolidate_error:
                                st.error(f"❌ Erro ao salvar arquivo consolidado: {str(consolidate_error)}")
                                st.exception(consolidate_error)
                                st.session_state['consolidar'] = False

                        else:
                            st.error("❌ Nenhum dado disponível para consolidação")
                            st.session_state['consolidar'] = False
                    
                    # === SEÇÃO DE DOWNLOAD PROFISSIONAL ===
                    st.markdown("---")
                    st.markdown("### 📥 Download dos Resultados")

                    col_info, col_downloads = st.columns([2, 3])

                    with col_info:
                        st.info("""
                        **📦 Pacote Completo (ZIP)**
                        - Todos os formulários organizados
                        - Arquivo consolidado
                        - Dados permanentes da API
                        - Cálculos realizados
                        - Arquivo README com instruções
                        
                        **📄 Consolidado Individual**
                        - Arquivo pronto para envio ao KPIH
                        - Todos os dados em um único CSV
                        """)

                    with col_downloads:
                        # Botão 1: Download do Consolidado
                        st.markdown("#### 🎯 Arquivo Principal")
                        
                        try:
                            with open(arquivo_consolidado, 'rb') as file:
                                dados_consolidado = file.read()
                                tamanho_consolidado = get_tamanho_legivel(len(dados_consolidado))
                                
                                st.download_button(
                                    label=f"📄 Baixar Consolidado ({tamanho_consolidado})",
                                    data=dados_consolidado,
                                    file_name=os.path.basename(arquivo_consolidado),
                                    mime="text/csv",
                                    use_container_width=True,
                                    help="Arquivo pronto para envio ao KPIH"
                                )
                        except Exception as e:
                            st.error(f"Erro ao preparar consolidado: {e}")
                        
                        st.markdown("#### 📦 Pacote Completo")
                        
                        # Botão 2: Download do ZIP
                        try:
                            zip_buffer, qtd_arquivos = criar_zip_formularios(
                                OUTPUT_DIR, 
                                competencia_normalizada, 
                                unidade
                            )
                            
                            tamanho_zip = get_tamanho_legivel(len(zip_buffer.getvalue()))
                            nome_zip = f"Relatorio_Coleta_{unidade}_{competencia_normalizada}.zip"
                            
                            st.download_button(
                                label=f"📦 Baixar Tudo ({qtd_arquivos} arquivos • {tamanho_zip})",
                                data=zip_buffer,
                                file_name=nome_zip,
                                mime="application/zip",
                                use_container_width=True,
                                type="primary",
                                help="Backup completo com todos os formulários organizados"
                            )
                            
                            st.success(f"✅ {qtd_arquivos} arquivos prontos para download")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao criar pacote ZIP: {e}")
                            st.info("💡 Você ainda pode baixar o consolidado acima")

                    st.markdown("---")

                    # Dica profissional
                    st.info("💡 **Dica:** Baixe o pacote completo (ZIP) como backup. Use o consolidado para envio ao sistema.")

                else:
                    st.warning("⚠️ Nenhum formulário foi salvo ainda.")
                    st.session_state['consolidar'] = False

    else: # se não possui nenhum formulario para aquela unidade vai aparecer essa mensagem
        st.info("ℹ️ Nenhum formulário aplicável para a unidade selecionada com as configurações atuais.")
    st.markdown('<div id="final-formularios"></div>', unsafe_allow_html=True)