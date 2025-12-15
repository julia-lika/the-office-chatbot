"""
Agente 2: Detector de Conspiração contra Toby

Este agente analisa emails para detectar se Michael Scott está conspirando contra Toby.

Arquitetura:
- Análise de sentimento e intenção
- Detecção de padrões de comportamento hostil
- Identificação de conversas sobre Toby
- LLM: Groq (Llama 3.1 70B ou modelo configurado) com prompt especializado
"""

from typing import List, Dict, Tuple
import config
from utils.document_loader import load_emails, format_email_for_analysis
from utils.llm_adapter import LLMAdapter
import json
import time


class ConspiracyDetectionAgent:
    """
    Agente especializado em detectar conspiração contra Toby Flenderson
    Compatível com múltiplos provedores de LLM via LLMAdapter
    """
    
    def __init__(self):
        # Usar adaptador universal de LLM
        self.llm = LLMAdapter()
    
    def analyze_emails(self) -> Dict:
        """
        Analisa todos os emails em busca de evidências de conspiração
        
        Returns:
            Dict com resumo da análise e emails suspeitos
        """
        print("🔍 Carregando emails...")
        emails = load_emails(str(config.EMAILS_PATH))
        print(f"✓ {len(emails)} emails carregados")
        
        # Filtrar emails relevantes (de/para Michael ou mencionando Toby)
        relevant_emails = self._filter_relevant_emails(emails)
        print(f"✓ {len(relevant_emails)} emails relevantes identificados")
        
        # Analisar cada email suspeito
        print(f"\n🔍 Analisando {len(relevant_emails)} emails relevantes...")
        suspicious_emails = []
        
        for i, email in enumerate(relevant_emails, 1):
            # Mostrar progresso
            if i % 10 == 0 or i == len(relevant_emails):
                print(f"  Progresso: {i}/{len(relevant_emails)} emails analisados...")
            
            analysis = self._analyze_single_email(email)
            if analysis['is_suspicious']:
                suspicious_emails.append({
                    'email': email,
                    'analysis': analysis
                })
        
        print(f"✓ Análise completa: {len(suspicious_emails)} emails suspeitos detectados")
        
        # Gerar relatório final
        report = self._generate_final_report(suspicious_emails, len(emails))
        
        return {
            'total_emails': len(emails),
            'relevant_emails': len(relevant_emails),
            'suspicious_emails': suspicious_emails,
            'report': report
        }
    
    def _filter_relevant_emails(self, emails: List[Dict]) -> List[Dict]:
        """Filtra emails relevantes para análise de conspiração"""
        relevant = []
        
        for email in emails:
            # Email de ou para Michael Scott
            if 'michael.scott@dundermifflin.com' in email['de'].lower() or \
               'michael.scott@dundermifflin.com' in email['para'].lower():
                relevant.append(email)
                continue
            
            # Email menciona Toby
            text_to_check = (email['assunto'] + ' ' + email['mensagem']).lower()
            if 'toby' in text_to_check or 'flenderson' in text_to_check:
                relevant.append(email)
        
        return relevant
    
    def _analyze_single_email(self, email: Dict) -> Dict:
        """
        Analisa um único email para detectar conspiração
        
        Returns:
            Dict com is_suspicious, severity (0-10), reasoning
        """
        email_text = format_email_for_analysis(email)
        
        # Prompt otimizado para Groq/Llama - mais direto e estruturado
        system_prompt = """Você é um investigador de comportamento corporativo especializado em detectar conspiração e hostilidade.

MISSÃO: Detectar se Michael Scott está conspirando contra Toby Flenderson (representante de RH).

PADRÕES DE CONSPIRAÇÃO:
1. Comentários depreciativos sobre Toby
2. Minar a autoridade de Toby
3. Piadas ou sarcasmo dirigido a Toby
4. Ignorar procedimentos de RH de Toby
5. Coordenação com outros contra Toby
6. Fazer Toby parecer incompetente
7. Hostilidade velada ou explícita

ESCALA DE SEVERIDADE:
- 0-3: Normal (sem conspiração)
- 4-6: Leve (piadas, ignorar menor)
- 7-8: Moderado (desrespeito claro)
- 9-10: Alto (conspiração ativa, hostilidade explícita)

FORMATO DE RESPOSTA (JSON estrito):
{
    "is_suspicious": true,
    "severity": 8,
    "reasoning": "explicação concisa e direta",
    "evidence_quotes": ["citação 1", "citação 2"]
}

IMPORTANTE: Responda APENAS com JSON válido, sem texto adicional."""

        user_prompt = f"""Analise este email e retorne JSON:

{email_text}

JSON:"""

        # Usar adaptador LLM com retry para parsing JSON
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response_text = self.llm.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,
                    max_tokens=1024
                )
                
                # Limpar resposta (remover markdown se houver)
                cleaned_response = response_text.strip()
                if cleaned_response.startswith('```'):
                    # Remover ```json e ```
                    lines = cleaned_response.split('\n')
                    cleaned_response = '\n'.join(lines[1:-1])
                
                # Parsear JSON
                analysis = json.loads(cleaned_response)
                
                # Validar estrutura
                required_keys = ['is_suspicious', 'severity', 'reasoning']
                if all(key in analysis for key in required_keys):
                    return analysis
                
            except json.JSONDecodeError as e:
                if attempt == max_retries - 1:
                    # Último retry falhou, usar fallback
                    print(f"  ⚠️  Erro ao parsear JSON no email: {email.get('assunto', 'sem assunto')[:50]}")
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"  ⚠️  Erro na análise: {str(e)[:50]}")
                    break
        
        # Fallback se não conseguir parsear
        return {
            'is_suspicious': False,
            'severity': 0,
            'reasoning': 'Erro ao processar análise - resposta inválida do LLM',
            'evidence_quotes': []
        }
    
    def _generate_final_report(self, suspicious_emails: List[Dict], total_emails: int) -> str:
        """Gera relatório final consolidado"""
        
        if not suspicious_emails:
            return """
╔══════════════════════════════════════════════════════════════════════╗
║              RELATÓRIO DE INVESTIGAÇÃO - CONSPIRAÇÃO                 ║
╚══════════════════════════════════════════════════════════════════════╝

STATUS: ✓ NENHUMA CONSPIRAÇÃO DETECTADA

Após análise detalhada de todos os emails corporativos, não foram
encontradas evidências de conspiração contra Toby Flenderson.

Recomendação: Nenhuma ação necessária.
"""
        
        # Organizar por severidade
        high_severity = [e for e in suspicious_emails if e['analysis']['severity'] >= 7]
        medium_severity = [e for e in suspicious_emails if 4 <= e['analysis']['severity'] < 7]
        low_severity = [e for e in suspicious_emails if e['analysis']['severity'] < 4]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║              RELATÓRIO DE INVESTIGAÇÃO - CONSPIRAÇÃO                 ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️  CONSPIRAÇÃO DETECTADA

