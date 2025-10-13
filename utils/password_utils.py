import bcrypt
import secrets
import re

def gerar_salt():
    """Gera um salt aleatório para a senha"""
    return bcrypt.gensalt()

def criar_hash_senha(senha):
    """
    Cria hash da senha com salt integrado (bcrypt já inclui o salt)
    Retorna: (hash_senha, salt_para_compatibilidade)
    """
    try:
        # bcrypt já gera e inclui o salt automaticamente
        senha_bytes = senha.encode('utf-8')
        salt = bcrypt.gensalt()
        hash_senha = bcrypt.hashpw(senha_bytes, salt)
        
        # Retorna hash como string e salt para compatibilidade
        return hash_senha.decode('utf-8'), salt.decode('utf-8')
    except Exception as e:
        print(f"Erro ao criar hash da senha: {e}")
        raise

def verificar_senha(senha, hash_armazenado):
    """
    Verifica se a senha digitada confere com o hash armazenado
    bcrypt já extrai o salt do hash automaticamente
    """
    try:
        senha_bytes = senha.encode('utf-8')
        hash_bytes = hash_armazenado.encode('utf-8')
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False

def validar_forca_senha(senha):
    """
    Valida a força da senha - TODOS os critérios são OBRIGATÓRIOS
    Retorna: (eh_valida, pontuacao, mensagens)
    """
    pontuacao = 0
    mensagens = []
    
    # CRITÉRIOS OBRIGATÓRIOS (todos devem ser atendidos)
    criterios_obrigatorios = {
        'comprimento': len(senha) >= 8,
        'maiuscula': bool(re.search(r'[A-Z]', senha)),
        'minuscula': bool(re.search(r'[a-z]', senha)),
        'numero': bool(re.search(r'\d', senha)),
        'especial': bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', senha))
    }
    
    # Verifica cada critério obrigatório
    if criterios_obrigatorios['comprimento']:
        pontuacao += 2
    else:
        mensagens.append("Mínimo 8 caracteres")
    
    if criterios_obrigatorios['maiuscula']:
        pontuacao += 1
    else:
        mensagens.append("Pelo menos 1 letra maiúscula")
    
    if criterios_obrigatorios['minuscula']:
        pontuacao += 1
    else:
        mensagens.append("Pelo menos 1 letra minúscula")
    
    if criterios_obrigatorios['numero']:
        pontuacao += 1
    else:
        mensagens.append("Pelo menos 1 número")
    
    if criterios_obrigatorios['especial']:
        pontuacao += 1
    else:
        mensagens.append("Pelo menos 1 caractere especial (!@#$%^&* etc.)")
    
    # Verifica senhas muito comuns (desqualifica imediatamente)
    senhas_fracas = [
        '123456', 'password', '12345678', 'qwerty', 'abc123', 
        '111111', 'admin', 'senha123', 'senha', 'password123',
        '123456789', 'qwerty123', '1234', '12345'
    ]
    
    if senha.lower() in senhas_fracas:
        return False, 0, ["Senha muito comum! Use uma senha mais segura"]
    
    # Bonus para senhas longas (não obrigatório, apenas para pontuação)
    if len(senha) >= 12:
        pontuacao += 1
    
    # VALIDAÇÃO RÍGIDA: TODOS os critérios obrigatórios devem ser atendidos
    # A senha só é válida se TODOS os 5 critérios básicos forem atendidos
    todos_criterios_atendidos = all(criterios_obrigatorios.values())
    
    # Senha é válida APENAS se todos os critérios obrigatórios forem atendidos
    eh_valida = todos_criterios_atendidos and len(mensagens) == 0
    
    return eh_valida, pontuacao, mensagens

def gerar_senha_temporaria(tamanho=8):
    """Gera uma senha temporária aleatória"""
    # Inclui diferentes tipos de caracteres para garantir complexidade
    maiusculas = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    minusculas = "abcdefghijklmnopqrstuvwxyz"
    numeros = "0123456789"
    especiais = "!@#$%^&*"
    
    # Garante pelo menos um de cada tipo
    senha = [
        secrets.choice(maiusculas),
        secrets.choice(minusculas),
        secrets.choice(numeros),
        secrets.choice(especiais)
    ]
    
    # Preenche o resto aleatoriamente
    todos_caracteres = maiusculas + minusculas + numeros + especiais
    for _ in range(tamanho - 4):
        senha.append(secrets.choice(todos_caracteres))
    
    # Embaralha a ordem
    secrets.SystemRandom().shuffle(senha)
    
    return ''.join(senha)

def obter_nivel_seguranca(pontuacao):
    """
    Retorna o nível de segurança baseado na pontuação
    Pontuação máxima: 7 (5 critérios básicos + 2 extras + 1 bonus)
    """
    if pontuacao <= 1:
        return "Muito Fraca", "🔴"
    elif pontuacao <= 2:
        return "Fraca", "🟠"
    elif pontuacao <= 3:
        return "Razoável", "🟡"
    elif pontuacao <= 4:
        return "Boa", "🟢"
    elif pontuacao <= 5:
        return "Muito Boa", "🟢"
    else:
        return "Excelente", "🟢"

def verificar_criterios_senha(senha):
    """
    Função auxiliar que retorna detalhes dos critérios atendidos
    Útil para debugging e interfaces mais detalhadas
    """
    criterios = {
        'comprimento': len(senha) >= 8,
        'maiuscula': bool(re.search(r'[A-Z]', senha)),
        'minuscula': bool(re.search(r'[a-z]', senha)),
        'numero': bool(re.search(r'\d', senha)),
        'especial': bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', senha)),
        'comprimento_bonus': len(senha) >= 12,
        'nao_comum': senha.lower() not in [
            '123456', 'password', '12345678', 'qwerty', 'abc123', 
            '111111', 'admin', 'senha123', 'senha', 'password123'
        ]
    }
    
    return criterios