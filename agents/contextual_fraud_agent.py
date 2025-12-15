"""
Agente 3B: Detector de Fraudes Contextuais

Analisa emails em conjunto com transações para detectar fraudes
que só são visíveis com contexto de comunicação.
"""

import pandas as pd
from typing import List, Dict
import json
import time
import config
from utils.document_loader import load_transactions, load_emails, format_email_for_analysis
from utils.llm_adapter import LLMAdapter


class ContextualFraudDetector:
    """
    Detector que usa contexto de emails para identificar fraudes
    """
    
    def __init__(self):
        self.llm = LLMAdapter()
        
    def analyze_contextual_frauds(self) -> Dict:
        """
        Analisa fraudes que requerem contexto de emails
        
        Returns:
            Dict com fraudes contextuais detectadas
        """
        print("🔍 Iniciando análise contextual...")
        
        # Carregar dados
        print("📧 Carregando emails e transações...")
        emails = load_emails(str(config.EMAILS_PATH))
        df = load_transactions(str(config.TRANSACTIONS_PATH))
        print(f"✓ {len(emails)} emails e {len(df)} transações carregados")
        
        frauds = []
        
        print("\n🔍 Analisando fraudes contextuais...")
        start_time = time.time()
        
        # Estratégia 1: Fraude coordenada (múltiplas pessoas)
        coordinated = self._detect_coordinated_fraud(emails, df)
        frauds.extend(coordinated)
        print(f"  ✓ Fraude coordenada: {len(coordinated)} casos")
        
        # Estratégia 2: Justificativas falsas
        false_justifications = self._detect_false_justifications(emails, df)
        frauds.extend(false_justifications)
        print(f"  ✓ Justificativas falsas: {len(false_justifications)} casos")
        
        # Estratégia 3: Ocultação de informação
        hidden_info = self._detect_hidden_information(emails, df)
        frauds.extend(hidden_info)
        print(f"  ✓ Ocultação de informação: {len(hidden_info)} casos")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Tempo de análise: {elapsed:.2f}s")
        
        # Gerar relatório
        report = self._generate_report(frauds, len(emails), len(df))
        
        return {
            'total_emails': len(emails),
            'total_transactions': len(df),
            'contextual_frauds': frauds,
            'total_frauds': len(frauds),
            'report': report
        }
    
    def _detect_coordinated_fraud(self, emails: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Detecta fraudes que envolvem coordenação entre múltiplas pessoas"""
        frauds = []
        
        # Filtrar emails suspeitos (mencionam valores, compras, aprovação)
        suspicious_keywords = [
            'compra', 'purchase', 'aprovação', 'approval', 'autorização', 'authorization',
            '$', 'valor', 'amount', 'despesa', 'expense', 'reembolso', 'reimbursement',
            'dividir', 'split', 'juntos', 'together', 'combinar', 'combine'
        ]
        
        suspicious_emails = []
        for email in emails:
            mensagem_lower = email.get('mensagem', '').lower()
            if any(keyword in mensagem_lower for keyword in suspicious_keywords):
                suspicious_emails.append(email)
        
        # Limitar a 20 emails mais suspeitos para performance
        suspicious_emails = suspicious_emails[:20]
        
        print(f"    → Analisando {len(suspicious_emails)} emails suspeitos...")
        
        for i, email in enumerate(suspicious_emails, 1):
            if i % 5 == 0:
                print(f"      Processando {i}/{len(suspicious_emails)}...")
            
            # Analisar email com LLM
            try:
                analysis = self._analyze_email_for_fraud_coordination(email, df)
                
                if analysis and analysis.get('is_fraud', False):
                    frauds.append({
                        'email': email,
                        'analysis': analysis,
                        'violation_type': 'FRAUDE_COORDENADA',
                        'severity': analysis.get('severity', 5),
                        'evidence': analysis.get('evidence', ''),
                        'reason': analysis.get('reason', '')
                    })
            except Exception as e:
                print(f"      ⚠️  Erro ao analisar email: {str(e)}")
                continue
        
        return frauds
    
    def _detect_false_justifications(self, emails: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Detecta justificativas falsas ou enganosas para despesas"""
        frauds = []
        
        # Filtrar emails que justificam despesas
        justification_keywords = [
            'cliente', 'client', 'reunião', 'meeting', 'necessário', 'necessary',
            'emergência', 'emergency', 'urgente', 'urgent', 'projeto', 'project'
        ]
        
        justification_emails = []
        for email in emails:
            mensagem_lower = email.get('mensagem', '').lower()
            if any(keyword in mensagem_lower for keyword in justification_keywords):
                justification_emails.append(email)
        
        # Limitar para performance
        justification_emails = justification_emails[:20]
        
        print(f"    → Analisando {len(justification_emails)} emails com justificativas...")
        
        for i, email in enumerate(justification_emails, 1):
            if i % 5 == 0:
                print(f"      Processando {i}/{len(justification_emails)}...")
            
            try:
                analysis = self._analyze_justification(email, df)
                
                if analysis and analysis.get('is_false', False):
                    frauds.append({
                        'email': email,
                        'analysis': analysis,
                        'violation_type': 'JUSTIFICATIVA_FALSA',
                        'severity': analysis.get('severity', 6),
                        'evidence': analysis.get('evidence', ''),
                        'reason': analysis.get('reason', '')
                    })
            except Exception as e:
                print(f"      ⚠️  Erro ao analisar justificativa: {str(e)}")
                continue
        
        return frauds
    
    def _detect_hidden_information(self, emails: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Detecta tentativas de ocultar informações relevantes"""
        frauds = []
        
        # Filtrar emails com possível ocultação
        hiding_keywords = [
            'não mencione', "don't mention", 'segredo', 'secret', 'confidencial', 'confidential',
            'entre nós', 'between us', 'só você', 'just you', 'discreto', 'discreet'
        ]
        
        hiding_emails = []
        for email in emails:
            mensagem_lower = email.get('mensagem', '').lower()
            if any(keyword in mensagem_lower for keyword in hiding_keywords):
                hiding_emails.append(email)
        
        print(f"    → Analisando {len(hiding_emails)} emails com possível ocultação...")
        
        for i, email in enumerate(hiding_emails, 1):
            try:
                analysis = self._analyze_information_hiding(email, df)
                
                if analysis and analysis.get('is_hiding', False):
                    frauds.append({
                        'email': email,
                        'analysis': analysis,
                        'violation_type': 'OCULTACAO_INFORMACAO',
                        'severity': analysis.get('severity', 8),
                        'evidence': analysis.get('evidence', ''),
                        'reason': analysis.get('reason', '')
                    })
            except Exception as e:
                print(f"      ⚠️  Erro ao analisar ocultação: {str(e)}")
                continue
        
        return frauds
    
    def _analyze_email_for_fraud_coordination(self, email: Dict, df: pd.DataFrame) -> Dict:
        """Usa LLM para analisar se email indica fraude coordenada"""
        
        # CORREÇÃO: Usar get() com fallback para normalizar campos
        remetente = email.get('remetente', email.get('de', 'Desconhecido'))
        destinatario = email.get('destinatario', email.get('para', 'Desconhecido'))
        
        # Extrair nomes dos participantes
        participants = [remetente, destinatario]
        
        # Buscar transações dos participantes
        participant_names = []
        for p in participants:
            # Extrair nome (antes do @)
            if '@' in p:
                name = p.split('@')[0].replace('.', ' ').title()
                participant_names.append(name)
        
        # Filtrar transações
        if participant_names:
            mask = df['funcionario'].str.contains('|'.join(participant_names), case=False, na=False)
            relevant_transactions = df[mask].head(10)
        else:
            relevant_transactions = pd.DataFrame()
        
        # Preparar prompt
        system_prompt = """Você é um auditor especializado em detectar fraudes corporativas.
Analise o email e transações para identificar se há coordenação fraudulenta.

SINAIS DE FRAUDE COORDENADA:
- Múltiplas pessoas dividindo compras para evitar limites
- Combinação para criar justificativas falsas
- Acordo para não reportar certas informações
- Divisão de responsabilidade para dificultar auditoria

IMPORTANTE: Responda APENAS com JSON válido (sem markdown).

Formato da resposta:
{
  "is_fraud": true/false,
  "severity": 0-10,
  "reason": "explicação breve",
  "evidence": "evidência específica do email",
  "participants": ["nome1", "nome2"]
}"""

        email_formatted = format_email_for_analysis(email)
        
        transactions_text = ""
        if not relevant_transactions.empty:
            transactions_text = "\n\nTRANSAÇÕES RELACIONADAS:\n"
            for _, tx in relevant_transactions.iterrows():
                transactions_text += f"- {tx['funcionario']}: ${tx['valor']:.2f} - {tx['descricao']} ({tx['data']})\n"
        
        user_prompt = f"""EMAIL:
{email_formatted}
{transactions_text}

Analise se este email indica fraude coordenada."""

        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
                max_tokens=500
            )
            
            # Limpar resposta
            cleaned = response.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(cleaned)
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"      ⚠️  Erro ao parsear JSON: {e}")
            print(f"      Resposta: {response[:200]}...")
            return None
        except Exception as e:
            print(f"      ⚠️  Erro na análise: {e}")
            return None
    
    def _analyze_justification(self, email: Dict, df: pd.DataFrame) -> Dict:
        """Analisa se justificativa é falsa ou enganosa"""
        
        system_prompt = """Você é um auditor analisando justificativas de despesas.
Identifique se a justificativa é falsa, exagerada ou enganosa.

SINAIS DE JUSTIFICATIVA FALSA:
- Alegação de "cliente" sem especificar quem
- "Emergência" sem detalhes concretos
- Justificativas vagas ou genéricas
- Contradições com a descrição da compra

IMPORTANTE: Responda APENAS com JSON válido.

Formato:
{
  "is_false": true/false,
  "severity": 0-10,
  "reason": "por que é falsa",
  "evidence": "trecho específico do email"
}"""

        email_formatted = format_email_for_analysis(email)
        user_prompt = f"""EMAIL:
{email_formatted}

Analise se a justificativa é falsa ou enganosa."""

        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
                max_tokens=400
            )
            
            # Limpar e parsear
            cleaned = response.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            
            return json.loads(cleaned)
            
        except Exception as e:
            print(f"      ⚠️  Erro: {e}")
            return None
    
    def _analyze_information_hiding(self, email: Dict, df: pd.DataFrame) -> Dict:
        """Analisa se há tentativa de ocultar informações"""
        
        system_prompt = """Você é um auditor investigando ocultação de informações.
Identifique se o email tenta esconder informações relevantes.

SINAIS DE OCULTAÇÃO:
- Pedidos de sigilo inadequados
- "Não mencione isso para..."
- Combinação para omitir fatos
- Destruição ou não registro de informações

IMPORTANTE: Responda APENAS com JSON válido.

Formato:
{
  "is_hiding": true/false,
  "severity": 0-10,
  "reason": "o que está sendo ocultado",
  "evidence": "trecho do email"
}"""

        email_formatted = format_email_for_analysis(email)
        user_prompt = f"""EMAIL:
{email_formatted}

Analise se há tentativa de ocultar informações."""

        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
                max_tokens=400
            )
            
            # Limpar e parsear
            cleaned = response.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            
            return json.loads(cleaned)
            
        except Exception as e:
            print(f"      ⚠️  Erro: {e}")
            return None
    
    def _generate_report(self, frauds: List[Dict], total_emails: int, total_transactions: int) -> str:
        """Gera relatório consolidado"""
        
        if not frauds:
            return f"""
╔══════════════════════════════════════════════════════════════════════╗
║         RELATÓRIO DE AUDITORIA - FRAUDES CONTEXTUAIS                 ║
╚══════════════════════════════════════════════════════════════════════╝

STATUS: ✓ NENHUMA FRAUDE CONTEXTUAL DETECTADA

Análise: {total_emails} emails e {total_transactions} transações
Resultado: Nenhum padrão de fraude coordenada identificado

Recomendação: Nenhuma ação necessária.
"""
        
        # Organizar por tipo
        by_type = {}
        for fraud in frauds:
            vtype = fraud['violation_type']
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(fraud)
        
        high_severity = [f for f in frauds if f['severity'] >= 8]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║         RELATÓRIO DE AUDITORIA - FRAUDES CONTEXTUAIS                 ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️  FRAUDES CONTEXTUAIS DETECTADAS

ESTATÍSTICAS:
- Emails analisados: {total_emails}
- Transações analisadas: {total_transactions}
- Fraudes contextuais encontradas: {len(frauds)}
- Alta severidade (≥8): {len(high_severity)}

VIOLAÇÕES POR TIPO:
"""
        
        for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            report += f"  • {vtype}: {len(items)} caso(s)\n"
        
        report += "\n" + "─"*70 + "\n"
        report += "TOP 10 CASOS MAIS SEVEROS:\n"
        report += "─"*70 + "\n\n"
        
        # Ordenar por severidade
        sorted_frauds = sorted(frauds, key=lambda x: -x['severity'])
        
        for i, fraud in enumerate(sorted_frauds[:10], 1):
            email = fraud['email']
            analysis = fraud['analysis']
            
            # CORREÇÃO: Normalizar campos aqui também
            remetente = email.get('remetente', email.get('de', 'Desconhecido'))
            destinatario = email.get('destinatario', email.get('para', 'Desconhecido'))
            
            report += f"[{i}] {fraud['violation_type']} - Severidade: {fraud['severity']}/10\n"
            report += f"    De: {remetente}\n"
            report += f"    Para: {destinatario}\n"
            report += f"    Assunto: {email.get('assunto', 'N/A')}\n"
            report += f"    Razão: {fraud['reason']}\n"
            report += f"    Evidência: {fraud['evidence'][:100]}...\n"
            report += "\n"
        
        report += f"""
{'─'*70}
CONCLUSÃO:
⚠️  {len(frauds)} fraude(s) contextual(is) detectada(s)
⚠️  Ação recomendada: Investigação aprofundada e possível ação legal

Este tipo de fraude é particularmente grave pois envolve:
- Coordenação entre múltiplas pessoas
- Tentativa deliberada de enganar a empresa
- Violação de confiança e ética profissional

Relatório gerado pelo Sistema de Auditoria Dunder Mifflin
"""
        
        return report


def main():
    """Executa detector de fraudes contextuais"""
    print("=" * 80)
    print("AGENTE 3B: DETECTOR DE FRAUDES CONTEXTUAIS")
    print("=" * 80)
    
    config.print_config_info()
    
    detector = ContextualFraudDetector()
    
    start_time = time.time()
    results = detector.analyze_contextual_frauds()
    total_elapsed = time.time() - start_time
    
    print(f"\n⏱️  Tempo total: {total_elapsed:.2f}s\n")
    
    print(results['report'])
    
    # Salvar resultados
    if results['contextual_frauds']:
        print("\n💾 Salvando detalhes das fraudes contextuais...")
        
        fraud_details = []
        for fraud in results['contextual_frauds']:
            email = fraud['email']
            
            # CORREÇÃO: Normalizar campos aqui também
            remetente = email.get('remetente', email.get('de', 'Desconhecido'))
            destinatario = email.get('destinatario', email.get('para', 'Desconhecido'))
            
            fraud_details.append({
                'de': remetente,
                'para': destinatario,
                'assunto': email.get('assunto', 'N/A'),
                'data': email.get('data', 'N/A'),
                'violation_type': fraud['violation_type'],
                'severity': fraud['severity'],
                'reason': fraud['reason'],
                'evidence': fraud['evidence'][:200]
            })
        
        if fraud_details:
            import pandas as pd
            df_frauds = pd.DataFrame(fraud_details)
            output_path = 'fraudes_contextuais.csv'
            df_frauds.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo salvo: {output_path}")


if __name__ == "__main__":
    main()