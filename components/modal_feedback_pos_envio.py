import streamlit as st
from data.manager_postgre import DatabaseManagerPostgres

def modal_feedback_sucesso():
    """
    Modal de feedback inline que aparece APENAS após envio 100% bem-sucedido para KPIH.
    Se houver erros parciais, este modal NÃO deve ser chamado.
    """
    
    # 🔥 VALIDAÇÃO EXTRA: Se detectar erros, não exibe modal
    teve_erros = st.session_state.get('envio_teve_erros_parciais', False)
    
    if teve_erros:
        return False
    
    # ============================================================================
    # VERIFICA SE FEEDBACK JÁ FOI ENVIADO - MOSTRA APENAS MENSAGEM
    # ============================================================================
    if st.session_state.get('feedback_enviado', False):
        st.success("✅ **Feedback enviado com sucesso! Obrigada por contribuir.**")
        st.markdown("---")
        return True
    
    # ============================================================================
    # FORMULÁRIO DE FEEDBACK
    # ============================================================================
    st.markdown("---")
    st.success("✅ **Todos os dados foram processados e registrados no sistema KPIH com sucesso!**")
    st.markdown("---")
    
    st.markdown("### ⭐ Ajude-nos a melhorar!")
    st.write("Sua opinião é muito importante para continuarmos evoluindo o sistema.")
    
    # Formulário de avaliação
    estrelas = st.radio(
        "Como você avalia sua experiência?",
        ["⭐ Ruim", "⭐⭐ Regular", "⭐⭐⭐ Bom", "⭐⭐⭐⭐ Muito Bom", "⭐⭐⭐⭐⭐ Excelente"],
        index=None,
        key="modal_estrelas"
    )
    
    comentario = st.text_area(
        "Tem alguma sugestão ou comentário?",
        placeholder="Conte-nos sobre sua experiência...",
        key="modal_comentario",
        height=100
    )
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        enviar_feedback = st.button(
            "📩 Enviar Feedback",
            type="primary",
            use_container_width=True,
            key="btn_enviar_feedback_modal"
        )
    
    with col2:
        pular_feedback = st.button(
            "⏭️ Pular",
            use_container_width=True,
            key="btn_pular_feedback_modal"
        )
    
    # ============================================================================
    # LÓGICA DE ENVIO - COM VALIDAÇÃO E FECHAMENTO CORRETO
    # ============================================================================
    if enviar_feedback:
        if estrelas is None:
            st.warning("⚠️ Por favor, selecione uma avaliação.")
            return False
        
        if not comentario or not comentario.strip():
            st.warning("⚠️ Por favor, escreva um comentário.")
            return False
        
        try:
            # Converte estrelas para número
            avaliacao_numero = estrelas.count('⭐')
            
            # Dados da sessão
            email_usuario = st.session_state.get('email_usuario', 'N/A')
            unidade_usuario = st.session_state.get('unidade_usuario', 'N/A')
            competencia_usuario = st.session_state.get('competencia_usuario', 'N/A')
            preenchimento_id = st.session_state.get('ultimo_preenchimento_id')
            
            # Salva no banco
            db = DatabaseManagerPostgres()
            feedback_id = db.registrar_feedback(
                email_usuario=email_usuario,
                unidade=unidade_usuario,
                competencia=competencia_usuario,
                avaliacao=avaliacao_numero,
                comentario=comentario,
                preenchimento_id=preenchimento_id
            )
            
            if feedback_id:
                # Marca como enviado e fecha o modal
                st.session_state['feedback_enviado'] = True
                st.session_state['mostrar_modal_feedback'] = False
                st.rerun()
            else:
                st.error("❌ Erro ao salvar feedback no banco de dados.")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar feedback: {str(e)}")
            return False
    
    if pular_feedback:
        st.session_state['feedback_enviado'] = True
        st.session_state['mostrar_modal_feedback'] = False
        st.rerun()
    
    return False