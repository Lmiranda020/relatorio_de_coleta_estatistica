"""
Funções para manipulação de arquivos e pastas
"""
import os
import streamlit as st
import zipfile
from io import BytesIO
import os
from datetime import datetime

def criar_zip_formularios(output_dir, competencia, unidade):
    """
    Cria um arquivo ZIP com todos os formulários da competência.
    Inclui metadata e organização profissional.
    """
    zip_buffer = BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            arquivos_adicionados = 0
            
            # Lista e organiza arquivos por tipo
            arquivos_csv = sorted([f for f in os.listdir(output_dir) if f.endswith('.csv')])
            
            for arquivo in arquivos_csv:
                caminho_completo = os.path.join(output_dir, arquivo)
                
                # Adiciona ao ZIP com path organizado
                if 'CONSOLIDADO' in arquivo:
                    zip_file.write(caminho_completo, f"00_CONSOLIDADO/{arquivo}")
                elif 'API' in arquivo:
                    zip_file.write(caminho_completo, f"01_DadosPermanentes/{arquivo}")
                elif 'Agua' in arquivo or 'Água' in arquivo:
                    zip_file.write(caminho_completo, f"02_Calculos/{arquivo}")
                else:
                    zip_file.write(caminho_completo, f"03_Formularios/{arquivo}")
                
                arquivos_adicionados += 1
            
            # Adiciona arquivo README.txt
            readme_content = f"""
╔══════════════════════════════════════════════════════════════╗
║          RELATÓRIO DE COLETA - CEJAM                         ║
╚══════════════════════════════════════════════════════════════╝

📋 INFORMAÇÕES DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Unidade: {unidade}
- Competência: {competencia}
- Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
- Total de arquivos: {arquivos_adicionados}

📁 ESTRUTURA DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00_CONSOLIDADO/     → Arquivo principal (use este para envio)
01_DadosPermanentes/ → Dados importados da API
02_Calculos/        → Cálculos automáticos (água, etc)
03_Formularios/     → Formulários individuais preenchidos

⚠️ IMPORTANTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- O arquivo CONSOLIDADO é o que deve ser enviado ao KPIH
- Mantenha este ZIP como backup
- Todos os arquivos usam separador ";" e encoding UTF-8

═══════════════════════════════════════════════════════════════
Sistema desenvolvido por: Equipe de Custos CEJAM
Para suporte: custos@cejam.org.br
═══════════════════════════════════════════════════════════════
            """.strip()
            
            zip_file.writestr("LEIA-ME.txt", readme_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        return zip_buffer, arquivos_adicionados
        
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