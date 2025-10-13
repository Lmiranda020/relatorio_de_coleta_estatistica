"""
Script para gerar o base64 dos DOIS arquivos de tokens das unidades.
Execute este script LOCALMENTE antes de fazer o deploy.
"""

import base64
import os

# Configurações
ARQUIVOS_TOKENS = {
    "importacao": {
        "caminho": "data/unidades_tokens_cejam.xlsx",
        "saida": "excel_tokens_importacao_encoded.txt",
        "descricao": "Tokens de IMPORTAÇÃO"
    },
    "exportacao": {
        "caminho": "data/unidades_tokens_cejam_exportacao.xlsx",
        "saida": "excel_tokens_exportacao_encoded.txt",
        "descricao": "Tokens de EXPORTAÇÃO"
    }
}

def gerar_base64_excel(caminho_arquivo, arquivo_saida, descricao):
    """
    Lê um arquivo Excel de tokens e gera uma string base64.
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Erro: Arquivo não encontrado: {caminho_arquivo}")
            print(f"💡 Certifique-se de estar na pasta raiz do projeto")
            return False
        
        print(f"\n📖 Processando: {descricao}")
        print(f"   Arquivo: {caminho_arquivo}")
        
        # Ler e codificar o arquivo
        with open(caminho_arquivo, "rb") as f:
            conteudo = f.read()
            encoded = base64.b64encode(conteudo).decode()
        
        # Salvar em arquivo de texto
        with open(arquivo_saida, "w") as f:
            f.write(encoded)
        
        # Estatísticas
        tamanho_original = len(conteudo)
        tamanho_encoded = len(encoded)
        
        print(f"✅ Codificado com sucesso!")
        print(f"   Tamanho original: {tamanho_original:,} bytes")
        print(f"   Tamanho base64: {tamanho_encoded:,} caracteres")
        print(f"   Salvo em: {arquivo_saida}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("🔐 Gerador de Base64 para Tokens de Unidades")
    print("=" * 60)
    
    sucesso_total = True
    arquivos_gerados = []
    
    # Processar cada arquivo
    for tipo, config in ARQUIVOS_TOKENS.items():
        sucesso = gerar_base64_excel(
            config["caminho"],
            config["saida"],
            config["descricao"]
        )
        
        if sucesso:
            arquivos_gerados.append(config["saida"])
        else:
            sucesso_total = False
    
    # Resumo final
    print("\n" + "=" * 60)
    if sucesso_total:
        print("✅ TODOS OS ARQUIVOS FORAM CODIFICADOS COM SUCESSO!")
        print("\n📋 Próximos passos:")
        print("   1. Abra os arquivos gerados:")
        for arquivo in arquivos_gerados:
            print(f"      - {arquivo}")
        print("\n   2. No Streamlit Cloud, vá em: Settings → Secrets")
        print("\n   3. Cole o conteúdo usando este formato:")
        print("\n```toml")
        print("# Tokens de IMPORTAÇÃO")
        print('excel_tokens_importacao_base64 = "COLE_CONTEUDO_DO_ARQUIVO_1"')
        print("\n# Tokens de EXPORTAÇÃO")
        print('excel_tokens_exportacao_base64 = "COLE_CONTEUDO_DO_ARQUIVO_2"')
        print("```")
        print("\n   4. Cada string será BEM LONGA, cole em UMA linha só!")
    else:
        print("❌ ALGUNS ARQUIVOS NÃO FORAM PROCESSADOS")
        print("💡 Verifique os erros acima e tente novamente")
    
    print("=" * 60)


if __name__ == "__main__":
    main()