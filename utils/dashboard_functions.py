import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data.manager_postgre import DatabaseManagerPostgres
from config.constants import competencias

def mostrar_dashboard_preenchimentos():
    """Dashboard principal na aba Relatórios"""
    st.subheader("📊 Dashboard - Preenchimentos Finalizados")
    
    db = DatabaseManagerPostgres()
    stats = db.obter_estatisticas_dashboard()
    
    if not stats:
        st.error("❌ Erro ao carregar estatísticas")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Finalizados", stats.get('total_preenchimentos', 0))
    
    with col2:
        st.metric("Últimos 30 dias", stats.get('ultimos_30_dias', 0))
    
    with col3:
        total_competencias = len(stats.get('por_competencia', []))
        st.metric("Competências", total_competencias)
    
    with col4:
        total_unidades = len(stats.get('ranking_unidades', []))
        st.metric("Unidades Ativas", total_unidades)
    
    st.markdown("---")
    
    # Gráficos em duas colunas
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("📅 Por Competência")
        por_competencia = stats.get('por_competencia', [])
        if por_competencia:
            df_comp = pd.DataFrame(por_competencia, columns=['Competência', 'Total'])
            fig_comp = px.bar(df_comp, x='Competência', y='Total', 
                             title="Preenchimentos por Competência")
            fig_comp.update_layout(height=400)
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Nenhum dado disponível")
    
    with col_graf2:
        st.subheader("🏢 Top 10 Unidades")
        por_unidade = stats.get('por_unidade', [])
        if por_unidade:
            df_unid = pd.DataFrame(por_unidade[:10], columns=['Unidade', 'Total'])
            fig_unid = px.bar(df_unid, x='Total', y='Unidade', orientation='h',
                             title="Top 10 Unidades que mais preenchem")
            fig_unid.update_layout(height=400)
            st.plotly_chart(fig_unid, use_container_width=True)
        else:
            st.info("Nenhum dado disponível")
    
    # Atividade recente
    st.subheader("📈 Atividade - Últimos 7 dias")
    por_dia = stats.get('por_dia', [])
    if por_dia:
        df_dias = pd.DataFrame(por_dia, columns=['Data', 'Total'])
        df_dias['Data'] = pd.to_datetime(df_dias['Data'])
        
        fig_linha = px.line(df_dias, x='Data', y='Total', 
                           title="Preenchimentos por dia",
                           markers=True)
        st.plotly_chart(fig_linha, use_container_width=True)
    else:
        st.info("Nenhuma atividade nos últimos 7 dias")

def mostrar_relatorio_unidades():
    """Relatório detalhado na aba Unidades"""
    st.subheader("🏢 Relatório por Unidades")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        competencia_filtro = st.selectbox("Competência", ["Todas"] + competencias)
        
    with col2:
        data_inicio = st.date_input("Data início", value=datetime.now() - timedelta(days=30))
        
    with col3:
        data_fim = st.date_input("Data fim", value=datetime.now())
    
    db = DatabaseManagerPostgres()
    
    if st.button("🔍 Aplicar Filtros"):
        # Prepara filtros
        comp_filtro = None if competencia_filtro == "Todas" else competencia_filtro
        
        # Obtém relatório
        relatorio = db.obter_relatorio_preenchimentos(
            competencia=comp_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        if relatorio:
            # Converte para DataFrame
            colunas = ['ID', 'Email', 'Nome', 'Unidade', 'Competência', 
                      'Data Finalização', 'Total Formulários', 'IP']
            df_relatorio = pd.DataFrame(relatorio, columns=colunas)
            
            # Formata data
            df_relatorio['Data Finalização'] = pd.to_datetime(
                df_relatorio['Data Finalização']
            ).dt.strftime('%d/%m/%Y')
            
            st.subheader(f"📋 Resultados ({len(df_relatorio)} registros)")
            st.dataframe(df_relatorio, use_container_width=True)
            
            # Download
            csv = df_relatorio.to_csv(index=False, sep=';')
            st.download_button(
                "📥 Baixar Relatório CSV",
                csv.encode('utf-8-sig'),
                f"relatorio_preenchimentos_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.info("ℹ️ Nenhum registro encontrado para os filtros selecionados")
    
    # Seção de unidades pendentes
    st.markdown("---")
    st.subheader("⏳ Status por Competência")
    
    competencia_status = st.selectbox("Selecione competência para ver status:", competencias)
    
    if st.button("📊 Ver Status da Competência"):
        status_unidades = db.obter_unidades_pendentes(competencia_status)
        
        if status_unidades:
            col_met1, col_met2, col_met3 = st.columns(3)
            
            with col_met1:
                st.metric("Total Unidades", status_unidades['total_unidades'])
            with col_met2:
                st.metric("Preencheram", status_unidades['total_preencheram'])
            with col_met3:
                st.metric("Pendentes", status_unidades['total_pendentes'])
            
            # Progress bar
            if status_unidades['total_unidades'] > 0:
                percentual = (status_unidades['total_preencheram'] / status_unidades['total_unidades']) * 100
                st.metric("Percentual Completo", f"{percentual:.1f}%")
                st.progress(percentual / 100)
            
            # Listas
            col_listas1, col_listas2 = st.columns(2)
            
            with col_listas1:
                st.success("✅ Unidades que Preencheram")
                for unidade in status_unidades['preencheram']:
                    st.write(f"• {unidade}")
                    
            with col_listas2:
                st.warning("⏳ Unidades Pendentes")
                for unidade in status_unidades['pendentes']:
                    st.write(f"• {unidade}")