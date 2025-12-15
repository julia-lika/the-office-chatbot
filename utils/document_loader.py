"""
Utilitários para carregar e processar documentos do sistema de auditoria
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict


def load_compliance_policy(filepath: str | Path) -> str:
    """
    Carrega a política de compliance
    
    Args:
        filepath: Caminho para o arquivo da política
        
    Returns:
        Conteúdo da política como string
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


def load_transactions(filepath: str | Path) -> pd.DataFrame:
    """
    Carrega transações bancárias do CSV
    
    Args:
        filepath: Caminho para o arquivo CSV
        
    Returns:
        DataFrame com as transações
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    
    # Carregar CSV
    df = pd.read_csv(filepath, encoding='utf-8')
    
    # Validar colunas necessárias
    required_columns = ['id_transacao', 'funcionario', 'data', 'valor', 'descricao']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Colunas faltando no CSV: {missing_columns}")
    
    # Converter tipos
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Remover linhas com valores inválidos
    df = df.dropna(subset=['valor', 'data'])
    
    return df


def load_emails(filepath: str | Path) -> List[Dict[str, str]]:
    """
    Carrega emails do arquivo de texto
    
    Args:
        filepath: Caminho para o arquivo de emails
        
    Returns:
        Lista de dicionários com emails parseados
        
    Formato retornado:
        [
            {
                'remetente': 'email',  # também acessível como 'de'
                'destinatario': 'email',  # também acessível como 'para'
                'assunto': 'texto',
                'data': 'data',
                'mensagem': 'corpo do email'
            }
        ]
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Separar emails (assumindo que são separados por linhas vazias ou delimitadores)
    emails = []
    current_email = {
        'remetente': '',
        'destinatario': '',
        'assunto': '',
        'data': '',
        'mensagem': ''
    }
    
    lines = content.split('\n')
    in_message = False
    message_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detectar novo email
        if line_stripped.startswith('---') or line_stripped.startswith('==='):
            # Salvar email anterior se existir
            if current_email['remetente'] or current_email['mensagem']:
                current_email['mensagem'] = '\n'.join(message_lines).strip()
                
                # Adicionar aliases para compatibilidade
                email_with_aliases = current_email.copy()
                email_with_aliases['de'] = current_email['remetente']
                email_with_aliases['para'] = current_email['destinatario']
                
                emails.append(email_with_aliases)
                
                # Resetar para próximo email
                current_email = {
                    'remetente': '',
                    'destinatario': '',
                    'assunto': '',
                    'data': '',
                    'mensagem': ''
                }
                message_lines = []
                in_message = False
            continue
        
        # Parse de campos
        if line_stripped.startswith('De:') or line_stripped.startswith('From:'):
            current_email['remetente'] = line_stripped.split(':', 1)[1].strip()
            in_message = False
            
        elif line_stripped.startswith('Para:') or line_stripped.startswith('To:'):
            current_email['destinatario'] = line_stripped.split(':', 1)[1].strip()
            in_message = False
            
        elif line_stripped.startswith('Assunto:') or line_stripped.startswith('Subject:'):
            current_email['assunto'] = line_stripped.split(':', 1)[1].strip()
            in_message = False
            
        elif line_stripped.startswith('Data:') or line_stripped.startswith('Date:'):
            current_email['data'] = line_stripped.split(':', 1)[1].strip()
            in_message = False
            
        elif line_stripped.startswith('Mensagem:') or line_stripped.startswith('Message:'):
            in_message = True
            # Pegar texto após "Mensagem:" se houver
            msg_text = line_stripped.split(':', 1)[1].strip()
            if msg_text:
                message_lines.append(msg_text)
                
        elif line_stripped == '':
            # Linha vazia pode indicar início da mensagem
            if current_email['remetente'] and not in_message:
                in_message = True
                
        else:
            # Adicionar linha à mensagem
            if in_message or (current_email['remetente'] and not current_email['mensagem']):
                message_lines.append(line)
                in_message = True
    
    # Adicionar último email
    if current_email['remetente'] or message_lines:
        current_email['mensagem'] = '\n'.join(message_lines).strip()
        
        # Adicionar aliases
        email_with_aliases = current_email.copy()
        email_with_aliases['de'] = current_email['remetente']
        email_with_aliases['para'] = current_email['destinatario']
        
        emails.append(email_with_aliases)
    
    # Filtrar emails vazios
    emails = [e for e in emails if e['mensagem'].strip()]
    
    return emails


