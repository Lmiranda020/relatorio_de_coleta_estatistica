import streamlit as st
from utils.password_utils import validar_forca_senha
from data.manager_postgre import DatabaseManagerPostgres
import time

def modal_cadastro_senha():
    """Modal para cadastro/alteração de senha no primeiro acesso - Versão Corrigida"""
    
    # Limpa a tela e mostra só o modal
    st.markdown("---")
    
    # Container centralizado
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        
        st.markdown("### 🔐 Definir Nova Senha")
        
        if st.session_state.get('primeiro_acesso', False):
            st.info("👋 Primeiro acesso detectado! Defina sua senha pessoal para continuar.")
        
        # Email do usuário
        email_usuario = st.session_state.get('email_usuario', '')
        if email_usuario:
            st.markdown(f"**📧 Usuário:** {email_usuario}")
        
        st.markdown("---")
        
        # Campos de senha
        nova_senha = st.text_input(
            "🔑 Nova Senha:",
            type="password",
            help="Mínimo 8 caracteres, com maiúscula, minúscula, número e símbolo",
            key="nova_senha_input"
        )
        
        confirmar_senha = st.text_input(
            "🔑 Confirmar Senha:",
            type="password",
            key="confirmar_senha_input"
        )
        
        # Indicador de força da senha
        senha_valida = False
        if nova_senha:
            try:
                eh_valida, pontuacao, mensagens_sugestao = validar_forca_senha(nova_senha)
                senha_valida = eh_valida
                
                # Converte pontuação em percentual
                forca_percentual = min(100, (pontuacao / 7) * 100)
                
                # Determina classificação e cor
                if pontuacao <= 1:
                    classificacao, cor, emoji = "Muito Fraca", "#ff4444", "🔴"
                elif pontuacao <= 2:
                    classificacao, cor, emoji = "Fraca", "#ff8800", "🟠"
                elif pontuacao <= 3:
                    classificacao, cor, emoji = "Razoável", "#ffdd00", "🟡"
                elif pontuacao <= 4:
                    classificacao, cor, emoji = "Boa", "#88dd00", "🟢"
                elif pontuacao <= 5:
                    classificacao, cor, emoji = "Muito Boa", "#00cc44", "🟢"
                else:
                    classificacao, cor, emoji = "Excelente", "#00aa00", "🟢"
                
                # Barra de progresso simples
                st.markdown(f"""
                **{emoji} Força da senha: {classificacao}**
                """)
                
                st.progress(forca_percentual / 100)
                
                # Mostra sugestões se senha não for válida
                if not eh_valida and mensagens_sugestao:
                    st.error("❌ **Senha não atende aos critérios obrigatórios:**")
                    for msg in mensagens_sugestao:
                        st.error(f"• {msg}")
                elif eh_valida:
                    st.success("✅ Senha atende a todos os critérios de segurança!")
            
            except Exception as e:
                st.warning("Erro ao avaliar força da senha")
        
        # Pergunta de segurança (OBRIGATÓRIA)
        st.markdown("**🔐 Pergunta de Segurança (OBRIGATÓRIO):**")
        st.markdown("*Esta pergunta será usada para recuperar sua senha caso necessário.*")
        
        pergunta_seguranca = st.selectbox(
            "Escolha uma pergunta:",
            [
                "",
                "Qual é o ramal da recepção da unidade?",
                "Qual é o CEP da unidade?",
                "Qual é o nome da rua onde fica a unidade?",
                "Qual é o horário de abertura da unidade?",
                "Qual é o número do CNES da unidade?",
                "Personalizada"
            ],
            key="pergunta_select"
        )
        
        pergunta_personalizada = ""
        resposta_seguranca = ""
        pergunta_final = ""
        
        if pergunta_seguranca == "Personalizada":
            pergunta_personalizada = st.text_input(
                "Digite sua pergunta:", 
                placeholder="Ex: Qual o nome do seu professor favorito?",
                key="pergunta_personalizada_input"
            )
            pergunta_final = pergunta_personalizada
        elif pergunta_seguranca and pergunta_seguranca != "":
            pergunta_final = pergunta_seguranca
        
        if pergunta_final:
            resposta_seguranca = st.text_input(
                "Resposta:", 
                type="password",
                placeholder="Digite sua resposta (será criptografada)",
                help="Esta resposta será necessária para recuperar sua senha",
                key="resposta_seguranca_input"
            )
        
        st.markdown("---")
        
        # Botões
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✅ Salvar Senha", use_container_width=True, type="primary"):
                # Lista de erros para mostrar todos de uma vez
                erros = []
                
                # Validação 1: Senha não pode estar vazia
                if not nova_senha:
                    erros.append("Digite uma senha!")
                
                # Validação 2: Confirmação de senha
                if nova_senha != confirmar_senha:
                    erros.append("As senhas não coincidem!")
                
                # Validação 3: Força da senha (OBRIGATÓRIO)
                if nova_senha:
                    try:
                        eh_valida, pontuacao, mensagens_erro = validar_forca_senha(nova_senha)
                        
                        if not eh_valida:
                            erros.append("Senha não atende aos critérios mínimos de segurança:")
                            erros.extend([f"  • {msg}" for msg in mensagens_erro])
                    except Exception as e:
                        erros.append("Erro ao validar senha. Use pelo menos 8 caracteres com maiúscula, minúscula, número e símbolo.")
                
                # Validação 4: Pergunta de segurança (OBRIGATÓRIA)
                if not pergunta_final or pergunta_final.strip() == "":
                    erros.append("Selecione uma pergunta de segurança!")
                
                # Validação 5: Resposta da pergunta (OBRIGATÓRIA)
                if pergunta_final and (not resposta_seguranca or resposta_seguranca.strip() == ""):
                    erros.append("Digite a resposta da pergunta de segurança!")
                
                # Validação 6: Se pergunta personalizada, deve ter conteúdo
                if pergunta_seguranca == "Personalizada" and (not pergunta_personalizada or pergunta_personalizada.strip() == ""):
                    erros.append("Digite sua pergunta personalizada!")
                
                # Se há erros, mostra todos
                if erros:
                    st.error("❌ **Corrija os seguintes problemas antes de continuar:**")
                    for erro in erros:
                        if erro.startswith("  •"):  # Suberro de validação de senha
                            st.error(erro)
                        else:
                            st.error(f"• {erro}")
                
                # Se não há erros, procede com o salvamento
                else:
                    try:
                        with st.spinner("Salvando nova senha..."):
                            db = DatabaseManagerPostgres()
                            
                            sucesso = db.definir_senha_primeiro_acesso(
                                email_usuario, 
                                nova_senha,
                                pergunta_final,
                                resposta_seguranca
                            )
                            
                            if sucesso:
                                st.success("✅ Senha definida com sucesso!")
                                st.info("🔄 Redirecionando para o sistema...")
                                time.sleep(3)
                                
                                # Agora sim, define como logado
                                st.session_state['usuario_logado'] = True
                                st.session_state['modal_cadastro_senha'] = False
                                
                                # Remove flags de primeiro acesso
                                if 'primeiro_acesso' in st.session_state:
                                    del st.session_state['primeiro_acesso']
                                
                                st.rerun()
                            else:
                                st.error("❌ Erro ao salvar senha. Tente novamente.")
                                
                    except Exception as e:
                        st.error(f"❌ Erro interno: {str(e)}")
        
        with col_btn2:
            if st.button("❌ Cancelar Login", use_container_width=True):
                # Limpa todos os estados relacionados
                st.session_state['modal_cadastro_senha'] = False
                st.session_state['usuario_logado'] = False
                if 'primeiro_acesso' in st.session_state:
                    del st.session_state['primeiro_acesso']
                if 'email_usuario' in st.session_state:
                    del st.session_state['email_usuario']
                if 'unidade_usuario' in st.session_state:
                    del st.session_state['unidade_usuario']
                st.rerun()
        
        # Instruções de ajuda
        with st.expander("ℹ️ Ajuda - Critérios de Senha Segura"):
            st.markdown("""
            **⚠️ TODOS os critérios abaixo são OBRIGATÓRIOS:**
            
            ✅ **Pelo menos 8 caracteres**
            
            ✅ **Pelo menos 1 letra maiúscula** (A-Z)
            
            ✅ **Pelo menos 1 letra minúscula** (a-z)  
            
            ✅ **Pelo menos 1 número** (0-9)
            
            ✅ **Pelo menos 1 caractere especial** (!@#$%^&* etc.)
            
            ✅ **Pergunta e resposta de segurança**
            
            **Exemplo de senha válida:** `MinhaSenh@123`
            
            **❌ Senhas que NÃO serão aceitas:**
            - 123456, password, qwerty, abc123
            - Senhas muito comuns ou sequências simples
            - Qualquer senha que não atenda aos critérios acima
            
            **🔐 A pergunta de segurança é obrigatória e será usada para recuperação de senha.**
            """)
        
        # Aviso importante
        st.warning("⚠️ **IMPORTANTE:** Todos os critérios são obrigatórios. O sistema não permitirá senhas fracas ou sem pergunta de segurança.")