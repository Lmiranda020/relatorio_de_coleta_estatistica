import streamlit as st
import pandas as pd
import re
import os
import importlib.util
import time
from PIL import Image
from pathlib import Path

MAP_PATH = "formularios X unidades.xlsx"
FORM_DIR = "formularios"

# Função para obter o caminho do desktop do usuário
def get_desktop_path():
    """
    Retorna o caminho do desktop do usuário atual
    """
    try:
        # Windows
        if os.name == 'nt':
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        # macOS e Linux
        else:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Verifica se o diretório existe
        if not os.path.exists(desktop):
            # Tenta alternativas para Linux
            desktop = os.path.join(os.path.expanduser('~'), 'Área de Trabalho')
            if not os.path.exists(desktop):
                desktop = os.path.expanduser('~')  # Fallback para home
        
        return desktop
    except Exception as e:
        st.error(f"Erro ao obter caminho do desktop: {str(e)}")
        return os.path.expanduser('~')  # Fallback para home

# Cria o diretório no desktop do usuário
desktop_path = get_desktop_path()
OUTPUT_DIR = os.path.join(desktop_path, "formularios_preenchidos")

# Cria a pasta se não existir
# Mensagem temporária de sucesso ao criar/encontrar a pasta
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    msg = st.success(f"✅ Pasta criada/encontrada em: {OUTPUT_DIR}")
    # Aguarda 3 segundos e remove a mensagem
    time.sleep(3)
    msg.empty()
except Exception as e:
    st.error(f"❌ Erro ao criar pasta no desktop: {str(e)}")
    # Fallback para pasta local
    OUTPUT_DIR = "formularios_preenchidos"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    st.warning(f"⚠️ Usando pasta local como alternativa: {OUTPUT_DIR}")

competencias = [
    "jan/2025", "fev/2025", "mar/2025", "abr/2025",
    "mai/2025", "jun/2025", "jul/2025", "ago/2025",
    "set/2025", "out/2025", "nov/2025", "dez/2025",
    "jan/2026", "fev/2026", "mar/2026", "abr/2026",
    "mai/2026", "jun/2026", "jul/2026", "ago/2026",
    "set/2026", "out/2026", "nov/2026", "dez/2026"
]

# Caminhos das imagens
imagem_cejam = r"C:\Users\larissa.miranda\Desktop\Python\relatorio_de_coleta_estatistica\imagens\logo cejam.png"
imagem_sus = r"C:\Users\larissa.miranda\Desktop\Python\relatorio_de_coleta_estatistica\imagens\logo sus.png"

# Cria 3 colunas: esquerda (logo CEJAM), centro (título), direita (logo SUS)
col_esq, col_centro, col_dir = st.columns([1, 6, 1])

# Logo CEJAM
with col_esq:
    if os.path.exists(imagem_cejam):
        st.image(Image.open(imagem_cejam), width=100)
    else:
        st.warning("Logo CEJAM não encontrada.")

# Título
with col_centro:
    st.markdown(
        "<h1 style='text-align: center;'>Relatório de Coleta</h1>",
        unsafe_allow_html=True
    )

# Logo SUS
with col_dir:
    if os.path.exists(imagem_sus):
        st.image(Image.open(imagem_sus), width=100)
    else:
        st.warning("Logo SUS não encontrada.")

# Aqui vai o conteúdo principal do app
st.write("Explicar sobre o aplicativo e como ele funciona. Colocar o link de um manual ou vídeo explicativo.")

# Mostra onde os arquivos serão salvos
msg1 = st.info(f"📁 **Arquivos serão salvos em:** {OUTPUT_DIR}")
# Aguarda 3 segundos e remove a mensagem
time.sleep(3)
msg1.empty()

df_mapeamento = pd.read_excel(MAP_PATH)
col_formulario = df_mapeamento.columns[0]
col_permanente = "Permanente?"

assert col_permanente in df_mapeamento.columns, "'Permanente?' precisa estar na planilha"

# Seção de seleção (fora das abas)
st.markdown("---")
st.markdown("## 📋 Configurações")

col1, col2 = st.columns(2)

with col1:
    unidade = st.selectbox("Selecione sua unidade:", df_mapeamento.columns[2:])

with col2:
    competencia = st.selectbox("Selecione a competência:", competencias)

# Armazena a unidade selecionada no session_state para os formulários
if unidade:
    st.session_state['unidade_selecionada'] = unidade