ESTATÍSTICAS:
- Total de emails analisados: {total_emails}
- Emails suspeitos encontrados: {len(suspicious_emails)}
- Alta severidade (7-10): {len(high_severity)}
- Média severidade (4-6): {len(medium_severity)}
- Baixa severidade (1-3): {len(low_severity)}

"""
        
        if high_severity:
            report += "\n🚨 EVIDÊNCIAS DE ALTA SEVERIDADE:\n"
            report += "─" * 70 + "\n"
            for item in high_severity[:5]:  # Top 5
                email = item['email']
                analysis = item['analysis']
                report += f"\nDe: {email['de']}\n"
                report += f"Para: {email['para']}\n"
                report += f"Data: {email['data']}\n"
                report += f"Assunto: {email['assunto']}\n"
                report += f"Severidade: {analysis['severity']}/10\n"
                report += f"Análise: {analysis['reasoning']}\n"
                if analysis.get('evidence_quotes'):
                    report += f"Evidências: {', '.join(analysis['evidence_quotes'][:2])}\n"
                report += "─" * 70 + "\n"
        
        report += f"""
CONCLUSÃO:
{'⚠️  AÇÃO RECOMENDADA: ' if high_severity else ''}
{'Evidências sugerem comportamento conspiratório de Michael Scott.' if high_severity else 'Comportamento suspeito detectado.'}
{'Recomenda-se intervenção de RH corporativo.' if high_severity else ''}

Relatório gerado pelo Sistema de Auditoria Dunder Mifflin
"""
        
        return report


def main():
    """Executa análise de conspiração"""
    print("=" * 80)
    print("AGENTE 2: DETECTOR DE CONSPIRAÇÃO CONTRA TOBY")
    print("=" * 80)
    print()
    
    # Mostrar configuração do LLM
    config.print_config_info()
    
    agent = ConspiracyDetectionAgent()
    
    print("🔍 Iniciando análise de emails...\n")
    
    start_time = time.time()
    results = agent.analyze_emails()
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Tempo total de análise: {elapsed:.2f}s")
    print(f"⚡ Tempo médio por email: {elapsed/results['relevant_emails']:.2f}s\n")
    
    print(results['report'])
    
    # Detalhes adicionais
    if results['suspicious_emails']:
        print("\n" + "="*80)
        print("EMAILS SUSPEITOS DETALHADOS:")
        print("="*80)
        
        for i, item in enumerate(results['suspicious_emails'][:10], 1):
            email = item['email']
            analysis = item['analysis']
            print(f"\n[{i}] De: {email['de']}")
            print(f"    Para: {email['para']}")
            print(f"    Assunto: {email['assunto']}")
            print(f"    Severidade: {analysis['severity']}/10")
            print(f"    Razão: {analysis['reasoning']}")


if __name__ == "__main__":
    main()