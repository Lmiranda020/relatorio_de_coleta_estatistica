"""
Funções para manipulação de arquivos e pastas
"""
import os
import streamlit as st
import zipfile
from io import BytesIO
import os
from datetime import datetime

def rastrear_arquivo_salvo(output_dir, nome_formulario, competencia, tipo_arquivo='csv'):
    """
    Rastreia onde um arquivo foi salvo e retorna seu caminho completo.
    Útil para encontrar arquivos com nomes variados.
    """
    padroes = [
        f"{nome_formulario}_{competencia}".replace("/", "-").replace(" ", "_"),
        f"{nome_formulario.replace(' ', '_')}_{competencia}".replace("/", "-"),
        nome_formulario.replace(" ", "_"),
    ]
    
    for padrão in padroes:
        caminho = os.path.join(output_dir, f"{padrão}.{tipo_arquivo}")
        if os.path.exists(caminho):
            return caminho
    
    return None


def organizar_arquivos_para_download(output_dir, competencia_normalizada, unidade, formularios_data):
    """
    Organiza todos os arquivos disponíveis em categorias para download.
    Retorna um dicionário com a estrutura completa.
    """
    estrutura = {
        'consolidado': [],
        'dados_permanentes': [],
        'calculos': [],
        'formularios': {
            'criticidade': [],
            'outros': []
        },
        'total_arquivos': 0,
        'total_tamanho': 0
    }
    
    try:
        if not os.path.exists(output_dir):
            return estrutura
        
        for arquivo in os.listdir(output_dir):
            if not arquivo.endswith('.csv'):
                continue
            
            caminho_completo = os.path.join(output_dir, arquivo)
            tamanho = os.path.getsize(caminho_completo)
            
            arquivo_info = {
                'nome': arquivo,
                'caminho': caminho_completo,
                'tamanho': tamanho
            }
            
            # Categoriza cada arquivo
            if 'CONSOLIDADO' in arquivo:
                estrutura['consolidado'].append(arquivo_info)
            elif 'Area_Criticidade_API' in arquivo or 'Criticidade_API' in arquivo:
                estrutura['dados_permanentes'].append(arquivo_info)
            elif 'Agua' in arquivo or 'Água' in arquivo:
                estrutura['calculos'].append(arquivo_info)
            elif 'Criticidade' in arquivo or 'Crítica' in arquivo:
                estrutura['formularios']['criticidade'].append(arquivo_info)
            else:
                estrutura['formularios']['outros'].append(arquivo_info)
            
            estrutura['total_arquivos'] += 1
            estrutura['total_tamanho'] += tamanho
        
        return estrutura
        
    except Exception as e:
        st.error(f"Erro ao organizar arquivos: {e}")
        return estrutura


