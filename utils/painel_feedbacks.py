import streamlit as st
import pandas as pd
from data.manager_postgre import DatabaseManagerPostgres

def mostrar_painel_feedbacks():
    """
    Painel para visualizar e analisar feedbacks dos usuários
    Adicione esta função ao painel de suporte (custos@cejam.org.br)
    """
    
    st.title("⭐ Painel de Feedbacks")
    
    db = DatabaseManagerPostgres()
    
    # Verifica/cria tabela de feedbacks
    if not db.criar_tabela_feedbacks():
        st.error("Erro ao criar/verificar tabela de feedbacks")
        return
    
    # Obter estatísticas
    stats = db.obter_estatisticas_feedbacks()
    
    if not stats:
        st.warning("Não foi possível carregar estatísticas de feedbacks")
        return
    
    # === SEÇÃO 1: MÉTRICAS GERAIS ===
    st.subheader("📊 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Feedbacks", stats['total_feedbacks'])
    
    with col2:
        st.metric("Média de Avaliação", f"{stats['media_avaliacao']}/5.0")
    
    with col3:
        st.metric("Últimos 30 dias", stats['ultimos_30_dias'])
    
    with col4:
        # Calcula taxa de satisfação (4 e 5 estrelas)
        total = stats['total_feedbacks']
        satisfeitos = sum(q for a, q in stats['distribuicao_estrelas'] if a >= 4)
        taxa_satisfacao = (satisfeitos / total * 100) if total > 0 else 0
        st.metric("Taxa de Satisfação", f"{taxa_satisfacao:.1f}%")
    
    st.divider()
    
    # === SEÇÃO 2: DISTRIBUIÇÃO DE ESTRELAS ===
    st.subheader("⭐ Distribuição de Avaliações")
    
    col_chart, col_table = st.columns([3, 1])
    
    with col_chart:
        # Criar DataFrame para o gráfico
        if stats['distribuicao_estrelas']:
            df_estrelas = pd.DataFrame(
                stats['distribuicao_estrelas'], 
                columns=['Estrelas', 'Quantidade']
            )
            
            # Gráfico de barras
            st.bar_chart(
                df_estrelas.set_index('Estrelas'), 
                use_container_width=True,
                color="#FFD700"
            )
    
    with col_table:
        st.write("**Detalhamento:**")
        for estrelas, quantidade in stats['distribuicao_estrelas']:
            percentual = (quantidade / stats['total_feedbacks'] * 100) if stats['total_feedbacks'] > 0 else 0
            st.write(f"{'⭐' * estrelas}: {quantidade} ({percentual:.1f}%)")
    
    st.divider()
    
    # === SEÇÃO 3: TOP UNIDADES ===
    st.subheader("🏆 Top 10 Unidades - Melhores Avaliações")
    
    if stats['top_unidades']:
        df_top_unidades = pd.DataFrame(
            stats['top_unidades'],
            columns=['Unidade', 'Total Feedbacks', 'Média']
        )
        df_top_unidades['Média'] = pd.to_numeric(df_top_unidades['Média'], errors='coerce').round(2)
        
        st.dataframe(
            df_top_unidades,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Ainda não há dados suficientes para ranking")
    
    st.divider()
    
    # === SEÇÃO 4: FEEDBACKS POR COMPETÊNCIA ===
    st.subheader("📅 Feedbacks por Competência")
    
    if stats['por_competencia']:
        df_competencia = pd.DataFrame(
            stats['por_competencia'],
            columns=['Competência', 'Total', 'Média']
        )
        # Converte para numérico antes de arredondar
        df_competencia['Média'] = pd.to_numeric(df_competencia['Média'], errors='coerce').round(2)
        
        col_comp1, col_comp2 = st.columns(2)
        
        with col_comp1:
            st.dataframe(
                df_competencia,
                use_container_width=True,
                hide_index=True
            )
        
        with col_comp2:
            st.line_chart(
                df_competencia.set_index('Competência')['Média'],
                use_container_width=True
            )
    
    st.divider()
    
    # === SEÇÃO 5: FEEDBACKS RECENTES ===
    st.subheader("💬 Feedbacks Recentes")
    
    if stats['feedbacks_recentes']:
        for feedback in stats['feedbacks_recentes']:
            fb_id, email, unidade, competencia, avaliacao, comentario, data = feedback
            
            with st.expander(
                f"{'⭐' * avaliacao} | {unidade} | {competencia} | {data.strftime('%d/%m/%Y')}"
            ):
                col_info, col_comment = st.columns([1, 2])
                
                with col_info:
                    st.write(f"**ID:** {fb_id}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Unidade:** {unidade}")
                    st.write(f"**Competência:** {competencia}")
                    st.write(f"**Avaliação:** {'⭐' * avaliacao}")
                    st.write(f"**Data:** {data.strftime('%d/%m/%Y')}")
                
                with col_comment:
                    st.write("**Comentário:**")
                    if comentario:
                        st.info(comentario)
                    else:
                        st.caption("_Sem comentário_")
    else:
        st.info("Ainda não há feedbacks registrados")
    
    st.divider()
    
    # === SEÇÃO 6: FILTROS E BUSCA DETALHADA ===
    st.subheader("🔍 Busca Detalhada de Feedbacks")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        filtro_avaliacao = st.selectbox(
            "Filtrar por avaliação:",
            [None, 1, 2, 3, 4, 5],
            format_func=lambda x: "Todas" if x is None else f"{'⭐' * x}"
        )
    
    with col_filtro2:
        # Obter competências disponíveis
        competencias_disponiveis = [comp for comp, _, _ in stats['por_competencia']]
        filtro_competencia = st.selectbox(
            "Filtrar por competência:",
            [None] + competencias_disponiveis,
            format_func=lambda x: "Todas" if x is None else x
        )
    
    with col_filtro3:
        filtro_unidade = st.text_input("Filtrar por unidade (opcional):")
    
    if st.button("🔍 Buscar", type="primary"):
        feedbacks_detalhados = db.listar_feedbacks_detalhados(
            filtro_avaliacao=filtro_avaliacao,
            filtro_competencia=filtro_competencia,
            filtro_unidade=filtro_unidade if filtro_unidade else None,
            limite=100
        )
        
        if feedbacks_detalhados:
            st.success(f"Encontrados {len(feedbacks_detalhados)} feedbacks")
            
            df_feedbacks = pd.DataFrame(
                feedbacks_detalhados,
                columns=[
                    'ID', 'Email', 'Unidade', 'Competência', 'Avaliação',
                    'Comentário', 'Data', 'Preenchimento ID', 'Total Formulários'
                ]
            )
            
            # Formatar colunas
            df_feedbacks['Avaliação'] = df_feedbacks['Avaliação'].apply(lambda x: '⭐' * x)
            df_feedbacks['Data'] = pd.to_datetime(df_feedbacks['Data']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                df_feedbacks,
                use_container_width=True,
                hide_index=True
            )
            
            # Botão de exportação
            csv = df_feedbacks.to_csv(index=False, encoding='utf-8-sig', sep=';')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name="feedbacks_detalhados.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum feedback encontrado com os filtros aplicados")