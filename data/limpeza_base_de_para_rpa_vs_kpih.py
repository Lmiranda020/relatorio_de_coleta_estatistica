import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from config.constants import get_token_unidades_importacao


def ajustar_competencia(competencia: str) -> str:
    """
    Ajusta competência de formatos como 'mai/2025' para '05/2025'.
    Se já estiver no formato '05/2025', retorna igual.
    """
    if "/" not in competencia:
        return competencia  # não tem como ajustar
    
    partes = competencia.split("/")
    if len(partes) != 2:
        return competencia  # formato inesperado
    
    mes_parte = partes[0].strip()
    ano_parte = partes[1].strip()

    # Se já for número (ex: "05/2025"), mantém
    if mes_parte.isdigit():
        return f"{mes_parte.zfill(2)}/{ano_parte}"

    # Converter mês por extenso (abreviado)
    meses_map = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12"
    }
    mes_numero = meses_map.get(mes_parte.lower()[:3])  # garante 3 primeiras letras
    if mes_numero:
        return f"{mes_numero}/{ano_parte}"

    return competencia  # caso não reconheça o mês

def carregar_e_tratar_depara_json(caminho_excel: str) -> List[Dict[str, str]]:
    """
    Lê o arquivo de de-para ERP vs KPIH, aplica filtros e retorna no formato
    esperado pela API: lista de dicionários com competencia + mapeamentos.
    
    Retorna uma lista onde cada item contém:
    - competencia: string no formato dd/yyyy
    - centroDeCustoErp: string
    - centroDeCustoKpih: string
    """
    try:
        st.info(f"📖 Carregando arquivo: {caminho_excel}")
        
        # 1. Ler Excel
        base = pd.read_excel(caminho_excel)
        
        st.info(f"🔍 Colunas encontradas: {list(base.columns)}")
        st.info(f"🔍 Total de registros no Excel: {len(base)}")
        
        # 2. Verificar se as colunas necessárias existem
        colunas_necessarias = ['centroDeCustoErp', 'centroDeCustoKpih']
        colunas_faltando = [col for col in colunas_necessarias if col not in base.columns]
        
        if colunas_faltando:
            st.error(f"Colunas obrigatórias não encontradas: {colunas_faltando}")
            raise ValueError(f"Colunas obrigatórias não encontradas: {colunas_faltando}")
        
        # 3. Tratar valores NaN/NA
        base = base.fillna("")
        
        # 4. Extrair competência - PRIORIDADE: sessão do Streamlit
        competencia_extraida = None
        
        # 1ª PRIORIDADE: Competência da sessão do Streamlit (escolha do usuário)
        if hasattr(st, 'session_state'):
            competencia_extraida = st.session_state.get('competencia_usuario', '')
            competencia_ajustada = ajustar_competencia(competencia_extraida)
            if competencia_ajustada:
                st.success(f"📅 Competência obtida da sessão do usuário: {competencia_ajustada}")
        
        # 2ª PRIORIDADE: Competência do Excel (caso não tenha na sessão)
        if not competencia_extraida and 'competencia' in base.columns:
            competencias = base['competencia'].dropna().astype(str)
            if len(competencias) > 0:
                competencia_ajustada = competencias.iloc[0].strip()
                st.info(f"📅 Competência obtida do Excel: {competencia_ajustada}")
        
        st.success(f"📅 Competência definida: {competencia_ajustada}")
        
        # 5. Aplicar filtros para exclusão
        st.info("🔧 Aplicando filtros de exclusão...")
        
        mask_excluir = (
            base["centroDeCustoErp"].str.contains("(NAO OPERACIONAL)", case=False, na=False, regex=False) |
            base["centroDeCustoErp"].str.contains(r"^SADT\s-\s", case=False, na=False) |
            base["centroDeCustoErp"].str.contains("JD MARCELO", case=False, na=False)
        )
        
        registros_excluidos = mask_excluir.sum()
        if registros_excluidos > 0:
            st.warning(f"❌ Registros excluídos pelos filtros: {registros_excluidos}")
        
        base_filtrada = base[~mask_excluir].copy()
        st.success(f"✅ Registros após filtros: {len(base_filtrada)}")
        
        # 6. Limpar e validar dados
        base_filtrada = base_filtrada.fillna("")
        
        # Remover registros onde os campos obrigatórios estão vazios
        mask_validos = (
            (base_filtrada["centroDeCustoErp"].str.strip() != "") &
            (base_filtrada["centroDeCustoKpih"].str.strip() != "")
        )
        
        registros_invalidos = (~mask_validos).sum()
        if registros_invalidos > 0:
            st.warning(f"⚠️ Registros com campos vazios removidos: {registros_invalidos}")
        
        base_filtrada = base_filtrada[mask_validos].copy()
        st.success(f"✅ Registros válidos finais: {len(base_filtrada)}")
        
        # 7. Criar lista de mapeamentos no formato esperado pela API
        mapeamentos = []
        
        for _, row in base_filtrada.iterrows():
            mapeamento = {
                "competencia": competencia_ajustada,
                "centroDeCustoErp": str(row["centroDeCustoErp"]).strip(),
                "centroDeCustoKpih": str(row["centroDeCustoKpih"]).strip()
            }
            mapeamentos.append(mapeamento)
        
        st.success(f"🎯 Total de mapeamentos criados: {len(mapeamentos)}")
        
        # 8. Mostrar exemplos dos primeiros registros
        if mapeamentos:
            with st.expander("📋 Primeiros 3 mapeamentos"):
                for i, mapeamento in enumerate(mapeamentos[:3]):
                    st.write(f"**{i+1}:** {mapeamento}")
        else:
            st.error("⚠️ Nenhum mapeamento foi criado!")
        
        return mapeamentos
        
    except FileNotFoundError:
        st.error(f"❌ Arquivo não encontrado: {caminho_excel}")
        return []
    except Exception as e:
        st.error(f"💥 Erro ao processar arquivo: {e}")
        st.exception(e)
        return []


