import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import schedule
import time
import os
from dotenv import load_dotenv
from data.manager_postgre import DatabaseManagerPostgres

load_dotenv()

class SistemaEmailsAutomatico:
    """
    Sistema autônomo de envio de emails
    VERSÃO COM MODO DE TESTE
    """
    
    def __init__(self, modo_teste=False, tipo_teste=None):
        self.db = DatabaseManagerPostgres()
        self.modo_teste = modo_teste
        self.tipo_teste = tipo_teste  # 'disponivel', 'lembrete' ou 'urgente'
        
        # Configuração do email
        self.EMAIL_REMETENTE = os.getenv('EMAIL_USER', 'larissa.miranda@cejam.org.br')
        self.SENHA_EMAIL = os.getenv('EMAIL_PASSWORD', 'qujx wlhb urnq sfby')
        self.SMTP_SERVER = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('EMAIL_PORT', '587'))
        
        # Feriados nacionais de 2025
        self.FERIADOS_2025 = [
            datetime(2025, 1, 1), datetime(2025, 4, 18), datetime(2025, 4, 21),
            datetime(2025, 5, 1), datetime(2025, 6, 19), datetime(2025, 9, 7),
            datetime(2025, 10, 12), datetime(2025, 11, 2), datetime(2025, 11, 15),
            datetime(2025, 11, 20), datetime(2025, 12, 25),
        ]
    
    def is_dia_util(self, data):
        """Verifica se é dia útil"""
        if data.weekday() >= 5:
            return False
        data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
        return data_sem_hora not in self.FERIADOS_2025
    
    def proximo_dia_util(self, data):
        """Retorna próximo dia útil"""
        data_atual = data
        while not self.is_dia_util(data_atual):
            data_atual += timedelta(days=1)
        return data_atual
    
    def calcular_competencia_anterior(self):
        """Calcula competência do mês anterior no formato 'set/2025'"""
        hoje = datetime.now()
        mes_anterior = hoje - relativedelta(months=1)
        meses_pt = {
            1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
        }
        mes_nome = meses_pt[mes_anterior.month]
        return f"{mes_nome}/{mes_anterior.year}"
    
    def obter_todas_unidades(self):
        """Busca todas as unidades cadastradas"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT u.nome, u.email, u.unidade
                FROM usuarios u
                WHERE u.email != 'custos@cejam.org.br'
            """)
            
            return [
                {'nome': nome, 'email': email, 'unidade': unidade}
                for nome, email, unidade in cursor.fetchall()
            ]
        except Exception as e:
            print(f"❌ Erro ao obter unidades: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def obter_unidades_pendentes(self, competencia):
        """Identifica unidades que não preencheram a competência"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Busca todas as unidades cadastradas
            cursor.execute("""
                SELECT DISTINCT u.nome, u.email, u.unidade
                FROM usuarios u
                WHERE u.email != 'custos@cejam.org.br'
            """)
            todas_unidades = cursor.fetchall()
            
            # Busca unidades que JÁ preencheram (usa LEFT JOIN para debug)
            cursor.execute("""
                SELECT DISTINCT unidade 
                FROM preenchimentos_finalizados 
                WHERE competencia = %s
            """, (competencia,))
            unidades_preenchidas = {row[0] for row in cursor.fetchall()}
            
            print(f"\n📊 DEBUG - Unidades que já preencheram {competencia}:")
            if unidades_preenchidas:
                for unidade in sorted(unidades_preenchidas):
                    print(f"   ✅ {unidade}")
            else:
                print("   ⚠️ Nenhuma unidade preencheu ainda")
            
            # Filtra apenas as pendentes
            pendentes = [
                {'nome': nome, 'email': email, 'unidade': unidade}
                for nome, email, unidade in todas_unidades
                if unidade not in unidades_preenchidas
            ]
            
            print(f"\n📊 Total de unidades: {len(todas_unidades)}")
            print(f"✅ Já preencheram: {len(unidades_preenchidas)}")
            print(f"⏳ Pendentes: {len(pendentes)}\n")
            
            return pendentes
            
        except Exception as e:
            print(f"❌ Erro ao obter unidades pendentes: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conn:
                conn.close()
    
    def enviar_email(self, destinatario_email, nome_destinatario, unidade, competencia, tipo_envio):
        """Envia email de notificação"""
        try:
            configs = {
                'disponivel': {
                    'assunto': f'📋 Preenchimento Disponível - Competência {competencia}',
                    'titulo': 'Preenchimento Disponível',
                    'mensagem': f'Informamos que o <strong>Relatório de Coleta</strong> referente à competência <strong>{competencia}</strong> já está disponível para preenchimento.',
                    'prazo': 'até o dia 10',
                    'cor': '#17a2b8',
                    'classe': 'info'
                },
                'urgente': {
                    'assunto': f'🚨 URGENTE: Último Dia - Competência {competencia}',
                    'titulo': 'Último Dia de Preenchimento',
                    'mensagem': f'<strong>ATENÇÃO:</strong> Hoje é o <strong>ÚLTIMO DIA</strong> para preenchimento do <strong>Relatório de Coleta</strong> referente à competência <strong>{competencia}</strong>.',
                    'prazo': 'HOJE (ÚLTIMO DIA)',
                    'cor': '#dc3545',
                    'classe': 'urgent'
                },
                'lembrete': {
                    'assunto': f'⚠️ Atraso: Preenchimento Pendente - Competência {competencia}',
                    'titulo': 'Preenchimento em Atraso',
                    'mensagem': f'O <strong>Relatório de Coleta</strong> referente à competência <strong>{competencia}</strong> está <strong>atrasado</strong>. Por favor, realize o preenchimento o quanto antes.',
                    'prazo': 'ATRASADO',
                    'cor': '#ffc107',
                    'classe': 'warning'
                }
            }
            
            config = configs.get(tipo_envio, configs['disponivel'])
            
            msg = EmailMessage()
            msg['From'] = self.EMAIL_REMETENTE
            msg['To'] = destinatario_email
            msg['Subject'] = config['assunto']
            
            corpo_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #162b47; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                    .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 5px 5px; }}
                    .{config['classe']} {{ background-color: {config['cor']}22; border-left: 4px solid {config['cor']}; padding: 15px; margin: 15px 0; }}
                    .btn {{ display: inline-block; background-color: #162b47; color: #fff !important; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; margin: 15px 0; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{config['titulo']}</h1>
                        <p style="margin: 0; font-size: 14px;">Relatório de Coleta - CEJAM</p>
                    </div>
                    
                    <div class="content">
                        <h2>Olá, {nome_destinatario}!</h2>
                        <p>{config['mensagem']}</p>
                        
                        <div class="{config['classe']}">
                            <h3 style="margin-top: 0;">🏥 {unidade}</h3>
                            <p style="margin: 5px 0;"><strong>Competência:</strong> {competencia}</p>
                            <p style="margin: 5px 0;"><strong>Prazo:</strong> <span style="color: {config['cor']}; font-weight: bold;">{config['prazo']}</span></p>
                        </div>
                        
                        {'<p style="font-size: 16px; color: #dc3545; font-weight: bold; text-align: center; margin: 20px 0;">⚠️ PREENCHIMENTO DEVE SER REALIZADO HOJE!</p>' if tipo_envio == 'urgente' else ''}
                        
                        <p>Acesse o sistema:</p>
                        
                        <center>
                            <a href="https://seu-sistema.streamlit.app" class="btn" style="color: #fff !important;">
                                🔗 Acessar Sistema
                            </a>
                        </center>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <h3>📌 Passo a passo:</h3>
                        <ol style="padding-left: 20px;">
                            <li>Acesse o sistema usando suas credenciais</li>
                            <li>Selecione a competência <strong>{competencia}</strong></li>
                            <li>Preencha todos os formulários obrigatórios</li>
                            <li>Revise as informações</li>
                            <li>Clique em <strong>"Enviar para KPIH"</strong></li>
                        </ol>
                        
                        <p style="margin-top: 20px;">Dúvidas: <strong>custos@cejam.org.br</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p style="margin: 5px 0;">© 2025 CEJAM</p>
                        <p style="margin: 5px 0;">Email automático - Não responda</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.set_content(corpo_html, subtype='html')
            
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as servidor:
                servidor.starttls()
                servidor.login(self.EMAIL_REMETENTE, self.SENHA_EMAIL)
                servidor.send_message(msg)
            
            print(f"✅ Email enviado para {destinatario_email} ({unidade}) - Tipo: {tipo_envio}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email para {destinatario_email}: {e}")
            return False
    
    def determinar_tipo_envio(self, hoje):
        """
        Determina qual tipo de email enviar baseado na data
        VERSÃO CORRIGIDA
        """
        dia_atual = hoje.day
        
        # Define os dias alvo (CORRIGIDO)
        dias_alvo = {
            1: 'disponivel',    # Dia 1: Aviso que está disponível
            10: 'urgente',      # Dia 10: Último dia para preencher
            20: 'lembrete'      # Dia 20: Cobrança dos atrasados
        }
        
        # MODO TESTE: força um tipo específico
        if self.modo_teste and self.tipo_teste:
            print(f"🧪 MODO TESTE: Forçando tipo '{self.tipo_teste}'")
            return self.tipo_teste
        
        # Verifica se hoje é dia útil
        if not self.is_dia_util(hoje):
            print(f"📅 {hoje.strftime('%d/%m/%Y')} não é dia útil")
            return None
        
        # Verifica se hoje é exatamente um dos dias alvo
        if dia_atual in dias_alvo:
            tipo = dias_alvo[dia_atual]
            print(f"📅 Dia {dia_atual} - Envio tipo '{tipo}'")
            return tipo
        
        # Verifica se hoje é o próximo dia útil após algum dia alvo
        for dia_alvo, tipo in dias_alvo.items():
            try:
                # Cria data do dia alvo no mês atual
                data_alvo = datetime(hoje.year, hoje.month, dia_alvo)
                
                # Encontra próximo dia útil após o dia alvo
                proximo_util = self.proximo_dia_util(data_alvo)
                
                # Se hoje é esse próximo dia útil E ainda estamos no mesmo mês
                if (proximo_util.day == dia_atual and 
                    proximo_util.month == hoje.month and
                    proximo_util > data_alvo):  # Garantir que é DEPOIS do dia alvo
                    
                    print(f"📅 Dia {dia_atual} - Próximo dia útil após dia {dia_alvo}")
                    return tipo
                    
            except ValueError:
                # Dia não existe no mês (ex: 31 de fevereiro)
                continue
        
        print(f"📅 Dia {dia_atual} - Não é dia de envio")
        return None
    
    def executar_envio_diario(self):
        """Função principal - executa diariamente"""
        hoje = datetime.now()
        
        print("\n" + "="*60)
        print(f"🔄 EXECUÇÃO: {hoje.strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        # Determina tipo de envio
        tipo_envio = self.determinar_tipo_envio(hoje)
        
        if not tipo_envio:
            print("⏭️ Nenhum envio necessário hoje")
            print("="*60 + "\n")
            return
        
        # Calcula competência
        competencia = self.calcular_competencia_anterior()
        print(f"📊 Competência: {competencia}")
        
        # Define destinatários
        if tipo_envio == 'disponivel':
            unidades = self.obter_todas_unidades()
            print(f"📧 Enviando para TODAS as {len(unidades)} unidades")
        else:
            unidades = self.obter_unidades_pendentes(competencia)
            if not unidades:
                print(f"✅ Todas as unidades já preencheram a competência {competencia}")
                print("="*60 + "\n")
                return
            print(f"⚠️ {len(unidades)} unidade(s) PENDENTE(S)")
        
        # Envia emails
        print(f"\n📨 Iniciando envio de emails ({tipo_envio})...\n")
        enviados = 0
        falhas = 0
        
        for i, unidade_info in enumerate(unidades, 1):
            print(f"[{i}/{len(unidades)}] Enviando para {unidade_info['email']}...", end=" ")
            
            sucesso = self.enviar_email(
                destinatario_email=unidade_info['email'],
                nome_destinatario=unidade_info['nome'],
                unidade=unidade_info['unidade'],
                competencia=competencia,
                tipo_envio=tipo_envio
            )
            
            if sucesso:
                enviados += 1
            else:
                falhas += 1
            
            time.sleep(1)  # Delay entre emails
        
        # Relatório final
        print("\n" + "="*60)
        print(f"📊 RELATÓRIO - {tipo_envio.upper()}")
        print(f"📅 {hoje.strftime('%d/%m/%Y %H:%M')}")
        print(f"✅ Enviados: {enviados}")
        print(f"❌ Falhas: {falhas}")
        print(f"📋 Total: {len(unidades)}")
        print("="*60 + "\n")
        
        # Registra log
        self.registrar_log(competencia, tipo_envio, enviados, falhas)
    
    def registrar_log(self, competencia, tipo_envio, enviados, falhas):
        """Registra log no banco"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_emails_relatorio (
                    id SERIAL PRIMARY KEY,
                    competencia VARCHAR(50),
                    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_envio VARCHAR(20),
                    total_enviados INTEGER,
                    total_falhas INTEGER
                )
            """)
            
            cursor.execute("""
                INSERT INTO logs_emails_relatorio 
                (competencia, tipo_envio, total_enviados, total_falhas)
                VALUES (%s, %s, %s, %s)
            """, (competencia, tipo_envio, enviados, falhas))
            
            conn.commit()
            print("✅ Log registrado no banco")
            
        except Exception as e:
            print(f"❌ Erro ao registrar log: {e}")
        finally:
            if conn:
                conn.close()


def iniciar_servico_automatico():
    """Inicia o serviço automático em PRODUÇÃO"""
    sistema = SistemaEmailsAutomatico(modo_teste=False)
    
    # Agenda execução diária às 08:00
    schedule.every().day.at("08:00").do(sistema.executar_envio_diario)
    
    print("="*60)
    print("✅ SERVIÇO DE EMAILS AUTOMÁTICO INICIADO")
    print("="*60)
    print("⏰ Horário: 08:00 (todos os dias)")
    print("📅 Dias de envio:")
    print("   - Dia 1 (ou próximo útil): Aviso de disponibilidade (TODAS)")
    print("   - Dia 10 (ou próximo útil): Último dia (PENDENTES)")
    print("   - Dia 20 (ou próximo útil): Cobrança de atrasados (PENDENTES)")
    print("="*60)
    print("\n⏳ Aguardando próximo envio...\n")
    
    # Loop infinito
    while True:
        schedule.run_pending()
        time.sleep(60)


def executar_teste_manual(tipo='lembrete'):
    """
    FUNÇÃO PARA TESTE MANUAL
    tipo: 'disponivel', 'lembrete' ou 'urgente'
    """
    print("\n" + "🧪"*30)
    print("MODO DE TESTE ATIVADO")
    print("🧪"*30 + "\n")
    
    sistema = SistemaEmailsAutomatico(modo_teste=True, tipo_teste=tipo)
    sistema.executar_envio_diario()


if __name__ == "__main__":
    # ============================================
    # ESCOLHA O MODO DE EXECUÇÃO:
    # ============================================
    
    # OPÇÃO 1: TESTE MANUAL (escolha o tipo)
    # executar_teste_manual(tipo='lembrete')  # Mude para 'lembrete' ou 'urgente'
    
    # OPÇÃO 2: PRODUÇÃO (comentar linha acima e descomentar abaixo)
    iniciar_servico_automatico()