alteracao_permanente = st.radio(
    "Há alguma alteração nos dados permanentes este mês?",
    ["Não", "Sim"],
    index=0
)

formularios_para_unidade = []

for i, row in df_mapeamento.iterrows():
    nome_formulario = row[col_formulario]
    eh_permanente = row[col_permanente] == True
    aplicavel = row[unidade] == True

    if aplicavel:
        if not eh_permanente:
            formularios_para_unidade.append(nome_formulario)
        elif eh_permanente and alteracao_permanente == "Sim":
            formularios_para_unidade.append(nome_formulario)

def normalizar_nome_arquivo(nome_formulario):
    """
    Converte o nome do formulário para o nome do arquivo Python
    """
    # Remove caracteres especiais e converte para minúsculas
    nome_normalizado = nome_formulario.lower()
    
    # Substitui espaços e caracteres especiais por underscores
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
    
    # Remove caracteres não alfanuméricos (exceto underscores)
    import re
    nome_normalizado = re.sub(r'[^\w]', '_', nome_normalizado)
    
    # Remove underscores duplicados
    nome_normalizado = re.sub(r'_+', '_', nome_normalizado)
    
    # Remove underscores no início e fim
    nome_normalizado = nome_normalizado.strip('_')
    
    return nome_normalizado

def validar_quantidade_ou_tempo(df, coluna="Quantidade"):
    quant_str = df[coluna].fillna("").astype(str).str.strip()

    # Regex para validar formato HH:MM:SS (24h)
    padrao_tempo = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")

    def eh_valido(valor):
        if valor == "":
            return False
        if padrao_tempo.match(valor):
            return True
        try:
            # Tenta converter número com vírgula ou ponto
            float(valor.replace(",", "."))
            return True
        except:
            return False

    validos = quant_str.apply(eh_valido)

    if not validos.all():
        invalidos = df.loc[~validos, coluna]
        return False, invalidos
    else:
        # Converte os valores válidos
        def converte_valor(v):
            if padrao_tempo.match(v):
                return v  # mantém string do tempo
            num = float(v.replace(",", "."))
            # Retorna como int se for inteiro, senão float
            return int(num) if num.is_integer() else num

        df[coluna] = quant_str.apply(converte_valor)
        return True, df


# Inicializa o armazenamento dos dados dos formulários no session_state
if 'formularios_data' not in st.session_state:
    st.session_state['formularios_data'] = {}