def criar_zip_formularios(output_dir, competencia, unidade, estrutura_arquivos=None):
    """
    Versão 2: Cria ZIP com base na estrutura real de arquivos encontrados.
    Se estrutura_arquivos for None, descobre automaticamente.
    """
    zip_buffer = BytesIO()
    
    try:
        # Se não passou a estrutura, descobre os arquivos
        if estrutura_arquivos is None:
            estrutura_arquivos = organizar_arquivos_para_download(
                output_dir, 
                competencia.replace("/", "-").replace(" ", "_"), 
                unidade, 
                {}
            )
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            contador = 0
            
            # Adiciona Consolidado (prioridade 1)
            for arquivo_info in estrutura_arquivos['consolidado']:
                zip_file.write(
                    arquivo_info['caminho'],
                    f"00_CONSOLIDADO/{arquivo_info['nome']}"
                )
                contador += 1
            
            # Adiciona Dados Permanentes (prioridade 2)
            for arquivo_info in estrutura_arquivos['dados_permanentes']:
                zip_file.write(
                    arquivo_info['caminho'],
                    f"01_DadosPermanentes/{arquivo_info['nome']}"
                )
                contador += 1
            
            # Adiciona Cálculos (prioridade 3)
            for arquivo_info in estrutura_arquivos['calculos']:
                zip_file.write(
                    arquivo_info['caminho'],
                    f"02_Calculos/{arquivo_info['nome']}"
                )
                contador += 1
            
            # Adiciona Formulários - Criticidade (prioridade 4)
            for arquivo_info in estrutura_arquivos['formularios']['criticidade']:
                zip_file.write(
                    arquivo_info['caminho'],
                    f"03_Formularios_Criticidade/{arquivo_info['nome']}"
                )
                contador += 1
            
            # Adiciona Formulários - Outros (prioridade 5)
            for arquivo_info in estrutura_arquivos['formularios']['outros']:
                zip_file.write(
                    arquivo_info['caminho'],
                    f"04_Formularios_Outros/{arquivo_info['nome']}"
                )
                contador += 1
            
            # Adiciona README
            readme_content = f"""
╔══════════════════════════════════════════════════════════════╗
║          RELATÓRIO DE COLETA - CEJAM                         ║
╚══════════════════════════════════════════════════════════════╝

INFORMAÇÕES DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unidade: {unidade}
Competência: {competencia}
Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Total de arquivos CSV: {contador}

ESTRUTURA DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00_CONSOLIDADO/
    Arquivo principal pronto para envio ao KPIH
    Use este arquivo para fazer o upload no sistema

01_DadosPermanentes/
    Dados permanentes importados via API
    Exemplo: Area_Criticidade_API

02_Calculos/
    Cálculos automáticos realizados
    Exemplo: Consumo de água

03_Formularios_Criticidade/
    Formulários de criticidade preenchidos
    • Área Crítica
    • Área Semi Crítica
    • Área Não Crítica

04_Formularios_Outros/
    Demais formulários preenchidos
    Vários modelos de O.S., refeições, etc

INSTRUÇÕES DE USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ENVIAR PARA KPIH:
   Use o arquivo em 00_CONSOLIDADO/

2. BACKUP:
   Mantenha toda a pasta compactada como backup

3. VERIFICAÇÃO:
   Se houver erros, revise os arquivos individuais
   nas pastas 03_ e 04_

DETALHES TÉCNICOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Separador: ;
Encoding: UTF-8
Formato: CSV

SUPORTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Para suporte técnico:
Email: custos@cejam.org.br

═══════════════════════════════════════════════════════════════
Sistema de Coleta de Dados - CEJAM
═══════════════════════════════════════════════════════════════
            """.strip()
            
            zip_file.writestr("LEIA-ME.txt", readme_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        return zip_buffer, contador
        
    except Exception as e:
        raise Exception(f"Erro ao criar ZIP: {str(e)}")

def get_tamanho_legivel(tamanho_bytes):
    """Converte bytes para formato legível (KB, MB)"""
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.1f} {unidade}"
        tamanho_bytes /= 1024.0

# Função para obter o caminho do desktop do usuário
def get_desktop_path():
    """
    Retorna o caminho do desktop do usuário atual
    """
    try:
        # Windows
        if os.name == 'nt': # verifica se o sistema é Windows, name é um atributo do módulo os que retorna o nome do sistema operacional
            #se o sistema operacional for Windows, o caminho do desktop é obtido com a função os.path.join, 
            # que junta o caminho do usuário com a pasta Desktop
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            # pah -> é um submodulo do módulo os que fornece funções para manipular caminhos de arquivos e diretórios
            # então essa primeira parte eu quero fazer algo com o caminho, ou seja, fazer um join
            # e expanduser é uma função do módulo os que retorna o caminho do diretório home do usuário atual
            # o ~ é um atalho que representa o diretório home do usuário, ou seja, o diretório pessoal do usuário atual
            # o ~ é uma convenção do sistema operacional que indica o diretório home do usuário atual
            # o expanduser é quem interpreta o ~ e retorna o caminho completo do diretório home do usuário

        # macOS e Linux
        else:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        #Valor	Significado
        #'nt'	Windows (NT = Windows NT)
        #'posix'	Linux, macOS, Unix, etc.
        #'java'	JVM (Jython)
        
        # Verifica se o diretório existe
        if not os.path.exists(desktop): # para verificar se existe o caminho do desktop, se não existir, ele tenta alternativas
            # Tenta alternativas para Linux
            desktop = os.path.join(os.path.expanduser('~'), 'Área de Trabalho') # a diferença é que eu faço um join agora com o nome "Aréa de Trabalho"
            if not os.path.exists(desktop): # mesmo assim, se não existir, ele tenta outra alternativa
                desktop = os.path.expanduser('~')  # traz o nome do diretorio home, sem o join
        
        return desktop # por fim, retorna o caminho do desktop ou do home
    except Exception as e: # se der error, ele captura a exceção e mostra uma mensagem de erro
        st.error(f"Erro ao obter caminho do desktop: {str(e)}")
        return os.path.expanduser('~')  # se der erro, retorna o caminho do diretório home do usuário