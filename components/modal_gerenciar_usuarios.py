import streamlit as st
import pandas as pd
from data.manager_postgre import DatabaseManagerPostgres
from utils.password_utils import gerar_senha_temporaria
import time

def modal_gerenciar_usuarios():
    """Interface para gerenciar usuários do sistema - apenas para custos@cejam.org.br"""
    
    # Verifica se é o usuário autorizado
    email_usuario = st.session_state.get('email_usuario', '')
    if email_usuario != 'custos@cejam.org.br':
        st.warning("⚠️ Acesso restrito apenas para custos@cejam.org.br")
        return
    
    st.markdown("### 👥 Gerenciamento de Usuários")
    
    # Abas do gerenciamento
    aba_lista, aba_criar, aba_resetar, aba_deletar = st.tabs(["📋 Lista de Usuários", "➕ Criar Usuário", "🔄 Reset de Senha", "🗑️ Deletar Usuário"])
    
    # ABA 1: Lista de usuários
    with aba_lista:
        st.markdown("#### 📋 Usuários Cadastrados")
        
        try:
            db = DatabaseManagerPostgres()
            usuarios = db.listar_usuarios()
            
            if usuarios:
                # Converte para DataFrame para melhor visualização
                df_usuarios = pd.DataFrame(usuarios, columns=[
                    'ID', 'Nome', 'Email', 'Unidade', 'Primeira Vez', 
                    'Tentativas Login', 'Conta Bloqueada', 'Data Criação'
                ])
                
                # Formatar colunas booleanas
                df_usuarios['Primeira Vez'] = df_usuarios['Primeira Vez'].apply(lambda x: "✅ Sim" if x else "❌ Não")
                df_usuarios['Conta Bloqueada'] = df_usuarios['Conta Bloqueada'].apply(lambda x: "🔒 Sim" if x else "✅ Não")
                
                # Exibe tabela
                st.dataframe(
                    df_usuarios[['Nome', 'Email', 'Unidade', 'Primeira Vez', 'Tentativas Login', 'Conta Bloqueada']],
                    use_container_width=True,
                    height=400
                )
                
                # Estatísticas
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    st.metric("Total Usuários", len(usuarios))
                
                with col_stats2:
                    primeiro_acesso = len([u for u in usuarios if u[4]])  # primeira_vez = True
                    st.metric("Primeiro Acesso", primeiro_acesso)
                
                with col_stats3:
                    contas_bloqueadas = len([u for u in usuarios if u[6]])  # conta_bloqueada = True
                    st.metric("Contas Bloqueadas", contas_bloqueadas)
                
                with col_stats4:
                    tentativas_altas = len([u for u in usuarios if u[5] >= 3])  # tentativas >= 3
                    st.metric("Tentativas Altas", tentativas_altas)
            else:
                st.info("Nenhum usuário cadastrado.")
                
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {str(e)}")
    
    # ABA 2: Criar novo usuário
    with aba_criar:
        st.markdown("#### ➕ Criar Novo Usuário")
        
        with st.form("form_criar_usuario"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome_usuario = st.text_input(
                    "Nome Completo:",
                    placeholder="João Silva"
                )
                
                email_usuario_novo = st.text_input(
                    "E-mail:",
                    placeholder="joao.silva@cejam.org.br"
                )
            
            with col2:
                unidade_usuario = st.selectbox(
                    "Unidade:",
                    [
                        "AMA 24H CAPAO REDONDO",
                        "AMA PQ NOVO SANTO AMARO",
                        "PA JD MACEDONIA",
                        "UBS PQ NOVO SANTO AMARO",
                        "UPA JD ANGELA",
                        "UPA VERA CRUZ",
                        "UBS ALTO DO IPIRANGA",
                        "USF BIRITIBA USSU",
                        "USF CHACARA GUANABARA",
                        "USF COCUERA",
                        "USF JD AEROPORTO II",
                        "USF JD AEROPORTO III",
                        "USF JD LAYR",
                        "USF JD MARGARIDA",
                        "USF JD PIATÃ",
                        "USF JD PLANALTO",
                        "USF NOVE DE JULHO",
                        "USF TABOÃO-LAMBARI",
                        "USF TAIAÇUPEBA",
                        "AME CARAPICUÍBA",
                        "LUCY MONTORO SANTOS",
                        "UNICA FISIOTERAPIA",
                        "UNICA JUNDIAPEBA",
                        "AMA/UBS JD CAPELA",
                        "AMA/UBS PQ FERNANDA",
                        "AMAE CAPAO REDONDO",
                        "CAPS ADULTO II JARDIM LIDIA",
                        "CAPS ALCOOL DROGA III JD ANGELA",
                        "CAPS INF JUVENIL II MBOI MIRIM",
                        "CEO CAPAO REDONDO",
                        "CEO II VERA CRUZ",
                        "CER IV M BOI MIRIM",
                        "UBS ALTO DA RIVIERA",
                        "UBS CHACARA STA MARIA",
                        "UBS CIDADE IPAVA",
                        "UBS HORIZONTE AZUL",
                        "UBS JD ARACATI",
                        "UBS JD CAICARA",
                        "UBS JD COIMBRA",
                        "UBS JD GUARUJA",
                        "UBS JD HERCULANO",
                        "UBS JD LIDIA",
                        "UBS JD NAKAMURA",
                        "UBS JD STA MARGARIDA",
                        "UBS PQ DO LAGO",
                        "UBS SANTA LUCIA",
                        "UBS VERA CRUZ",
                        "UBS VILA CALU",
                        "LUCY MONTORO PARIQUERA-AÇU",
                        "HOSPITAL MOYSES DEUTSCH MBOI MIRIM",
                        "NUCLEO TECNICO REGIONAL",
                        "HOSPITAL MUNICIPAL EVANDRO FREIRE",
                        "HOSPITAL ESTADUAL DE FRANCO DA ROCHA",
                        "HOSPITAL GERAL DE ITAPEVI",
                        "HOSPITAL E MATERNIDADE DE SÃO ROQUE",
                        "HOSPITAL E MATERNIDADE MARISKA RIBEIRO",
                        "HOSPITAL DIA CAMPO LIMPO",
                        "HOSPITAL DIA M BOI MIRIM I",
                        "HOSPITAL DIA M BOI MIRIM II",
                        "LABORATORIO LACEN",
                        "SEDE"
                    ]
                )
                
                tipo_senha = st.radio(
                    "Tipo de senha:",
                    ["Gerar senha temporária", "Definir senha específica"]
                )
            
            senha_especifica = ""
            if tipo_senha == "Definir senha específica":
                senha_especifica = st.text_input(
                    "Senha:",
                    type="password",
                    help="Deixe vazio para gerar automaticamente"
                )
            
            # Botões
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.form_submit_button("✅ Criar Usuário", use_container_width=True):
                    # Validações
                    if not nome_usuario:
                        st.error("Digite o nome do usuário!")
                        return
                    
                    if not email_usuario_novo:
                        st.error("Digite o e-mail do usuário!")
                        return
                    
                    if not email_usuario_novo.lower().endswith("@cejam.org.br"):
                        st.error("E-mail deve terminar com @cejam.org.br")
                        return
                    
                    # Cria usuário
                    try:
                        db = DatabaseManagerPostgres()
                        
                        senha_final = senha_especifica if senha_especifica else None
                        
                        sucesso, resultado = db.criar_usuario(
                            nome_usuario,
                            email_usuario_novo,
                            unidade_usuario,
                            senha_final
                        )
                        
                        if sucesso:
                            if senha_especifica:
                                # Usuário criado com senha específica
                                st.success(f"✅ Usuário criado com sucesso!")
                                st.info(f"📧 E-mail: {email_usuario_novo}")
                                st.info(f"🔑 Senha definida conforme informado")
                                
                                # Enviar email de boas-vindas (sem senha)
                                assunto_email = "Bem-vindo ao Sistema de Relatório de Coleta - CEJAM"
                                corpo_email = f"""
                Olá {nome_usuario},

                Sua conta foi criada no Relatório de Coleta - CEJAM!

                📧 E-mail: {email_usuario_novo}
                🏢 Unidade: {unidade_usuario}
                🔑 Senha: Definida pelo administrador

                Acesse o sistema e faça seu primeiro login.

                Em caso de dúvidas, entre em contato com o suporte.

                Atenciosamente,
                Equipe CEJAM
                                """.strip()
                                
                            else:
                                # Usuário criado com senha temporária - ENVIAR POR EMAIL
                                senha_temporaria = resultado
                                
                                st.success(f"✅ Usuário criado com sucesso!")
                                st.info(f"📧 E-mail: {email_usuario_novo}")
                                
                                # Prepara email com senha temporária
                                assunto_email = "Sua conta foi criada - Sistema de Relatório de Coleta - CEJAM"
                                corpo_email = f"""
                Olá {nome_usuario},

                Sua conta foi criada no Relatório de Coleta - CEJAM!

                📧 E-mail: {email_usuario_novo}
                🏢 Unidade: {unidade_usuario}
                🔑 Senha temporária: {senha_temporaria}

                IMPORTANTE: Esta é uma senha temporária. No seu primeiro acesso, você deverá:
                1. Fazer login com esta senha
                2. Definir uma nova senha segura
                3. Cadastrar uma pergunta de segurança

                Acesse o sistema e faça seu primeiro login.

                Em caso de dúvidas, entre em contato com o suporte.

                Atenciosamente,
                Equipe CEJAM
                                """.strip()
                            
                            # Enviar email
                            try:
                                from utils.email_utils import enviar_email
                                
                                st.info("📤 Enviando email para o usuário...")
                                
                                email_enviado = enviar_email(
                                    email_usuario_novo, 
                                    assunto_email, 
                                    corpo_email
                                )
                                
                                if email_enviado:
                                    st.success("📧 Email enviado com sucesso para o usuário!")
                                    if not senha_especifica:
                                        st.success("🔐 Senha temporária enviada por email")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao enviar email. Verifique as configurações.")
                                    if not senha_especifica:
                                        st.warning(f"⚠️ ATENÇÃO: Senha temporária: **{senha_temporaria}**")
                                        st.info("Informe manualmente esta senha ao usuário.")
                                        
                            except Exception as e:
                                st.error(f"❌ Erro ao enviar email: {str(e)}")
                                if not senha_especifica:
                                    st.warning(f"⚠️ ATENÇÃO: Senha temporária: **{senha_temporaria}**")
                                    st.info("Informe manualmente esta senha ao usuário.")
                        else:
                            st.error(f"❌ {resultado}")
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao criar usuário: {str(e)}")

            
            with col_btn2:
                if st.form_submit_button("🔄 Limpar", use_container_width=True):
                    st.rerun()
    
    # ABA 3: Reset de senha - VERSÃO ATUALIZADA COM ENVIO DE EMAIL
    with aba_resetar:
        st.markdown("#### 🔄 Resetar Senha de Usuário")
        
        # Lista usuários para seleção
        try:
            db = DatabaseManagerPostgres()
            usuarios_list = db.listar_usuarios()
            
            if usuarios_list:
                # Cria lista de opções (nome - email)
                opcoes_usuarios = [f"{u[1]} - {u[2]}" for u in usuarios_list]
                
                with st.form("form_reset_senha"):
                    usuario_selecionado = st.selectbox(
                        "Selecione o usuário:",
                        [""] + opcoes_usuarios
                    )
                    
                    tipo_reset = st.radio(
                        "Tipo de reset:",
                        [
                            "Gerar nova senha temporária",
                            "Desbloquear conta (zerar tentativas)",
                            "Marcar como primeiro acesso",
                            "Reset completo (senha + desbloqueio + primeiro acesso)"
                        ]
                    )
                    
                    if st.form_submit_button("🔄 Executar Reset", use_container_width=True):
                        if not usuario_selecionado:
                            st.error("Selecione um usuário!")
                            return
                        
                        # Extrai dados do usuário selecionado
                        partes_usuario = usuario_selecionado.split(" - ")
                        nome_usuario = partes_usuario[0]
                        email_reset = partes_usuario[1]
                        
                        try:
                            db = DatabaseManagerPostgres()
                            
                            # Busca dados completos do usuário para o email
                            usuario_dados = None
                            for u in usuarios_list:
                                if u[2] == email_reset:  # u[2] é o email
                                    usuario_dados = u
                                    break
                            
                            unidade_usuario = usuario_dados[3] if usuario_dados else "Não informado"
                            
                            if tipo_reset == "Gerar nova senha temporária":
                                nova_senha_temp = gerar_senha_temporaria()
                                sucesso = db.resetar_senha_usuario(email_reset, nova_senha_temp)
                                
                                if sucesso:
                                    st.success("✅ Senha resetada com sucesso!")
                                    
                                    # Preparar email
                                    assunto_email = "Sua senha foi resetada - Sistema de Relatório de Coleta - CEJAM"
                                    corpo_email = f"""
    Olá {nome_usuario},

    Sua senha foi resetada no Sistema de Relatório de Coleta - CEJAM.

    📧 E-mail: {email_reset}
    🏢 Unidade: {unidade_usuario}
    🔑 Nova senha temporária: {nova_senha_temp}

    IMPORTANTE: Esta é uma senha temporária. No seu próximo acesso, você deverá:
    1. Fazer login com esta nova senha
    2. Definir uma nova senha segura

    Acesse o sistema e faça login com a nova senha.

    Em caso de dúvidas, entre em contato com o suporte.

    Atenciosamente,
    Equipe CEJAM
                                    """.strip()
                                    
                                    # Enviar email
                                    try:
                                        from utils.email_utils import enviar_email
                                        
                                        st.info("📤 Enviando nova senha por email...")
                                        
                                        email_enviado = enviar_email(email_reset, assunto_email, corpo_email)
                                        
                                        if email_enviado:
                                            st.success("📧 Nova senha enviada por email com sucesso!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao enviar email.")
                                            st.warning(f"⚠️ ATENÇÃO: Nova senha temporária: **{nova_senha_temp}**")
                                            st.info("Informe manualmente esta senha ao usuário.")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Erro ao enviar email: {str(e)}")
                                        st.warning(f"⚠️ ATENÇÃO: Nova senha temporária: **{nova_senha_temp}**")
                                        st.info("Informe manualmente esta senha ao usuário.")
                                else:
                                    st.error("❌ Erro ao resetar senha.")
                            
                            elif tipo_reset == "Desbloquear conta (zerar tentativas)":
                                sucesso = db.desbloquear_conta_usuario(email_reset)
                                
                                if sucesso:
                                    st.success("✅ Conta desbloqueada com sucesso!")
                                    
                                    # Preparar email
                                    assunto_email = "Sua conta foi desbloqueada - Sistema de Relatório de Coleta - CEJAM"
                                    corpo_email = f"""
    Olá {nome_usuario},

    Sua conta foi desbloqueada no Sistema de Relatório de Coleta - CEJAM.

    📧 E-mail: {email_reset}
    🏢 Unidade: {unidade_usuario}
    🔓 Status: Conta desbloqueada - tentativas de login zeradas

    Você pode agora acessar o sistema normalmente com sua senha atual.

    Se não lembrar de sua senha, solicite um reset de senha ao suporte.

    Em caso de dúvidas, entre em contato com o suporte.

    Atenciosamente,
    Equipe CEJAM
                                    """.strip()
                                    
                                    # Enviar email
                                    try:
                                        from utils.email_utils import enviar_email
                                        
                                        st.info("📤 Enviando notificação por email...")
                                        
                                        email_enviado = enviar_email(email_reset, assunto_email, corpo_email)
                                        
                                        if email_enviado:
                                            st.success("📧 Notificação de desbloqueio enviada por email!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Conta desbloqueada, mas houve erro ao enviar email de notificação.")
                                            
                                    except Exception as e:
                                        st.warning(f"⚠️ Conta desbloqueada, mas erro ao enviar email: {str(e)}")
                                else:
                                    st.error("❌ Erro ao desbloquear conta.")
                            
                            elif tipo_reset == "Marcar como primeiro acesso":
                                sucesso = db.marcar_primeiro_acesso(email_reset)
                                
                                if sucesso:
                                    st.success("✅ Usuário marcado para primeiro acesso!")
                                    
                                    # Preparar email
                                    assunto_email = "Redefinição de senha necessária - Sistema de Relatório de Coleta - CEJAM"
                                    corpo_email = f"""
    Olá {nome_usuario},

    Sua conta foi configurada para redefinição de senha no Sistema de Relatório de Coleta - CEJAM.

    📧 E-mail: {email_reset}
    🏢 Unidade: {unidade_usuario}
    🔄 Status: Redefinição de senha obrigatória no próximo login

    IMPORTANTE: No seu próximo acesso, você deverá:
    1. Fazer login com sua senha atual
    2. Definir uma nova senha segura
    3. Cadastrar/atualizar sua pergunta de segurança

    Se não lembrar de sua senha atual, solicite um reset de senha ao suporte.

    Em caso de dúvidas, entre em contato com o suporte.

    Atenciosamente,
    Equipe CEJAM
                                    """.strip()
                                    
                                    # Enviar email
                                    try:
                                        from utils.email_utils import enviar_email
                                        
                                        st.info("📤 Enviando notificação por email...")
                                        
                                        email_enviado = enviar_email(email_reset, assunto_email, corpo_email)
                                        
                                        if email_enviado:
                                            st.success("📧 Notificação enviada por email!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Primeiro acesso marcado, mas houve erro ao enviar email de notificação.")
                                            
                                    except Exception as e:
                                        st.warning(f"⚠️ Primeiro acesso marcado, mas erro ao enviar email: {str(e)}")
                                else:
                                    st.error("❌ Erro ao marcar primeiro acesso.")
                            
                            elif tipo_reset == "Reset completo (senha + desbloqueio + primeiro acesso)":
                                nova_senha_temp = gerar_senha_temporaria()
                                sucesso = db.reset_completo_usuario(email_reset, nova_senha_temp)
                                
                                if sucesso:
                                    st.success("✅ Reset completo realizado com sucesso!")
                                    
                                    # Preparar email
                                    assunto_email = "Reset completo de conta - Sistema de Relatório de Coleta - CEJAM"
                                    corpo_email = f"""
    Olá {nome_usuario},

    Sua conta passou por um reset completo no Sistema de Relatório de Coleta - CEJAM.

    📧 E-mail: {email_reset}
    🏢 Unidade: {unidade_usuario}
    🔑 Nova senha temporária: {nova_senha_temp}

    🔄 ALTERAÇÕES REALIZADAS:
    ✅ Nova senha temporária gerada
    ✅ Conta desbloqueada (tentativas zeradas)
    ✅ Marcado para primeiro acesso

    IMPORTANTE: No seu próximo acesso, você deverá:
    1. Fazer login com a senha temporária informada acima
    2. Definir uma nova senha segura
    3. Cadastrar/atualizar sua pergunta de segurança

    Acesse o sistema e faça login com a nova senha temporária.

    Em caso de dúvidas, entre em contato com o suporte.

    Atenciosamente,
    Equipe CEJAM
                                    """.strip()
                                    
                                    # Enviar email
                                    try:
                                        from utils.email_utils import enviar_email
                                        
                                        st.info("📤 Enviando nova senha e informações por email...")
                                        
                                        email_enviado = enviar_email(email_reset, assunto_email, corpo_email)
                                        
                                        if email_enviado:
                                            st.success("📧 Informações de reset completo enviadas por email!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao enviar email.")
                                            st.warning(f"⚠️ ATENÇÃO: Nova senha temporária: **{nova_senha_temp}**")
                                            st.info("⚠️ Reset completo realizado. Informe manualmente as informações ao usuário.")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Erro ao enviar email: {str(e)}")
                                        st.warning(f"⚠️ ATENÇÃO: Nova senha temporária: **{nova_senha_temp}**")
                                        st.info("⚠️ Reset completo realizado. Informe manualmente as informações ao usuário.")
                                else:
                                    st.error("❌ Erro ao executar reset completo.")
                            
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
            else:
                st.info("Nenhum usuário cadastrado para reset.")
                
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {str(e)}")

        # Adicionar informações sobre o envio de emails
        with st.expander("ℹ️ Informações sobre Envio de Email"):
            st.markdown("""
            **📧 Envio Automático de Email:**
            
            - **Reset de Senha:** Nova senha temporária é enviada por email
            - **Desbloqueio:** Notificação de que a conta foi desbloqueada
            - **Primeiro Acesso:** Instruções sobre redefinição obrigatória
            - **Reset Completo:** Todas as informações e nova senha
            
            **🔧 Em caso de falha no envio:**
            
            - As operações são executadas mesmo se o email falhar
            - Senhas temporárias são exibidas na tela como backup
            - O usuário deve ser informado manualmente se necessário
            
            **⚠️ Importante:**
            
            - Verifique as configurações de email se houver falhas constantes
            - Senhas temporárias são válidas até serem alteradas
            """)

    with aba_deletar:
        st.markdown("#### 🗑️ Deletar Usuário")
        
        st.warning("⚠️ **ATENÇÃO:** Esta ação é irreversível! O usuário será removido permanentemente do sistema.")
        
        # Lista usuários para seleção
        try:
            db = DatabaseManagerPostgres()
            usuarios_list = db.listar_usuarios()
            
            if usuarios_list:
                # Remove o próprio usuário custos@cejam.org.br da lista para não se auto-deletar
                usuarios_filtrados = [u for u in usuarios_list if u[2] != 'custos@cejam.org.br']
                
                if usuarios_filtrados:
                    # Cria lista de opções (nome - email - unidade)
                    opcoes_usuarios = [f"{u[1]} - {u[2]} - {u[3]}" for u in usuarios_filtrados]
                    
                    # SEM FORM - Componentes diretos
                    usuario_selecionado = st.selectbox(
                        "Selecione o usuário para deletar:",
                        [""] + opcoes_usuarios,
                        key="select_usuario_deletar"
                    )
                    
                    # Checkbox de confirmação
                    confirmacao = st.checkbox(
                        "✅ Confirmo que desejo deletar este usuário permanentemente",
                        help="Esta ação não pode ser desfeita",
                        key="confirm_delete_1"
                    )
                    
                    # Segundo nível de confirmação - só aparece se tiver usuário selecionado E primeira confirmação
                    confirmacao_final = False
                    if usuario_selecionado and confirmacao:
                        st.error("⚠️ **ÚLTIMA CONFIRMAÇÃO:** Você tem certeza que deseja deletar este usuário?")
                        confirmacao_final = st.checkbox(
                            "🔴 SIM, tenho certeza absoluta que quero deletar este usuário",
                            key="confirm_delete_2"
                        )
                    
                    # Verifica se todas as condições estão atendidas
                    pode_deletar = bool(usuario_selecionado and confirmacao and confirmacao_final)
                    
                    st.markdown("---")
                    
                    # Botões
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button(
                            "🗑️ DELETAR USUÁRIO", 
                            use_container_width=True, 
                            type="primary",
                            disabled=not pode_deletar,
                            key="btn_deletar_usuario"
                        ):
                            if not usuario_selecionado:
                                st.error("Selecione um usuário!")
                            elif not confirmacao or not confirmacao_final:
                                st.error("Confirme a operação marcando ambas as caixas!")
                            else:
                                # Extrai dados do usuário selecionado
                                partes = usuario_selecionado.split(" - ")
                                nome_usuario = partes[0]
                                email_deletar = partes[1]
                                
                                try:
                                    db = DatabaseManagerPostgres()
                                    
                                    # Confirma novamente o email para evitar erros
                                    if email_deletar == 'custos@cejam.org.br':
                                        st.error("❌ Não é possível deletar o usuário administrador!")
                                    else:
                                        sucesso = db.deletar_usuario(email_deletar)
                                        
                                        if sucesso:
                                            st.success(f"✅ Usuário '{nome_usuario}' deletado com sucesso!")
                                            st.info("🔄 Atualizando lista de usuários...")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao deletar usuário. Verifique se não há dependências.")
                                            
                                except Exception as e:
                                    st.error(f"❌ Erro ao deletar usuário: {str(e)}")
                    
                    with col_btn2:
                        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar_delete"):
                            # Lista de keys para limpar
                            keys_deletar = [
                                "select_usuario_deletar",
                                "confirm_delete_1", 
                                "confirm_delete_2",
                            ]
                            
                            # Limpa todos os estados relacionados
                            contador_limpeza = 0
                            for key in keys_deletar:
                                if key in st.session_state:
                                    del st.session_state[key]
                                    contador_limpeza += 1
                            
                            if contador_limpeza > 0:
                                st.success(f"🧹 {contador_limpeza} campo(s) limpo(s) com sucesso!")                           
                            time.sleep(1)
                            st.rerun()
                    # Informações importantes
                    with st.expander("ℹ️ Informações Importantes sobre Exclusão"):
                        st.markdown("""
                        **⚠️ Ao deletar um usuário:**
                        
                        - O usuário será removido permanentemente do banco de dados
                        - Não será possível recuperar os dados do usuário
                        - Históricos de login e atividades podem ser perdidos
                        - O email ficará disponível para novo cadastro
                        
                        **🛡️ Segurança:**
                        
                        - O usuário administrador (custos@cejam.org.br) não pode ser deletado
                        - É necessária confirmação dupla para executar a exclusão
                        - Recomenda-se fazer backup antes de exclusões em massa
                        
                        **💡 Alternativas à exclusão:**
                        
                        - Use "Reset de Senha" para reativar contas com problemas
                        - Use "Desbloquear Conta" para resolver bloqueios
                        - Considere apenas desativar ao invés de deletar (se implementado)
                        """)
                else:
                    st.info("Não há usuários disponíveis para exclusão (além do administrador).")
            else:
                st.info("Nenhum usuário cadastrado no sistema.")
                
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {str(e)}")