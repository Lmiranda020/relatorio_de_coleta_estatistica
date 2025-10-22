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

def criar_zip_simples(output_dir, competencia_normalizada, unidade):
    """
    Cria um ZIP simples com todos os arquivos CSV em uma única pasta.
    Versão simplificada para download obrigatório.
    
    Args:
        output_dir: Diretório com os arquivos
        competencia_normalizada: Competência no formato MM-AAAA
        unidade: Nome da unidade
        
    Returns:
        tuple: (BytesIO com o ZIP, quantidade de arquivos)
    """
    from io import BytesIO
    import zipfile
    from datetime import datetime

    # Debug para ver os formulários que traz da API e quais estão sendo salvos na memória do Streamlit

    st.markdown("### 🔍 DEBUG - Formulários na Memória")
    formularios_data = st.session_state.get('formularios_data', {})

    st.write(f"**Total:** {len(formularios_data)} formulários")

    for nome in formularios_data.keys():
        st.write(f"- `{nome}`")

    
    zip_buffer = BytesIO()
    arquivos_adicionados = 0
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Nome da pasta raiz dentro do ZIP
            pasta_raiz = f"formularios_preenchidos_{competencia_normalizada}"
            
            # Percorre todos os arquivos CSV do diretório
            if os.path.exists(output_dir):
                for arquivo in os.listdir(output_dir):
                    if arquivo.endswith('.csv'):
                        caminho_completo = os.path.join(output_dir, arquivo)
                        
                        # Adiciona o arquivo dentro da pasta raiz
                        zip_file.write(
                            caminho_completo,
                            arcname=f"{pasta_raiz}/{arquivo}"
                        )
                        arquivos_adicionados += 1
            
            # Adiciona arquivo README
            readme_content = f"""
╔══════════════════════════════════════════════════════════════╗
║          RELATÓRIO DE COLETA - CEJAM                         ║
╚══════════════════════════════════════════════════════════════╝

INFORMAÇÕES DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unidade: {unidade}
Competência: {competencia_normalizada.replace('_', ' ').replace('-', '/')}
Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Total de arquivos: {arquivos_adicionados}

CONTEÚDO DO PACOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Formulários individuais preenchidos
✅ Dados permanentes obtidos via API
✅ Arquivo CONSOLIDADO (pronto para envio ao KPIH)
✅ Cálculos de consumo de água

INSTRUÇÕES DE USO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 📤 ENVIAR PARA KPIH:
   → Use o arquivo que começa com "CONSOLIDADO_"
   → Este arquivo contém todos os dados organizados

2. 💾 BACKUP:
   → Mantenha esta pasta compactada como backup
   → Útil para auditorias e conferências

3. 🔍 CONFERÊNCIA:
   → Os demais arquivos CSV são os formulários individuais
   → Use para conferir dados específicos se necessário

DETALHES TÉCNICOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Formato: CSV
Separador: ; (ponto e vírgula)
Encoding: UTF-8 com BOM
Decimal: , (vírgula)

SUPORTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email: custos@cejam.org.br
🎫 Sistema de tickets disponível no menu

═══════════════════════════════════════════════════════════════
Sistema de Coleta de Dados - CEJAM © {datetime.now().year}
═══════════════════════════════════════════════════════════════
            """.strip()
            
            zip_file.writestr(f"{pasta_raiz}/LEIA-ME.txt", readme_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        return zip_buffer, arquivos_adicionados
        
    except Exception as e:
        raise Exception(f"Erro ao criar ZIP simplificado: {str(e)}")