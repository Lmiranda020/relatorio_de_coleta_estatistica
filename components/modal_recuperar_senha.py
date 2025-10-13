import streamlit as st
import time
from utils.password_utils import validar_forca_senha
from data.manager_postgre import DatabaseManagerPostgres
from PIL import Image
import os
from config.constants import imagem_cejam, imagem_sus

def mostrar_tela_recuperacao():
    """Tela completa de recuperação de senha"""
   
    # Header da página
    if st.button("⬅️ Voltar", key="btn_voltar_login"):
        st.session_state.tela_recuperacao = False
        _limpar_estados_recuperacao()
        st.rerun()
        
    st.markdown("### 🔑 Recuperar Senha")
             
    # Controle de etapas
    if 'etapa_recuperacao' not in st.session_state:
        st.session_state.etapa_recuperacao = 1
        
    # ETAPA 1: Informar email
    if st.session_state.etapa_recuperacao == 1:
        _etapa_verificar_email()
            
    # ETAPA 2: Responder pergunta de segurança
    elif st.session_state.etapa_recuperacao == 2:
        _etapa_pergunta_seguranca()
            
    # ETAPA 3: Definir nova senha
    elif st.session_state.etapa_recuperacao == 3:
        _etapa_nova_senha()

def _etapa_verificar_email():
    """Primeira etapa: verificar email"""
    st.info("📧 Digite seu e-mail para verificar se possui pergunta de segurança cadastrada.")
    
    with st.form("form_email_recuperacao"):
        email_recuperacao = st.text_input(
            "E-mail:",
            placeholder="seu.email@cejam.org.br"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submitted = st.form_submit_button("🔍 Verificar", use_container_width=True)
        
        with col_btn2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.session_state.tela_recuperacao = False
            _limpar_estados_recuperacao()
            st.rerun()
        
        if submitted:
            if not email_recuperacao:
                st.error("Digite um e-mail!")
                return
            
            if not email_recuperacao.lower().endswith("@cejam.org.br"):
                st.error("E-mail deve terminar com @cejam.org.br")
                return
            
            # Verifica se usuário existe e tem pergunta de segurança
            try:
                db = DatabaseManagerPostgres()
                pergunta = db.obter_pergunta_seguranca(email_recuperacao)
                
                if pergunta:
                    st.session_state.email_recuperacao = email_recuperacao
                    st.session_state.pergunta_recuperacao = pergunta
                    st.session_state.etapa_recuperacao = 2
                    st.rerun()
                else:
                    st.error("❌ Usuário não encontrado ou não possui pergunta de segurança cadastrada. Entre em contato com o suporte.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao verificar usuário: {str(e)}")

def _etapa_pergunta_seguranca():
    """Segunda etapa: responder pergunta de segurança"""
    email_recuperacao = st.session_state.get('email_recuperacao', '')
    pergunta_recuperacao = st.session_state.get('pergunta_recuperacao', '')
    
    st.success(f"✅ Usuário encontrado: {email_recuperacao}")
    st.info("🔐 Responda sua pergunta de segurança para redefinir a senha:")
    
    st.markdown(f"**Pergunta:** {pergunta_recuperacao}")
    
    with st.form("form_resposta_seguranca"):
        resposta_informada = st.text_input(
            "Sua resposta:",
            type="password"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            verificar = st.form_submit_button("✅ Verificar", use_container_width=True)
        
        with col_btn2:
            voltar = st.form_submit_button("⬅️ Voltar", use_container_width=True)
        
        with col_btn3:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.session_state.tela_recuperacao = False
            _limpar_estados_recuperacao()
            st.rerun()
        
        if voltar:
            st.session_state.etapa_recuperacao = 1
            st.rerun()
        
        if verificar:
            if not resposta_informada:
                st.error("Digite sua resposta!")
                return
            
            try:
                db = DatabaseManagerPostgres()
                resposta_correta = db.verificar_resposta_seguranca(
                    email_recuperacao, 
                    resposta_informada
                )
                
                if resposta_correta:
                    st.session_state.etapa_recuperacao = 3
                    st.rerun()
                else:
                    st.error("❌ Resposta incorreta. Tente novamente ou entre em contato com o suporte.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao verificar resposta: {str(e)}")

def _etapa_nova_senha():
    """Terceira etapa: definir nova senha - VERSÃO CORRIGIDA"""
    email_recuperacao = st.session_state.get('email_recuperacao', '')
    
    st.success("✅ Identidade verificada! Defina sua nova senha:")
    
    with st.form("form_nova_senha_recuperacao"):
        nova_senha = st.text_input(
            "Nova Senha:",
            type="password",
            help="Mínimo 8 caracteres, com maiúscula, minúscula, número e símbolo"
        )
        
        confirmar_senha = st.text_input(
            "Confirmar Nova Senha:",
            type="password"
        )
        
        # Indicador de força da senha (apenas visual - SEM ERROS)
        if nova_senha:
            try:
                eh_valida, pontuacao, mensagens_sugestao = validar_forca_senha(nova_senha)
                
                # Converte pontuação em percentual
                forca_percentual = min(100, (pontuacao / 7) * 100)
                
                from utils.password_utils import obter_nivel_seguranca
                classificacao, emoji = obter_nivel_seguranca(pontuacao)
                
            except Exception as e:
                st.warning(f"Erro ao validar força da senha: {str(e)}")
                forca_percentual = 50
                classificacao = "Média"
                mensagens_sugestao = []
                emoji = "🟡"
            
            # Cor baseada na pontuação
            if pontuacao <= 1:
                cor = "#ff4444"  # Vermelho
            elif pontuacao <= 2:
                cor = "#ff8800"  # Laranja
            elif pontuacao <= 3:
                cor = "#ffdd00"  # Amarelo
            elif pontuacao <= 4:
                cor = "#88dd00"  # Verde claro
            elif pontuacao <= 5:
                cor = "#00cc44"  # Verde
            else:
                cor = "#00aa00"  # Verde escuro
            
            # Interface visual
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 4px solid {cor};
                margin: 15px 0;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 20px; margin-right: 10px;">{emoji}</span>
                    <strong style="font-size: 16px;">Força da senha: {classificacao}</strong>
                    <span style="margin-left: auto; color: #666; font-size: 14px;">
                        {pontuacao}/7 critérios
                    </span>
                </div>
                <div style="
                    width: 100%; 
                    background-color: #e9ecef; 
                    border-radius: 8px;
                    height: 8px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {forca_percentual}%; 
                        background-color: {cor}; 
                        height: 100%; 
                        border-radius: 8px;
                        transition: width 0.3s ease, background-color 0.3s ease;
                    "></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostra sugestões apenas como INFORMAÇÃO (não como erro)
            if mensagens_sugestao and not eh_valida:
                st.info("💡 **Sugestões para melhorar sua senha:**")
                for msg in mensagens_sugestao:
                    st.markdown(f"• {msg}")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            salvar = st.form_submit_button("✅ Salvar Senha", use_container_width=True)
        
        with col_btn2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.session_state.tela_recuperacao = False
            _limpar_estados_recuperacao()
            st.rerun()
        
        if salvar:
            # Validações básicas
            if not nova_senha:
                st.error("Digite uma nova senha!")
                return
            
            if nova_senha != confirmar_senha:
                st.error("As senhas não coincidem!")
                return
            
            # Valida força da senha APENAS quando tentar salvar
            try:
                eh_valida, pontuacao, mensagens_erro = validar_forca_senha(nova_senha)
                
                if not eh_valida:
                    st.error("❌ Senha não atende aos critérios mínimos de segurança:")
                    for msg in mensagens_erro:
                        st.error(f"• {msg}")
                    return
                
            except Exception as e:
                st.error("❌ Por favor, use uma senha com pelo menos 8 caracteres, incluindo maiúscula, minúscula, número e símbolo.")
                return
            
            # CORREÇÃO: Chama método com parâmetros corretos
            try:
                db = DatabaseManagerPostgres()
                # Seu método espera 4 parâmetros, então passe None nos opcionais
                sucesso = db.atualizar_senha_usuario(email_recuperacao, nova_senha, None, None)
                
                if sucesso:
                    st.success("✅ Senha alterada com sucesso! Faça login com a nova senha.")
                    time.sleep(2)
                    
                    # Limpa session states e volta ao login
                    st.session_state.tela_recuperacao = False
                    _limpar_estados_recuperacao()
                    st.rerun()
                else:
                    st.error("❌ Erro ao alterar senha. Tente novamente.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao salvar nova senha: {str(e)}")

def _limpar_estados_recuperacao():
    """Limpa todos os estados relacionados à recuperação"""
    estados_para_limpar = [
        'etapa_recuperacao',
        'email_recuperacao',
        'pergunta_recuperacao'
    ]
    
    for estado in estados_para_limpar:
        if estado in st.session_state:
            del st.session_state[estado]