def format_email_for_analysis(email: Dict[str, str]) -> str:
    """
    Formata um email para análise pelo LLM
    
    Args:
        email: Dicionário com campos do email
        
    Returns:
        String formatada do email
    """
    # Suporta tanto 'remetente'/'destinatario' quanto 'de'/'para'
    remetente = email.get('remetente', email.get('de', 'N/A'))
    destinatario = email.get('destinatario', email.get('para', 'N/A'))
    
    formatted = f"""
De: {remetente}
Para: {destinatario}
Assunto: {email.get('assunto', 'N/A')}
Data: {email.get('data', 'N/A')}

{email.get('mensagem', '')}
""".strip()
    
    return formatted


def split_text_for_rag(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Divide texto em chunks para RAG (Retrieval Augmented Generation)
    
    Args:
        text: Texto para dividir
        chunk_size: Tamanho aproximado de cada chunk em caracteres
        chunk_overlap: Sobreposição entre chunks
        
    Returns:
        Lista de chunks de texto
    """
    # Dividir por parágrafos primeiro
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        
        # Se o parágrafo sozinho é maior que chunk_size, dividir por sentenças
        if para_size > chunk_size:
            sentences = para.split('. ')
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Adicionar ponto final se não tiver
                if not sentence.endswith('.'):
                    sentence += '.'
                
                sentence_size = len(sentence)
                
                if current_size + sentence_size > chunk_size and current_chunk:
                    # Salvar chunk atual
                    chunks.append(' '.join(current_chunk))
                    
                    # Manter overlap
                    if chunk_overlap > 0 and current_chunk:
                        overlap_text = ' '.join(current_chunk[-2:]) if len(current_chunk) >= 2 else current_chunk[-1]
                        current_chunk = [overlap_text, sentence]
                        current_size = len(overlap_text) + sentence_size
                    else:
                        current_chunk = [sentence]
                        current_size = sentence_size
                else:
                    current_chunk.append(sentence)
                    current_size += sentence_size
        
        # Se adicionar este parágrafo excede o tamanho
        elif current_size + para_size > chunk_size and current_chunk:
            # Salvar chunk atual
            chunks.append('\n\n'.join(current_chunk))
            
            # Manter overlap
            if chunk_overlap > 0 and current_chunk:
                current_chunk = [current_chunk[-1], para]
                current_size = len(current_chunk[-2]) + para_size
            else:
                current_chunk = [para]
                current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Adicionar último chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def load_and_validate_data(compliance_path: str | Path, 
                          transactions_path: str | Path, 
                          emails_path: str | Path) -> Dict:
    """
    Carrega e valida todos os dados do sistema
    
    Args:
        compliance_path: Caminho da política
        transactions_path: Caminho das transações
        emails_path: Caminho dos emails
        
    Returns:
        Dicionário com todos os dados carregados
    """
    print("📂 Carregando dados do sistema...")
    
    # Carregar política
    print("  → Política de compliance...", end=" ")
    policy = load_compliance_policy(compliance_path)
    print(f"✓ ({len(policy)} caracteres)")
    
    # Carregar transações
    print("  → Transações bancárias...", end=" ")
    transactions = load_transactions(transactions_path)
    print(f"✓ ({len(transactions)} transações)")
    
    # Carregar emails
    print("  → Emails...", end=" ")
    emails = load_emails(emails_path)
    print(f"✓ ({len(emails)} emails)")
    
    return {
        'policy': policy,
        'transactions': transactions,
        'emails': emails
    }


def save_results(results: pd.DataFrame, output_path: str | Path, description: str = "resultados"):
    """
    Salva resultados em CSV
    
    Args:
        results: DataFrame com resultados
        output_path: Caminho para salvar
        description: Descrição dos dados para mensagem
    """
    output_path = Path(output_path)
    
    # Criar diretório se não existir
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Salvar CSV
    results.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✓ {description.capitalize()} salvos em: {output_path}")


# Aliases para compatibilidade
load_policy = load_compliance_policy