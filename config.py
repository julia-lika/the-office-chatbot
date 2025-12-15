"""
Configuração central do sistema de auditoria
Suporta o provedor de LLM groq
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()

# ============================================================================
# CONFIGURAÇÕES DO LLM PROVIDER
# ============================================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq") 

# Chaves de API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Modelos disponíveis por provider (ATUALIZADO - Dezembro 2024)
MODELS = {
    "groq": {
        "default": "llama-3.3-70b-versatile",
        "alternatives": [
            "llama-3.3-70b-versatile",      # Melhor qualidade (recomendado) ⭐
            "llama-3.1-70b-specdec",        # Rápido com speculative decoding
            "llama-3.3-70b-specdec",        # Versão 3.3 otimizada
            "llama-3.1-8b-instant",         # Mais rápido, menor
            "mixtral-8x7b-32768",           # Bom raciocínio, janela grande
            "gemma2-9b-it",                 # Leve e econômico
            "llama-3.2-1b-preview",         # Ultra rápido
            "llama-3.2-3b-preview"          # Rápido e compacto
        ]
    }
}

# Selecionar modelo baseado no provider
if LLM_PROVIDER == "groq":
    MODEL_NAME = os.getenv("MODEL_NAME", MODELS["groq"]["default"])
else:
    raise ValueError(f"Provider não suportado: {LLM_PROVIDER}. Use 'groq'")

# Configurações do modelo
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# ============================================================================
# CAMINHOS DOS ARQUIVOS
# ============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COMPLIANCE_POLICY_PATH = DATA_DIR / "politica_compliance.txt"
TRANSACTIONS_PATH = DATA_DIR / "transacoes_bancarias.csv"
EMAILS_PATH = DATA_DIR / "emails.txt"

# ============================================================================
# CONFIGURAÇÕES DO CHROMADB
# ============================================================================

CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "compliance_policy"

# ============================================================================
# VALIDAÇÕES
# ============================================================================

if LLM_PROVIDER == "groq":
    if not GROQ_API_KEY:
        raise ValueError(
            "\n❌ GROQ_API_KEY não encontrada!\n\n"
            "Configure no arquivo .env:\n"
            "  LLM_PROVIDER=groq\n"
            "  GROQ_API_KEY=gsk_sua_chave_aqui\n\n"
            "Obtenha sua chave GRATUITA em: https://console.groq.com/keys\n"
        )
    print("✓ Groq API Key configurada")

# ============================================================================
# INFORMAÇÕES DE CONFIGURAÇÃO
# ============================================================================

def print_config_info():
    """Imprime informações de configuração na inicialização"""
    print()
    print("╔" + "═"*70 + "╗")
    print("║" + " "*25 + "CONFIGURAÇÃO DO SISTEMA" + " "*22 + "║")
    print("╠" + "═"*70 + "╣")
    print(f"║  🤖 LLM Provider: {LLM_PROVIDER.upper():<50}  ║")
    print(f"║  📦 Modelo: {MODEL_NAME:<56}  ║")
    print(f"║  🌡️  Temperatura: {TEMPERATURE:<51}  ║")
    print(f"║  📊 Max Tokens: {MAX_TOKENS:<53}  ║")
    print("╚" + "═"*70 + "╝")
    print()


def get_model_info():
    """Retorna informações sobre o modelo atual"""
    return {
        "provider": LLM_PROVIDER,
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "available_models": MODELS.get(LLM_PROVIDER, {}).get("alternatives", [])
    }


# ============================================================================
# VERIFICAÇÕES DE ARQUIVOS
# ============================================================================

def check_data_files():
    """Verifica se todos os arquivos de dados existem"""
    missing_files = []
    
    if not COMPLIANCE_POLICY_PATH.exists():
        missing_files.append(str(COMPLIANCE_POLICY_PATH))
    
    if not TRANSACTIONS_PATH.exists():
        missing_files.append(str(TRANSACTIONS_PATH))
    
    if not EMAILS_PATH.exists():
        missing_files.append(str(EMAILS_PATH))
    
    if missing_files:
        raise FileNotFoundError(
            f"\n❌ Arquivos de dados não encontrados:\n" +
            "\n".join(f"  - {f}" for f in missing_files) +
            "\n\nCertifique-se de copiar os arquivos para a pasta 'data/'"
        )
    
    return True


# ============================================================================
# EXPORTAÇÕES ÚTEIS
# ============================================================================

__all__ = [
    'LLM_PROVIDER',
    'GROQ_API_KEY',
    'MODEL_NAME',
    'TEMPERATURE',
    'MAX_TOKENS',
    'COMPLIANCE_POLICY_PATH',
    'TRANSACTIONS_PATH',
    'EMAILS_PATH',
    'CHROMA_PERSIST_DIR',
    'COLLECTION_NAME',
    'print_config_info',
    'get_model_info',
    'check_data_files',
    'MODELS'
]