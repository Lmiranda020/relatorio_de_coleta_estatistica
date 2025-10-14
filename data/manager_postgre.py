import psycopg2
import psycopg2.extras
from datetime import datetime
import numpy as np 
import json
import streamlit as st

def sanitizar_dados_extras(dados_extras):
    """Converte tipos numpy/pandas para tipos Python nativos antes de serializar para JSON"""
    if not dados_extras:
        return None
    
    def converter_valor(valor):
        if isinstance(valor, (np.integer, np.int64)):
            return int(valor)
        elif isinstance(valor, (np.floating, np.float64)):
            return float(valor)
        elif isinstance(valor, np.bool_):
            return bool(valor)
        elif isinstance(valor, dict):
            return {k: converter_valor(v) for k, v in valor.items()}
        elif isinstance(valor, list):
            return [converter_valor(item) for item in valor]
        return valor
    
    return converter_valor(dados_extras)


class DatabaseManagerPostgres:
    #classe é uma funcionalidade do python que permite organizar dados e funcilidade em um único lugar
    # é como se fosse um estojo que vou guardando coisas
    # Cada função dentro da classe é chamada de método
    # classe é um molde, é como fosse um planta de uma casa, um projeção
    #Ela define como um objeto deve ser, que atributos ele terá e que funcionalidades (métodos) poderá executar.
    # Mas só criar a classe não cria nada concreto ainda. É só o projeto.

    def __init__(self):
        try:
            # Converte porta para int se vier como string
            porta = st.secrets["database"]["port"]
            if isinstance(porta, str):
                porta = int(porta)
        #Ele é a função que roda automaticamente quando você cria uma instância do objeto.
        # É dentro dele que você define os atributos da instância, que são os dados específicos daquele objeto concreto.
        #Ele é a primeira função que é executada sempre que você cria uma instância da classe
        #self serve para acessar as intancias
        #Ele é a referência para a própria instância que está sendo criada ou usada.
        # Graças a ele, outros métodos da classe podem acessar os atributos dessa instância
            self.DB_CONFIG = {
                "host": st.secrets["database"]["host"],
                "database": st.secrets["database"]["database"],
                "user": st.secrets["database"]["user"],
                "password": st.secrets["database"]["password"],
                "port": porta,
                "connect_timeout": 10,
                "sslmode": "require"  # IMPORTANTE para Supabase
            }
        except Exception as e:
            print(f"❌ Erro ao configurar banco: {e}")
            raise
        #o que transforma um valor passado como argumento em atributo da instância é você armazená-lo dentro de self
    

    #precisa do self porque o método vai usar self.DB_CONFIG
    def get_connection(self):
        try:
            return psycopg2.connect(**self.DB_CONFIG)
        #psycopg2.connect(...)
        # psycopg2 é uma biblioteca Python usada para conectar ao banco de dados PostgreSQL.
        # A função connect() recebe informações sobre como se conectar ao banco, como:
        # host (servidor do banco)
        # database (nome do banco)
        # user (usuário)
        # password (senha)
        # port (porta do servidor)
        # Esse ** é o unpacking de dicionário.
        # Ele “desempacota” o dicionário para passar cada chave como argumento nomeado na função.
        # psycopg2.connect() retorna é um objeto de conexão, que é como uma “linha invisível” entre o seu programa Python e o banco de dados. Por si só, ele não traz dados do banco nem retorna um valor útil como booleano ou tabela.
        # Ele só te dá essa porta aberta, que você vai usar depois 
        except Exception as e:
            print(f"Erro na conexão com o banco: {e}")
            raise

    # self em qualquer método da classe sempre representa a instância que vai ser criada a partir da classe, não importa em qual método você esteja.
    def criar_tabelas(self):
        """Cria as tabelas se não existirem"""
        conn = None
        try:
            conn = self.get_connection() #aqui eu executo 
            cursor = conn.cursor()

            # Como você já criou as tabelas no DBeaver, esta função só verifica se existem
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'tickets_ajuda'
                );
            """)
            
            tabela_existe = cursor.fetchone()[0]
            if not tabela_existe:
                print("Tabelas não encontradas. Execute os comandos SQL no DBeaver primeiro.")
                return False
            
            return True
            
        except Exception as e:
            print(f"Erro ao verificar tabelas: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def criar_ticket(self, nome, email, unidade=None, assunto=None, mensagem=None, arquivo=None):
        """Cria um novo ticket no banco de dados"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Processa o arquivo se existir
            arquivo_nome = None
            arquivo_dados = None
            arquivo_tipo = None
            
            if arquivo:
                arquivo_nome = getattr(arquivo, 'name', str(arquivo))
                if hasattr(arquivo, 'read'):
                    arquivo.seek(0)  # Volta ao início do arquivo
                    arquivo_dados = arquivo.read()
                arquivo_tipo = getattr(arquivo, 'type', 'application/octet-stream')

            # Insere o ticket
            cursor.execute("""
                INSERT INTO tickets_ajuda 
                (nome, email, unidade, assunto, mensagem, arquivo_nome, arquivo_dados, arquivo_tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (nome, email, unidade, assunto, mensagem, arquivo_nome, arquivo_dados, arquivo_tipo))
            
            ticket_id = cursor.fetchone()[0]

            # Adiciona entrada no histórico
            self.adicionar_historico(cursor, ticket_id, nome, 'usuario', f"Ticket criado: {assunto or 'Sem assunto'}")

            conn.commit()
            print(f"Ticket {ticket_id} criado com sucesso!")
            return ticket_id

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao criar ticket: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def adicionar_historico(self, cursor, ticket_id, autor, tipo, mensagem):
        """Adiciona entrada no histórico do ticket"""
        try:
            cursor.execute("""
                INSERT INTO ticket_historico (ticket_id, autor, tipo, mensagem)
                VALUES (%s, %s, %s, %s)
            """, (ticket_id, autor, tipo, mensagem))
        except Exception as e:
            print(f"Erro ao adicionar histórico: {e}")
            raise

    def listar_tickets(self, status=None, email_usuario=None): # aqui eu defino uma função para filtrar os tickets, passando o email e o status
        """Lista tickets com filtros opcionais"""
        conn = None # defino uma variavel com o valor none, conn = connection
        try:
            conn = self.get_connection() # tento acesso o banco de dados, chamando a função que faz isso
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            query = "SELECT * FROM tickets_ajuda WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)

            if email_usuario:
                query += " AND email = %s"
                params.append(email_usuario)

            query += " ORDER BY data_criacao DESC"

            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            return [dict(row) for row in resultados]

        except Exception as e:
            print(f"Erro ao listar tickets: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def obter_ticket(self, ticket_id):
        """Obtém um ticket específico pelo ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT * FROM tickets_ajuda WHERE id = %s", (ticket_id,))
            linha = cursor.fetchone()
            return dict(linha) if linha else None
        except Exception as e:
            print(f"Erro ao obter ticket: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def atualizar_status_ticket(self, ticket_id, novo_status, usuario):
        """Atualiza o status de um ticket"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tickets_ajuda
                SET status = %s, data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (novo_status, ticket_id))

            self.adicionar_historico(cursor, ticket_id, usuario, 'suporte', f"Status alterado para: {novo_status}")

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao atualizar status: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def adicionar_resposta(self, ticket_id, resposta, respondido_por):
        """Adiciona uma resposta a um ticket"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tickets_ajuda
                SET resposta = %s, respondido_por = %s, data_resposta = CURRENT_TIMESTAMP,
                    status = 'Respondido', data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (resposta, respondido_por, ticket_id))

            self.adicionar_historico(cursor, ticket_id, respondido_por, 'suporte', resposta)

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao adicionar resposta: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def obter_arquivo_ticket(self, ticket_id):
        """Obtém dados do arquivo de um ticket"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT arquivo_dados FROM tickets_ajuda WHERE id = %s", (ticket_id,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Exception as e:
            print(f"Erro ao obter arquivo: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def testar_conexao(self):
        """Testa a conexão com o banco"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            resultado = cursor.fetchone()
            conn.close()
            return resultado[0] == 1
        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
            return False
        
    # ADICIONAR ESTAS FUNÇÕES NA SUA CLASSE DatabaseManagerPostgres:

    def criar_usuario(self, nome, email, unidade, senha=None):
        """Cria um novo usuário no sistema"""
        from utils.password_utils import criar_hash_senha, gerar_senha_temporaria
        
        try:
            # Verifica se usuário já existe
            if self.verificar_usuario_existe(email):
                return False, "Usuário já existe no sistema"
            
            # Se não foi fornecida senha, gera uma temporária
            if senha is None:
                senha = gerar_senha_temporaria()
                primeira_vez = True
                senha_retorno = senha
            else:
                primeira_vez = False
                senha_retorno = None
            
            # Cria hash da senha
            hash_senha, salt = criar_hash_senha(senha)
            
            query = """
            INSERT INTO usuarios (nome, email, unidade, senha_hash, salt, primeira_vez, 
                                tentativas_login, conta_bloqueada, data_criacao)
            VALUES (%s, %s, %s, %s, %s, %s, 0, FALSE, NOW())
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (nome, email, unidade, hash_senha, salt, primeira_vez))
                    conn.commit()
            
            return True, senha_retorno
            
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            return False, f"Erro ao criar usuário: {str(e)}"

    def validar_senha_usuario(self, email, senha):
        """Valida senha do usuário no banco de dados"""
        from utils.password_utils import verificar_senha
        
        try:
            # LOG 1: Tentativa de conexão
            print(f"🔍 DEBUG: Tentando conectar ao banco para validar {email}")
            
            query = """
            SELECT nome, unidade, senha_hash, salt, tentativas_login, conta_bloqueada, primeira_vez
            FROM usuarios 
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                print(f"✅ DEBUG: Conexão estabelecida com sucesso")
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    resultado = cursor.fetchone()
                    
                    # LOG 2: Verifica se usuário foi encontrado
                    if not resultado:
                        print(f"❌ DEBUG: Usuário {email} não encontrado no banco")
                        return False, "Usuário não encontrado"
                    
                    print(f"✅ DEBUG: Usuário {email} encontrado no banco")
                    
                    nome, unidade, senha_hash, salt, tentativas, bloqueada, primeira_vez = resultado
                    
                    # LOG 3: Status da conta
                    print(f"🔍 DEBUG: Conta bloqueada? {bloqueada}")
                    print(f"🔍 DEBUG: Tentativas: {tentativas}")
                    print(f"🔍 DEBUG: Primeira vez? {primeira_vez}")
                    
                    # Verifica se conta está bloqueada
                    if bloqueada:
                        print(f"⚠️ DEBUG: Conta está bloqueada")
                        return False, "Conta bloqueada. Entre em contato com o suporte."
                    
                    # Verifica se excedeu tentativas
                    if tentativas >= 5:
                        print(f"⚠️ DEBUG: Excedeu tentativas, bloqueando conta")
                        self.bloquear_conta_usuario(email)
                        return False, "Muitas tentativas de login. Conta bloqueada."
                    
                    # LOG 4: Verificação de senha
                    print(f"🔍 DEBUG: Verificando senha...")
                    print(f"🔍 DEBUG: Hash no banco existe? {bool(senha_hash)}")
                    
                    if verificar_senha(senha, senha_hash):
                        print(f"✅ DEBUG: Senha CORRETA!")
                        # Login bem-sucedido
                        self.resetar_tentativas_login(email)
                        
                        if primeira_vez:
                            return True, f"PRIMEIRA_VEZ|{unidade}"
                        else:
                            return True, unidade
                    else:
                        print(f"❌ DEBUG: Senha INCORRETA")
                        # Senha incorreta - incrementa tentativas
                        self.incrementar_tentativas_login(email)
                        tentativas_restantes = 5 - (tentativas + 1)
                        return False, f"Senha incorreta. {tentativas_restantes} tentativas restantes."
            
        except Exception as e:
            # LOG 5: Erro na conexão ou consulta
            print(f"❌ DEBUG ERRO CRÍTICO: {e}")
            import traceback
            print(f"📋 DEBUG TRACEBACK:\n{traceback.format_exc()}")
            return False, f"Erro ao validar login: {str(e)}"

    def verificar_usuario_existe(self, email):
        """Verifica se email já está cadastrado"""
        try:
            query = "SELECT COUNT(*) FROM usuarios WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    count = cursor.fetchone()[0]
                    return count > 0
            
        except Exception as e:
            print(f"Erro ao verificar usuário: {e}")
            return False

    def incrementar_tentativas_login(self, email):
        """Incrementa contador de tentativas de login"""
        try:
            query = """
            UPDATE usuarios 
            SET tentativas_login = tentativas_login + 1 
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    conn.commit()
            
        except Exception as e:
            print(f"Erro ao incrementar tentativas: {e}")

    def resetar_tentativas_login(self, email):
        """Zera contador de tentativas após login bem-sucedido"""
        try:
            query = "UPDATE usuarios SET tentativas_login = 0 WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    conn.commit()
            
        except Exception as e:
            print(f"Erro ao resetar tentativas: {e}")

    def bloquear_conta_usuario(self, email):
        """Bloqueia conta do usuário após muitas tentativas"""
        try:
            query = "UPDATE usuarios SET conta_bloqueada = TRUE WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    conn.commit()
            
        except Exception as e:
            print(f"Erro ao bloquear conta: {e}")

    def atualizar_senha_usuario(self, email, nova_senha, pergunta_seguranca=None, resposta_seguranca=None):
        """Atualiza senha do usuário"""
        from utils.password_utils import criar_hash_senha
        
        try:
            # Cria hash da nova senha
            hash_senha, salt = criar_hash_senha(nova_senha)
            
            # Hash da resposta de segurança se fornecida
            resposta_hash = None
            if resposta_seguranca:
                resposta_hash, _ = criar_hash_senha(resposta_seguranca.lower().strip())
            
            query = """
            UPDATE usuarios 
            SET senha_hash = %s, salt = %s, primeira_vez = FALSE,
                pergunta_seguranca = %s, resposta_seguranca_hash = %s,
                tentativas_login = 0, conta_bloqueada = FALSE
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (hash_senha, salt, pergunta_seguranca, resposta_hash, email))
                    conn.commit()
                    return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao atualizar senha: {e}")
            return False

    def definir_senha_primeiro_acesso(self, email, nova_senha, pergunta_seguranca=None, resposta_seguranca=None):
        """Define senha no primeiro acesso"""
        return self.atualizar_senha_usuario(email, nova_senha, pergunta_seguranca, resposta_seguranca)

    def obter_pergunta_seguranca(self, email):
        """Obtém pergunta de segurança do usuário"""
        try:
            query = "SELECT pergunta_seguranca FROM usuarios WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    resultado = cursor.fetchone()
                    return resultado[0] if resultado and resultado[0] else None
            
        except Exception as e:
            print(f"Erro ao obter pergunta de segurança: {e}")
            return None

    def verificar_resposta_seguranca(self, email, resposta_informada):
        """Verifica se resposta de segurança está correta"""
        from utils.password_utils import verificar_senha
        
        try:
            query = "SELECT resposta_seguranca_hash FROM usuarios WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    resultado = cursor.fetchone()
                    
                    if not resultado or not resultado[0]:
                        return False
                    
                    resposta_hash = resultado[0]
                    # CORREÇÃO: Apenas 2 argumentos
                    return verificar_senha(resposta_informada.lower().strip(), resposta_hash)
            
        except Exception as e:
            print(f"Erro ao verificar resposta de segurança: {e}")
            return False

    def listar_usuarios(self):
        """Lista todos os usuários do sistema"""
        try:
            query = """
            SELECT id, nome, email, unidade, primeira_vez, tentativas_login, 
                conta_bloqueada, data_criacao
            FROM usuarios 
            ORDER BY nome
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()
            
        except Exception as e:
            print(f"Erro ao listar usuários: {e}")
            return []

    def resetar_senha_usuario(self, email, nova_senha_temporaria):
        """Reseta senha para uma temporária"""
        from utils.password_utils import criar_hash_senha
        
        try:
            hash_senha, salt = criar_hash_senha(nova_senha_temporaria)
            
            query = """
            UPDATE usuarios 
            SET senha_hash = %s, salt = %s, primeira_vez = TRUE,
                tentativas_login = 0, conta_bloqueada = FALSE
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (hash_senha, salt, email))
                    conn.commit()
                    return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao resetar senha: {e}")
            return False

    def desbloquear_conta_usuario(self, email):
        """Desbloqueia conta do usuário"""
        try:
            query = """
            UPDATE usuarios 
            SET conta_bloqueada = FALSE, tentativas_login = 0 
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    conn.commit()
                    return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao desbloquear conta: {e}")
            return False

    def marcar_primeiro_acesso(self, email):
        """Marca usuário para primeiro acesso"""
        try:
            query = "UPDATE usuarios SET primeira_vez = TRUE WHERE email = %s"
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    conn.commit()
                    return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao marcar primeiro acesso: {e}")
            return False

    def reset_completo_usuario(self, email, nova_senha_temporaria):
        """Reset completo: nova senha + desbloqueio + primeiro acesso"""
        from utils.password_utils import criar_hash_senha
        
        try:
            hash_senha, salt = criar_hash_senha(nova_senha_temporaria)
            
            query = """
            UPDATE usuarios 
            SET senha_hash = %s, salt = %s, primeira_vez = TRUE,
                tentativas_login = 0, conta_bloqueada = FALSE,
                pergunta_seguranca = NULL, resposta_seguranca_hash = NULL
            WHERE email = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (hash_senha, salt, email))
                    conn.commit()
                    return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao executar reset completo: {e}")
            return False
        
    def deletar_usuario(self, email_usuario):
        """
        Deleta um usuário do sistema permanentemente
        """
        try:
            # Proteção adicional - não permitir deletar o admin
            if email_usuario == 'custos@cejam.org.br':
                print(f"Tentativa bloqueada de deletar usuário admin: {email_usuario}")
                return False
                
            # Primeiro verifica se o usuário existe
            query_verificar = "SELECT email FROM usuarios WHERE email = %s"
            
            # Usando o padrão da sua classe com get_connection()
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Verifica se usuário existe
                    cursor.execute(query_verificar, (email_usuario,))
                    usuario_existe = cursor.fetchone()
                    
                    if not usuario_existe:
                        print(f"Usuário não encontrado: {email_usuario}")
                        return False
                        
                    # Deleta o usuário
                    query_deletar = "DELETE FROM usuarios WHERE email = %s"
                    cursor.execute(query_deletar, (email_usuario,))
                    
                    # Verifica se alguma linha foi afetada
                    linhas_afetadas = cursor.rowcount
                    
                    # Commit das alterações
                    conn.commit()
                    
                    print(f"Usuário {email_usuario} deletado. Linhas afetadas: {linhas_afetadas}")
                    return linhas_afetadas > 0
            
        except Exception as e:
            print(f"Erro ao deletar usuário {email_usuario}: {e}")
            return False
        

    #daqui até o final são as funções para rastrear os preenchimentos dos formulários, afins de estatística na tabela
    def criar_tabela_preenchimentos_finalizados(self):
        """Cria tabela para registrar preenchimentos finalizados"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preenchimentos_finalizados (
                    id SERIAL PRIMARY KEY,
                    email_usuario VARCHAR(255) NOT NULL,
                    nome_usuario VARCHAR(255) NOT NULL,
                    unidade VARCHAR(255) NOT NULL,
                    competencia VARCHAR(50) NOT NULL,
                    data_finalizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_formularios INTEGER DEFAULT 0,
                    ip_address VARCHAR(45),
                    navegador TEXT,
                    dados_extras JSONB,
                    status_envio VARCHAR(50) DEFAULT 'consolidado',
                    UNIQUE(email_usuario, competencia)
                )
            """)

            # Adiciona coluna status_envio se não existir (para tabelas antigas)
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='preenchimentos_finalizados' 
                        AND column_name='status_envio'
                    ) THEN
                        ALTER TABLE preenchimentos_finalizados 
                        ADD COLUMN status_envio VARCHAR(50) DEFAULT 'consolidado';
                    END IF;
                END $$;
        """)
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao criar tabela preenchimentos_finalizados: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def registrar_preenchimento_finalizado(self, email_usuario, nome_usuario, unidade, competencia, total_formularios, ip_address=None, dados_extras=None, status_envio='consolidado'):
        """Registra quando usuário finaliza preenchimento (clica em Enviar para KPIH)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Converte dados_extras para JSON se necessário
            if dados_extras and not isinstance(dados_extras, str):
                # SANITIZA tipos numpy/pandas ANTES de converter para JSON
                dados_extras = json.dumps(sanitizar_dados_extras(dados_extras))
            
            # Verifica se já existe registro para este usuário/competência
            cursor.execute("""
                SELECT id FROM preenchimentos_finalizados 
                WHERE email_usuario = %s AND competencia = %s
            """, (email_usuario, competencia))
            
            existe = cursor.fetchone()
            
            if existe:
                # Atualiza registro existente
                cursor.execute("""
                    UPDATE preenchimentos_finalizados 
                    SET nome_usuario = %s, 
                        unidade = %s, 
                        data_finalizacao = CURRENT_TIMESTAMP,
                        total_formularios = %s, 
                        ip_address = %s, 
                        dados_extras = %s, 
                        status_envio = %s
                    WHERE email_usuario = %s AND competencia = %s
                    RETURNING id
                """, (nome_usuario, unidade, total_formularios, ip_address, dados_extras, status_envio, email_usuario, competencia))
                
                resultado = cursor.fetchone()
                if resultado is None:
                    print(f"⚠️ AVISO: UPDATE não retornou ID")
                    registro_id = existe[0]  # Usa o ID que já tínhamos
                else:
                    registro_id = resultado[0]
                
                print(f"✅ Registro ATUALIZADO - ID: {registro_id}")
                
            else:
                # Insere novo registro
                cursor.execute("""
                    INSERT INTO preenchimentos_finalizados 
                    (email_usuario, nome_usuario, unidade, competencia, total_formularios, ip_address, dados_extras, status_envio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (email_usuario, nome_usuario, unidade, competencia, total_formularios, ip_address, dados_extras, status_envio))
                
                resultado = cursor.fetchone()
                if resultado is None:
                    print(f"❌ ERRO: INSERT não retornou ID")
                    conn.rollback()
                    return None
                
                registro_id = resultado[0]
                print(f"✅ Registro CRIADO - ID: {registro_id}")
            
            # Commit da transação
            conn.commit()
            print(f"✅ Transação confirmada (commit) - ID final: {registro_id}")
            
            return registro_id
            
        except Exception as e:
            print(f"❌ Erro ao registrar preenchimento: {e}")
            if conn:
                conn.rollback()
                print(f"🔄 Rollback executado")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            if conn:
                conn.close()
                print(f"🔌 Conexão fechada")

    def obter_estatisticas_dashboard(self):
        """Obtém estatísticas para dashboard do painel de suporte"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total de preenchimentos finalizados
            cursor.execute("SELECT COUNT(*) FROM preenchimentos_finalizados")
            total_preenchimentos = cursor.fetchone()[0]
            
            # Preenchimentos últimos 30 dias
            cursor.execute("""
                SELECT COUNT(*) FROM preenchimentos_finalizados 
                WHERE data_finalizacao >= CURRENT_DATE - INTERVAL '30 days'
            """)
            ultimos_30_dias = cursor.fetchone()[0]
            
            # Por competência
            cursor.execute("""
                SELECT competencia, COUNT(*) as total
                FROM preenchimentos_finalizados 
                GROUP BY competencia
                ORDER BY competencia DESC
            """)
            por_competencia = cursor.fetchall()
            
            # Por unidade (TOP 15)
            cursor.execute("""
                SELECT unidade, COUNT(*) as total
                FROM preenchimentos_finalizados
                GROUP BY unidade
                ORDER BY total DESC
                LIMIT 15
            """)
            por_unidade = cursor.fetchall()
            
            # Atividade últimos 7 dias
            cursor.execute("""
                SELECT DATE(data_finalizacao) as data, COUNT(*) as total
                FROM preenchimentos_finalizados 
                WHERE data_finalizacao >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(data_finalizacao)
                ORDER BY data DESC
            """)
            por_dia = cursor.fetchall()
            
            # Por mês (últimos 6 meses)
            cursor.execute("""
                SELECT 
                    TO_CHAR(data_finalizacao, 'YYYY-MM') as mes,
                    COUNT(*) as total
                FROM preenchimentos_finalizados 
                WHERE data_finalizacao >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY TO_CHAR(data_finalizacao, 'YYYY-MM')
                ORDER BY mes DESC
            """)
            por_mes = cursor.fetchall()
            
            # Unidades que mais preenchem
            cursor.execute("""
                SELECT unidade, COUNT(*) as total,
                    MAX(data_finalizacao) as ultimo_preenchimento
                FROM preenchimentos_finalizados
                GROUP BY unidade
                ORDER BY total DESC
            """)
            ranking_unidades = cursor.fetchall()

            # Status de envios
            cursor.execute("""
                SELECT status_envio, COUNT(*) as total
                FROM preenchimentos_finalizados
                GROUP BY status_envio
            """)
            por_status = cursor.fetchall()

            # Unidades com maior taxa de finalização
            cursor.execute("""
                SELECT unidade, 
                    COUNT(DISTINCT competencia) as competencias_preenchidas,
                    MAX(data_finalizacao) as ultimo_preenchimento
                FROM preenchimentos_finalizados
                GROUP BY unidade
                ORDER BY competencias_preenchidas DESC
            """)
            ranking_finalizacao = cursor.fetchall()
            
            return {
                'total_preenchimentos': total_preenchimentos,
                'ultimos_30_dias': ultimos_30_dias,
                'por_competencia': por_competencia,
                'por_unidade': por_unidade,
                'por_dia': por_dia,
                'por_mes': por_mes,
                'ranking_unidades': ranking_unidades,
                'por_status': por_status,
                'ranking_finalizacao': ranking_finalizacao
            }
            
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def obter_relatorio_preenchimentos(self, competencia=None, unidade=None, data_inicio=None, data_fim=None):
        """Relatório detalhado dos preenchimentos finalizados"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id,
                    email_usuario,
                    nome_usuario,
                    unidade,
                    competencia,
                    data_finalizacao,
                    total_formularios,
                    ip_address
                FROM preenchimentos_finalizados 
                WHERE 1=1
            """
            
            params = []
            
            if competencia:
                query += " AND competencia = %s"
                params.append(competencia)
                
            if unidade:
                query += " AND unidade = %s"
                params.append(unidade)
                
            if data_inicio:
                query += " AND DATE(data_finalizacao) >= %s"
                params.append(data_inicio)
                
            if data_fim:
                query += " AND DATE(data_finalizacao) <= %s"
                params.append(data_fim)
                
            query += " ORDER BY data_finalizacao DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"Erro ao obter relatório: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def obter_unidades_pendentes(self, competencia):
        """Lista unidades que ainda não preencheram para a competência"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Todas as unidades cadastradas
            cursor.execute("SELECT DISTINCT unidade FROM usuarios ORDER BY unidade")
            todas_unidades = [row[0] for row in cursor.fetchall()]
            
            # Unidades que já preencheram esta competência
            cursor.execute("""
                SELECT DISTINCT unidade 
                FROM preenchimentos_finalizados 
                WHERE competencia = %s
            """, (competencia,))
            unidades_preencheram = [row[0] for row in cursor.fetchall()]
            
            # Unidades pendentes
            unidades_pendentes = [u for u in todas_unidades if u not in unidades_preencheram]
            
            return {
                'todas': todas_unidades,
                'preencheram': unidades_preencheram,
                'pendentes': unidades_pendentes,
                'total_unidades': len(todas_unidades),
                'total_preencheram': len(unidades_preencheram),
                'total_pendentes': len(unidades_pendentes)
            }
            
        except Exception as e:
            print(f"Erro ao obter unidades pendentes: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def buscar_dados_usuario(self, email):
        """Busca dados do usuário pelo email"""
        try:
            query = "SELECT nome, unidade FROM usuarios WHERE email = %s"
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (email,))
                    resultado = cursor.fetchone()
                    if resultado:
                        return {'nome': resultado[0], 'unidade': resultado[1]}
                    return None
        except Exception as e:
            print(f"Erro ao buscar dados do usuário: {e}")
            return None

    def atualizar_status_envio_api(self, email_usuario, competencia, status):
        """Atualiza status quando enviado para API"""
        try:
            query = """
                UPDATE preenchimentos_finalizados 
                SET status_envio = %s, data_envio_api = CURRENT_TIMESTAMP
                WHERE email_usuario = %s AND competencia = %s
            """
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (status, email_usuario, competencia))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar status de envio: {e}")
            return False

    def criar_tabela_feedbacks(self):
        """
        Cria tabela para armazenar feedbacks dos usuários após envio para KPIH
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedbacks_usuarios (
                    id SERIAL PRIMARY KEY,
                    email_usuario VARCHAR(255) NOT NULL,
                    unidade VARCHAR(255) NOT NULL,
                    competencia VARCHAR(50) NOT NULL,
                    avaliacao INTEGER NOT NULL CHECK (avaliacao >= 1 AND avaliacao <= 5),
                    comentario TEXT,
                    preenchimento_id INTEGER,
                    data_feedback TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (preenchimento_id) REFERENCES preenchimentos_finalizados(id) ON DELETE SET NULL
                )
            """)
            
            # Índices para otimizar consultas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedbacks_email 
                ON feedbacks_usuarios(email_usuario)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedbacks_competencia 
                ON feedbacks_usuarios(competencia)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedbacks_avaliacao 
                ON feedbacks_usuarios(avaliacao)
            """)
            
            conn.commit()
            print("✅ Tabela feedbacks_usuarios criada/verificada com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela feedbacks_usuarios: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()


    def registrar_feedback(self, email_usuario, unidade, competencia, avaliacao, comentario, preenchimento_id=None):
        """
        Registra feedback do usuário no banco de dados
        
        Args:
            email_usuario: Email do usuário que enviou o feedback
            unidade: Unidade do usuário
            competencia: Competência do preenchimento
            avaliacao: Nota de 1 a 5 estrelas
            comentario: Comentário opcional do usuário
            preenchimento_id: ID do preenchimento relacionado (opcional)
        
        Returns:
            ID do feedback registrado ou None em caso de erro
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Valida avaliação
            if not isinstance(avaliacao, int) or avaliacao < 1 or avaliacao > 5:
                print(f"⚠️ Avaliação inválida: {avaliacao}. Deve ser entre 1 e 5")
                return None
            
            cursor.execute("""
                INSERT INTO feedbacks_usuarios 
                (email_usuario, unidade, competencia, avaliacao, comentario, preenchimento_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (email_usuario, unidade, competencia, avaliacao, comentario, preenchimento_id))
            
            feedback_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Feedback {feedback_id} registrado com sucesso")
            return feedback_id
            
        except Exception as e:
            print(f"❌ Erro ao registrar feedback: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()


    def obter_estatisticas_feedbacks(self):
        """
        Obtém estatísticas gerais dos feedbacks
        
        Returns:
            Dicionário com estatísticas ou None em caso de erro
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total de feedbacks
            cursor.execute("SELECT COUNT(*) FROM feedbacks_usuarios")
            total_feedbacks = cursor.fetchone()[0]
            
            # Média de avaliação
            cursor.execute("SELECT AVG(avaliacao) FROM feedbacks_usuarios")
            media_resultado = cursor.fetchone()[0]
            media_avaliacao = round(float(media_resultado), 2) if media_resultado else 0
            
            # Distribuição por estrelas
            cursor.execute("""
                SELECT avaliacao, COUNT(*) as quantidade
                FROM feedbacks_usuarios
                GROUP BY avaliacao
                ORDER BY avaliacao DESC
            """)
            distribuicao_estrelas = cursor.fetchall()
            
            # Feedbacks últimos 30 dias
            cursor.execute("""
                SELECT COUNT(*) FROM feedbacks_usuarios 
                WHERE data_feedback >= CURRENT_DATE - INTERVAL '30 days'
            """)
            ultimos_30_dias = cursor.fetchone()[0]
            
            # Feedbacks por competência
            cursor.execute("""
                SELECT competencia, COUNT(*) as total, AVG(avaliacao) as media
                FROM feedbacks_usuarios
                GROUP BY competencia
                ORDER BY competencia DESC
            """)
            por_competencia = cursor.fetchall()
            
            # Top unidades com melhores avaliações
            cursor.execute("""
                SELECT unidade, COUNT(*) as total_feedbacks, AVG(avaliacao) as media_avaliacao
                FROM feedbacks_usuarios
                GROUP BY unidade
                HAVING COUNT(*) >= 3
                ORDER BY media_avaliacao DESC, total_feedbacks DESC
                LIMIT 10
            """)
            top_unidades = cursor.fetchall()
            
            # Feedbacks mais recentes
            cursor.execute("""
                SELECT id, email_usuario, unidade, competencia, avaliacao, 
                    LEFT(comentario, 100) as comentario_preview, data_feedback
                FROM feedbacks_usuarios
                ORDER BY data_feedback DESC
                LIMIT 10
            """)
            feedbacks_recentes = cursor.fetchall()
            
            return {
                'total_feedbacks': total_feedbacks,
                'media_avaliacao': media_avaliacao,
                'distribuicao_estrelas': distribuicao_estrelas,
                'ultimos_30_dias': ultimos_30_dias,
                'por_competencia': por_competencia,
                'top_unidades': top_unidades,
                'feedbacks_recentes': feedbacks_recentes
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas de feedbacks: {e}")
            return None
        finally:
            if conn:
                conn.close()


    def listar_feedbacks_detalhados(self, filtro_avaliacao=None, filtro_competencia=None, 
                                    filtro_unidade=None, limite=50):
        """
        Lista feedbacks com filtros opcionais
        
        Args:
            filtro_avaliacao: Filtrar por avaliação específica (1-5)
            filtro_competencia: Filtrar por competência
            filtro_unidade: Filtrar por unidade
            limite: Quantidade máxima de registros
        
        Returns:
            Lista de feedbacks ou lista vazia em caso de erro
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    f.id,
                    f.email_usuario,
                    f.unidade,
                    f.competencia,
                    f.avaliacao,
                    f.comentario,
                    f.data_feedback,
                    f.preenchimento_id,
                    p.total_formularios
                FROM feedbacks_usuarios f
                LEFT JOIN preenchimentos_finalizados p ON f.preenchimento_id = p.id
                WHERE 1=1
            """
            
            params = []
            
            if filtro_avaliacao is not None:
                query += " AND f.avaliacao = %s"
                params.append(filtro_avaliacao)
            
            if filtro_competencia:
                query += " AND f.competencia = %s"
                params.append(filtro_competencia)
            
            if filtro_unidade:
                query += " AND f.unidade = %s"
                params.append(filtro_unidade)
            
            query += " ORDER BY f.data_feedback DESC LIMIT %s"
            params.append(limite)
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Erro ao listar feedbacks: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def obter_feedback_por_preenchimento(self, preenchimento_id):
        """
        Busca feedback relacionado a um preenchimento específico
        
        Args:
            preenchimento_id: ID do preenchimento
        
        Returns:
            Dados do feedback ou None se não encontrado
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email_usuario, unidade, competencia, avaliacao, 
                    comentario, data_feedback
                FROM feedbacks_usuarios
                WHERE preenchimento_id = %s
            """, (preenchimento_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    'id': resultado[0],
                    'email_usuario': resultado[1],
                    'unidade': resultado[2],
                    'competencia': resultado[3],
                    'avaliacao': resultado[4],
                    'comentario': resultado[5],
                    'data_feedback': resultado[6]
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar feedback por preenchimento: {e}")
            return None
        finally:
            if conn:
                conn.close()


    def verificar_feedback_ja_enviado(self, email_usuario, competencia):
        """
        Verifica se usuário já enviou feedback para determinada competência
        
        Args:
            email_usuario: Email do usuário
            competencia: Competência do preenchimento
        
        Returns:
            True se já existe feedback, False caso contrário
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM feedbacks_usuarios
                WHERE email_usuario = %s AND competencia = %s
            """, (email_usuario, competencia))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            print(f"❌ Erro ao verificar feedback: {e}")
            return False
        finally:
            if conn:
                conn.close()