# def obter_token_por_unidade_id() -> str:
#     """
#     Obtém o token da unidade com base no ID armazenado na sessão do Streamlit.
#     Filtra o arquivo de tokens pela unidade específica.
#     USA TOKENS DE IMPORTAÇÃO.
#     """
#     try:
#         # 1. Obter ID da unidade da sessão
#         unidade_id = st.session_state.get('unidade_id', None)
        
#         if not unidade_id:
#             st.error("❌ ID da unidade não encontrado na sessão. Execute primeiro a busca de dados permanentes.")
#             return ""
        
#         st.info(f"🔍 Buscando token para unidade ID: {unidade_id}")
        
#         # 2. Verificar se o DataFrame foi carregado
#         TOKEN_UNIDADES_IMPORTACAO_DF = get_token_unidades_importacao()
#         if TOKEN_UNIDADES_IMPORTACAO_DF.empty:
#             st.error("❌ Arquivo de tokens não foi carregado corretamente")
#             return ""
        
#         st.info(f"📊 Total de unidades disponíveis: {len(TOKEN_UNIDADES_IMPORTACAO_DF)}")
        
#         # 3. Filtrar pela unidade específica
#         unidade_filtrada = TOKEN_UNIDADES_IMPORTACAO_DF[TOKEN_UNIDADES_IMPORTACAO_DF['id'] == unidade_id]
        
#         if unidade_filtrada.empty:
#             st.error(f"❌ Unidade com ID {unidade_id} não encontrada no arquivo de tokens")
#             st.warning("💡 Verifique se o ID está correto e se o arquivo de tokens está atualizado")
#             return ""
        
#         # 4. Obter token da unidade
#         token = unidade_filtrada.iloc[0]['token']
#         nome_unidade = unidade_filtrada.iloc[0].get('nome', f'Unidade {unidade_id}')
        
#         st.success(f"✅ Token encontrado para {nome_unidade} (ID: {unidade_id})")
        
#         return str(token).strip()
        
#     except KeyError as e:
#         st.error(f"❌ Coluna não encontrada no DataFrame de tokens: {e}")
#         st.info("💡 Certifique-se de que o Excel tem as colunas: id, nome, token")
#         return ""
#     except Exception as e:
#         st.error(f"💥 Erro ao obter token da unidade: {e}")
#         st.exception(e)
#         return ""