# Só mostra as abas se há formulários para mostrar
if formularios_para_unidade:
    st.markdown("---")
    st.markdown("## 📝 Formulários")
    
    # Cria as abas
    tabs = st.tabs([f"📋 {nome}" for nome in formularios_para_unidade])
    
    # Para cada aba, renderiza o formulário correspondente
    for i, (tab, nome_formulario) in enumerate(zip(tabs, formularios_para_unidade)):
        with tab:
            # Usa a função de normalização
            modulo_nome = normalizar_nome_arquivo(nome_formulario)
            caminho = os.path.join(FORM_DIR, f"{modulo_nome}.py")

            if os.path.exists(caminho):
                try:
                    # Carrega o módulo
                    spec = importlib.util.spec_from_file_location(modulo_nome, caminho)
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)

                    # Cria um formulário individual para cada aba
                    with st.form(key=f"form_{i}_{modulo_nome}"):
                        st.markdown(f"### {nome_formulario}")
                        
                        # Renderiza o formulário
                        df_formulario = modulo.render_form(competencia)
                        
                        # Botão de submissão individual para cada formulário
                        submitted = st.form_submit_button(f"💾 Salvar {nome_formulario}")
                    
                        if submitted:
                            if not df_formulario.empty and "Quantidade" in df_formulario.columns:
                                valido, resultado = validar_quantidade_ou_tempo(df_formulario, "Quantidade")
                                if not valido:
                                    st.warning("⚠️ Valores inválidos na coluna Quantidade:")
                                    for idx, val in resultado.items():
                                        st.write(f"Linha {idx + 2}: valor '{val}' inválido")
                                else:
                                    df_formulario = resultado
                                    # Remove as linhas que adicionam colunas extras
                                    # df_formulario["Unidade"] = unidade
                                    # df_formulario["Formulário"] = nome_formulario
                                    
                                    st.session_state['formularios_data'][nome_formulario] = df_formulario
                                    arquivo_individual = os.path.join(
                                        OUTPUT_DIR,
                                        f"{nome_formulario}_{unidade}_{competencia}.csv".replace("/", "-").replace(" ", "_")
                                    )
                                    
                                    # Salva o arquivo
                                    try:
                                        # Substitui ponto por vírgula na coluna Quantidade
                                        if 'Quantidade' in df_formulario.columns:
                                            df_formulario['Quantidade'] = df_formulario['Quantidade'].astype(str).str.replace('.', ',')
                                        df_formulario.to_csv(arquivo_individual, index=False, encoding="utf-8-sig", sep=";")
                                        st.success(f"✅ {nome_formulario} salvo com sucesso!")
                                        st.info(f"📁 Arquivo salvo: {arquivo_individual}")
                                    except Exception as save_error:
                                        st.error(f"❌ Erro ao salvar arquivo: {str(save_error)}")
                            else:
                                st.warning(f"⚠️ Formulário retornou dados vazios ou com estrutura incorreta.")
                            
                except Exception as e:
                    st.error(f"❌ Erro ao carregar formulário {nome_formulario}: {str(e)}")
            else:
                st.error(f"❌ Formulário não encontrado: {caminho}")
                
                # Mostra arquivos disponíveis para debug
                if os.path.exists(FORM_DIR):
                    arquivos_disponiveis = [f for f in os.listdir(FORM_DIR) if f.endswith('.py')]
                    if arquivos_disponiveis:
                        st.write("**Arquivos disponíveis na pasta formularios:**")
                        for arquivo in sorted(arquivos_disponiveis):
                            st.write(f"- {arquivo}")

    # Seção de consolidação (depois das abas)
    st.markdown("---")
    st.markdown("## 📊 Consolidação Final")
    
    # Mostra quantos formulários foram preenchidos
    formularios_salvos = len(st.session_state['formularios_data'])
    total_formularios = len(formularios_para_unidade)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Formulários Salvos", formularios_salvos)
    
    with col2:
        st.metric("Total de Formulários", total_formularios)
    
    with col3:
        progresso = (formularios_salvos / total_formularios) * 100 if total_formularios > 0 else 0
        st.metric("Progresso", f"{progresso:.1f}%")
    
    # Barra de progresso
    st.progress(progresso / 100)
    
    # Botão para consolidar todos os formulários
    if st.button("🔄 Consolidar Todos os Formulários", disabled=formularios_salvos == 0):
        if st.session_state['formularios_data']:
            # Junta todos os DataFrames salvos
            dfs_consolidados = list(st.session_state['formularios_data'].values())
            df_final = pd.concat(dfs_consolidados, ignore_index=True)
            
            # Salva o arquivo consolidado
            arquivo_consolidado = os.path.join(
                OUTPUT_DIR, 
                f"CONSOLIDADO_{unidade}_{competencia}.csv".replace("/", "-").replace(" ", "_")
            )
            
            try:
                # Substitui ponto por vírgula na coluna Quantidade
                if 'Quantidade' in df_final.columns:
                    df_final['Quantidade'] = df_final['Quantidade'].astype(str).str.replace('.', ',')
                df_final.to_csv(arquivo_consolidado, index=False, encoding="utf-8-sig", sep=";")
                st.success("✅ Arquivo consolidado gerado com sucesso!")
                st.info(f"📁 Arquivo consolidado: {arquivo_consolidado}")
                
                # Mostra resumo
                st.markdown("### 📈 Resumo da Consolidação")
                st.write(f"**Total de registros**: {len(df_final)}")
                st.write(f"**Formulários incluídos**: {', '.join(st.session_state['formularios_data'].keys())}")
                
                # Mostra preview dos dados
                with st.expander("👀 Preview dos dados consolidados"):
                    st.dataframe(df_final.head(10))
            except Exception as consolidate_error:
                st.error(f"❌ Erro ao salvar arquivo consolidado: {str(consolidate_error)}")
        else:
            st.warning("⚠️ Nenhum formulário foi salvo ainda.")
    
    # Botão para limpar dados salvos
    if st.button("🗑️ Limpar Dados Salvos"):
        st.session_state['formularios_data'] = {}
        st.success("✅ Dados salvos foram limpos!")
        st.rerun()

else:
    st.info("ℹ️ Nenhum formulário aplicável para a unidade selecionada com as configurações atuais.")