def validar_estrutura_depara(mapeamentos: List[Dict[str, str]]) -> bool:
    """
    Valida se a estrutura dos mapeamentos está correta para a API.
    """
    if not mapeamentos:
        st.error("❌ Lista de mapeamentos está vazia")
        return False
    
    campos_obrigatorios = ["centroDeCustoErp", "centroDeCustoKpih"]
    
    erros_encontrados = 0
    
    for i, mapeamento in enumerate(mapeamentos):
        # Verificar se todos os campos obrigatórios existem
        for campo in campos_obrigatorios:
            if campo not in mapeamento:
                st.error(f"❌ Campo '{campo}' faltando no mapeamento {i+1}")
                erros_encontrados += 1
            
            elif not mapeamento[campo] or str(mapeamento[campo]).strip() == "":
                st.error(f"❌ Campo '{campo}' vazio no mapeamento {i+1}")
                erros_encontrados += 1
    
    if erros_encontrados == 0:
        st.success(f"✅ Estrutura validada - {len(mapeamentos)} mapeamentos válidos")
        return True
    else:
        st.error(f"❌ {erros_encontrados} erros encontrados na validação")
        return False


def obter_competencia_usuario() -> str:
    """
    Obtém a competência selecionada pelo usuário na sessão do Streamlit.
    Retorna a competência ou uma padrão caso não encontre.
    """
    competencia = None
    
    # Tenta obter da sessão do Streamlit
    try:
        if hasattr(st, 'session_state'):
            competencia = st.session_state.get('competencia_usuario', '')
            if competencia:
                st.success(f"✅ Competência do usuário encontrada: {competencia}")
                return competencia.strip()
    except:
        pass
    
    # # Fallback para competência padrão
    # competencia_padrao = "09/2025"
    # st.warning(f"⚠️ Competência do usuário não encontrada, usando padrão: {competencia_padrao}")
    # return competencia_padrao


def obter_estatisticas_depara(mapeamentos: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Retorna estatísticas dos dados de de-para carregados e exibe no Streamlit.
    """
    if not mapeamentos:
        st.warning("📊 Nenhum mapeamento disponível para estatísticas")
        return {"total": 0, "competencias": [], "centros_erp_unicos": 0, "centros_kpih_unicos": 0}
    
    competencias = list(set([m["competencia"] for m in mapeamentos]))
    centros_erp = list(set([m["centroDeCustoErp"] for m in mapeamentos]))
    centros_kpih = list(set([m["centroDeCustoKpih"] for m in mapeamentos]))
    
    stats = {
        "total": len(mapeamentos),
        "competencias": competencias,
        "centros_erp_unicos": len(centros_erp),
        "centros_kpih_unicos": len(centros_kpih),
        "sample_centros_erp": centros_erp[:5],
        "sample_centros_kpih": centros_kpih[:5]
    }
    
    # Exibir estatísticas no Streamlit
    st.info("📊 **Estatísticas dos Dados de De-Para:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Mapeamentos", stats['total'])
    
    with col2:
        st.metric("Centros ERP Únicos", stats['centros_erp_unicos'])
    
    with col3:
        st.metric("Centros KPIH Únicos", stats['centros_kpih_unicos'])
    
    with st.expander("🔍 Detalhes das Estatísticas"):
        st.write("**Competências encontradas:**", competencias)
        st.write("**Amostra de Centros ERP:**", stats['sample_centros_erp'])
        st.write("**Amostra de Centros KPIH:**", stats['sample_centros_kpih'])
    
    return stats


def armazenar_unidade_id_na_sessao(unidade_id: int):
    """
    Armazena o ID da unidade na sessão do Streamlit para uso posterior.
    """
    if 'unidade_id' not in st.session_state:
        st.session_state['unidade_id'] = unidade_id
        st.success(f"✅ ID da unidade armazenado na sessão: {unidade_id}")
    else:
        # Atualiza se for diferente
        if st.session_state['unidade_id'] != unidade_id:
            st.session_state['unidade_id'] = unidade_id
            st.info(f"🔄 ID da unidade atualizado na sessão: {unidade_id}")
        else:
            st.info(f"ℹ️ ID da unidade já estava na sessão: {unidade_id}")


def obter_unidade_id_da_sessao() -> int:
    """
    Obtém o ID da unidade armazenado na sessão do Streamlit.
    """
    unidade_id = st.session_state.get('unidade_id', None)
    
    if unidade_id:
        st.info(f"✅ ID da unidade recuperado da sessão: {unidade_id}")
        return unidade_id
    else:
        st.error("❌ ID da unidade não encontrado na sessão")
        return None