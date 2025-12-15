"""
Agente 3A: Detector de Fraudes Standalone

Este agente analisa transações bancárias para detectar violações diretas
de compliance sem necessidade de contexto de emails.

Arquitetura:
- Análise de regras baseada em lógica
- Validação contra política de compliance
- LLM: Groq (Llama 3.1 70B ou modelo configurado) para interpretação de regras complexas
"""

import pandas as pd
from typing import List, Dict, Tuple
import config
from utils.document_loader import load_transactions, load_compliance_policy
from utils.llm_adapter import LLMAdapter
import time


class StandaloneFraudDetector:
    """
    Detector de fraudes que não requerem contexto de emails
    Compatível com múltiplos provedores de LLM via LLMAdapter
    """
    
    def __init__(self):
        # Usar adaptador universal de LLM
        self.llm = LLMAdapter()
        self.compliance_policy = load_compliance_policy(str(config.COMPLIANCE_POLICY_PATH))
        
    def analyze_transactions(self) -> Dict:
        """
        Analisa todas as transações em busca de violações standalone
        
        Returns:
            Dict com transações fraudulentas e relatório
        """
        print("💰 Carregando transações...")
        df = load_transactions(str(config.TRANSACTIONS_PATH))
        print(f"✓ {len(df)} transações carregadas")
        
        fraudulent_transactions = []
        
        # Aplicar múltiplas checagens
        print("\n🔍 Aplicando verificações de compliance...")
        
        start_time = time.time()
        
        # Regra 1: Itens proibidos (Seção 3)
        prohibited_items = self._check_prohibited_items(df)
        fraudulent_transactions.extend(prohibited_items)
        print(f"  ✓ Itens proibidos: {len(prohibited_items)} violações")
        
        # Regra 2: Valores acima de alçada sem aprovação
        unauthorized_amounts = self._check_unauthorized_amounts(df)
        fraudulent_transactions.extend(unauthorized_amounts)
        print(f"  ✓ Valores não autorizados: {len(unauthorized_amounts)} violações")
        
        # Regra 3: Smurfing (estruturação de pagamentos)
        smurfing_cases = self._check_smurfing(df)
        fraudulent_transactions.extend(smurfing_cases)
        print(f"  ✓ Smurfing detectado: {len(smurfing_cases)} violações")
        
        # Regra 4: Locais restritos
        restricted_locations = self._check_restricted_locations(df)
        fraudulent_transactions.extend(restricted_locations)
        print(f"  ✓ Locais restritos: {len(restricted_locations)} violações")
        
        # Regra 5: Categorias suspeitas
        suspicious_categories = self._check_suspicious_categories(df)
        fraudulent_transactions.extend(suspicious_categories)
        print(f"  ✓ Categorias suspeitas: {len(suspicious_categories)} violações")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Tempo de análise: {elapsed:.2f}s")
        
        # Remover duplicatas (uma transação pode violar múltiplas regras)
        unique_frauds = self._deduplicate_frauds(fraudulent_transactions)
        
        # Gerar relatório
        report = self._generate_report(unique_frauds, len(df))
        
        return {
            'total_transactions': len(df),
            'fraudulent_transactions': unique_frauds,
            'total_frauds': len(unique_frauds),
            'report': report
        }
    
    def _check_prohibited_items(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta compra de itens proibidos pela Seção 3"""
        prohibited_keywords = [
            'mágica', 'magic', 'karaokê', 'karaoke', 'algema', 'handcuff',
            'corrente', 'chain', 'fumaça', 'smoke', 'pombo', 'pigeon',
            'stripper', 'baralho marcado', 'discoteca', 'disco',
            'arma', 'weapon', 'gun', 'airsoft', 'espada', 'sword', 'katana',
            'ninja', 'nunchaku', 'spray de pimenta', 'pepper spray',
            'camuflagem', 'camouflage', 'armadilha', 'trap',
            'vela artesanal', 'candle', 'startup', 'rede social', 'social network',
            'beterraba', 'beet', 'binóculo', 'binocular', 'vigilância', 'surveillance',
            'walkie talkie', 'walkie-talkie'
        ]
        
        violations = []
        
        for idx, row in df.iterrows():
            description_lower = row['descricao'].lower()
            
            for keyword in prohibited_keywords:
                if keyword in description_lower:
                    violations.append({
                        'transaction': row.to_dict(),
                        'violation_type': 'ITEM_PROIBIDO',
                        'severity': 9,
                        'rule': 'Seção 3 - Lista Negra de Itens',
                        'reason': f'Compra de item proibido detectada: "{keyword}"',
                        'evidence': f'Descrição: {row["descricao"]}'
                    })
                    break
        
        return violations
    
    def _check_unauthorized_amounts(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta valores acima de alçada (Seção 1)"""
        violations = []
        
        # Valores acima de $500 requerem Purchase Order
        high_value_threshold = 500.00
        
        for idx, row in df.iterrows():
            if row['valor'] > high_value_threshold:
                # Verificar se há indicação de PO na descrição
                description_lower = row['descricao'].lower()
                if 'po' not in description_lower and 'purchase order' not in description_lower and 'p.o.' not in description_lower:
                    violations.append({
                        'transaction': row.to_dict(),
                        'violation_type': 'VALOR_NAO_AUTORIZADO',
                        'severity': 7,
                        'rule': 'Seção 1.3 - Grandes Despesas',
                        'reason': f'Valor acima de ${high_value_threshold} sem evidência de Purchase Order',
                        'evidence': f'Valor: ${row["valor"]:.2f}'
                    })
        
        return violations
    
    def _check_smurfing(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta smurfing (estruturação) - Seção 1.3"""
        violations = []
        detected_pairs = set()  # Evitar duplicatas
        
        # Agrupar por funcionário e data
        df_sorted = df.sort_values(['funcionario', 'data', 'descricao'])
        
        for funcionario in df['funcionario'].unique():
            func_df = df_sorted[df_sorted['funcionario'] == funcionario]
            
            # Verificar transações do mesmo dia com descrições similares
            for data in func_df['data'].unique():
                day_transactions = func_df[func_df['data'] == data]
                
                # Buscar pares de transações similares
                transactions_list = list(day_transactions.iterrows())
                
                for i in range(len(transactions_list)):
                    for j in range(i + 1, len(transactions_list)):
                        idx1, row1 = transactions_list[i]
                        idx2, row2 = transactions_list[j]
                        
                        # Criar chave única para o par
                        pair_key = tuple(sorted([row1['id_transacao'], row2['id_transacao']]))
                        if pair_key in detected_pairs:
                            continue
                        
                        # Verificar similaridade de descrição
                        desc1_words = set(row1['descricao'].lower().split())
                        desc2_words = set(row2['descricao'].lower().split())
                        
                        if not desc1_words or not desc2_words:
                            continue
                        
                        similarity = len(desc1_words & desc2_words) / len(desc1_words | desc2_words)
                        
                        # Se descrições muito similares e ambas entre $300-$500
                        if similarity > 0.6 and 300 <= row1['valor'] <= 500 and 300 <= row2['valor'] <= 500:
                            total = row1['valor'] + row2['valor']
                            if total > 500:
                                detected_pairs.add(pair_key)
                                violations.append({
                                    'transaction': {
                                        'id_1': row1['id_transacao'],
                                        'id_2': row2['id_transacao'],
                                        'funcionario': funcionario,
                                        'data': data,
                                        'valor_total': total,
                                        'valor_1': row1['valor'],
                                        'valor_2': row2['valor'],
                                        'descricao_1': row1['descricao'],
                                        'descricao_2': row2['descricao'],
                                        'similaridade': f"{similarity*100:.1f}%"
                                    },
                                    'violation_type': 'SMURFING',
                                    'severity': 10,
                                    'rule': 'Seção 1.3 - Proibição de Smurfing',
                                    'reason': f'Possível estruturação: duas compras similares ({similarity*100:.0f}% similar) no mesmo dia totalizando ${total:.2f}',
                                    'evidence': f'TX1: {row1["id_transacao"]} (${row1["valor"]:.2f}) + TX2: {row2["id_transacao"]} (${row2["valor"]:.2f})'
                                })
        
        return violations
    
    def _check_restricted_locations(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta uso de locais restritos - Seção 2.1"""
        violations = []
        
        # Lista de locais restritos
        restricted_locations = ['hooters', 'hooter']
        
        for idx, row in df.iterrows():
            description_lower = row['descricao'].lower()
            
            for location in restricted_locations:
                if location in description_lower:
                    violations.append({
                        'transaction': row.to_dict(),
                        'violation_type': 'LOCAL_RESTRITO',
                        'severity': 6,
                        'rule': 'Seção 2.1 - Locais Restritos',
                        'reason': f'Refeição em local restrito: {location.title()} (banido da lista de reembolso)',
                        'evidence': f'Descrição: {row["descricao"]}'
                    })
                    break
        
        return violations
    
    def _check_suspicious_categories(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta padrões suspeitos em categorias"""
        violations = []
        
        # Categoria "Segurança" é suspeita (pode indicar armamento)
        if 'categoria' in df.columns:
            security_df = df[df['categoria'] == 'Segurança']
            
            for idx, row in security_df.iterrows():
                violations.append({
                    'transaction': row.to_dict(),
                    'violation_type': 'CATEGORIA_SUSPEITA',
                    'severity': 7,
                    'rule': 'Seção 3.2 - Armamento e Defesa',
                    'reason': 'Despesa categorizada como "Segurança" (possível armamento)',
                    'evidence': f'Descrição: {row["descricao"]}, Valor: ${row["valor"]:.2f}'
                })
        
        return violations
    
    def _deduplicate_frauds(self, frauds: List[Dict]) -> List[Dict]:
        """Remove duplicatas mantendo a violação mais severa"""
        # Agrupar por ID de transação
        fraud_dict = {}
        
        for fraud in frauds:
            # Obter ID da transação
            tx = fraud['transaction']
            if isinstance(tx, dict):
                tx_id = tx.get('id_transacao', tx.get('id_1', str(hash(str(tx)))))
            else:
                continue
            
            if tx_id not in fraud_dict or fraud['severity'] > fraud_dict[tx_id]['severity']:
                fraud_dict[tx_id] = fraud
        
        return list(fraud_dict.values())
    
    def _generate_report(self, frauds: List[Dict], total: int) -> str:
        """Gera relatório consolidado"""
        
        if not frauds:
            return """
╔══════════════════════════════════════════════════════════════════════╗
║         RELATÓRIO DE AUDITORIA - FRAUDES STANDALONE                  ║
╚══════════════════════════════════════════════════════════════════════╝

STATUS: ✓ NENHUMA VIOLAÇÃO DETECTADA

Todas as transações estão em conformidade com a política de compliance.

Recomendação: Nenhuma ação necessária.
"""
        
        # Organizar por tipo e severidade
        by_type = {}
        for fraud in frauds:
            vtype = fraud['violation_type']
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(fraud)
        
        high_severity = [f for f in frauds if f['severity'] >= 8]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║         RELATÓRIO DE AUDITORIA - FRAUDES STANDALONE                  ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️  VIOLAÇÕES DETECTADAS

ESTATÍSTICAS:
- Total de transações analisadas: {total}
- Violações encontradas: {len(frauds)}
- Alta severidade (≥8): {len(high_severity)}

VIOLAÇÕES POR TIPO:
"""
        
        for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            report += f"  • {vtype}: {len(items)} caso(s)\n"
        
        report += "\n" + "─"*70 + "\n"
        report += "TOP 10 VIOLAÇÕES MAIS SEVERAS:\n"
        report += "─"*70 + "\n\n"
        
        # Ordenar por severidade
        sorted_frauds = sorted(frauds, key=lambda x: -x['severity'])
        
        for i, fraud in enumerate(sorted_frauds[:10], 1):
            tx = fraud['transaction']
            report += f"[{i}] {fraud['violation_type']} - Severidade: {fraud['severity']}/10\n"
            report += f"    Regra: {fraud['rule']}\n"
            report += f"    Razão: {fraud['reason']}\n"
            report += f"    {fraud['evidence']}\n"
            
            if isinstance(tx, dict):
                if 'id_transacao' in tx:
                    report += f"    ID: {tx['id_transacao']} | Funcionário: {tx.get('funcionario', 'N/A')}\n"
                elif 'id_1' in tx:
                    report += f"    IDs: {tx['id_1']} + {tx['id_2']} | Funcionário: {tx.get('funcionario', 'N/A')}\n"
                    report += f"    Similaridade: {tx.get('similaridade', 'N/A')}\n"
            report += "\n"
        
        report += f"""
{'─'*70}
CONCLUSÃO:
⚠️  {len(frauds)} violação(ões) de compliance detectada(s)
⚠️  Ação recomendada: Revisão com RH e possível ação disciplinar

Relatório gerado pelo Sistema de Auditoria Dunder Mifflin
"""
        
        return report


def main():
    """Executa detecção de fraudes standalone"""
    print("=" * 80)
    print("AGENTE 3A: DETECTOR DE FRAUDES STANDALONE")
    print("=" * 80)
    print()
    
    # Mostrar configuração do LLM
    config.print_config_info()
    
    detector = StandaloneFraudDetector()
    
    print("🔍 Iniciando análise de transações...\n")
    
    start_time = time.time()
    results = detector.analyze_transactions()
    total_elapsed = time.time() - start_time
    
    print(f"\n⏱️  Tempo total: {total_elapsed:.2f}s\n")
    
    print(results['report'])
    
    # Salvar detalhes em CSV
    if results['fraudulent_transactions']:
        print("\n💾 Salvando detalhes das violações...")
        
        fraud_details = []
        for fraud in results['fraudulent_transactions']:
            tx = fraud['transaction']
            if isinstance(tx, dict):
                # Transação simples
                if 'id_transacao' in tx:
                    fraud_details.append({
                        'id_transacao': tx['id_transacao'],
                        'funcionario': tx.get('funcionario', 'N/A'),
                        'data': tx.get('data', 'N/A'),
                        'valor': tx.get('valor', 0),
                        'descricao': tx.get('descricao', 'N/A'),
                        'violation_type': fraud['violation_type'],
                        'severity': fraud['severity'],
                        'rule': fraud['rule'],
                        'reason': fraud['reason']
                    })
                # Smurfing (par de transações)
                elif 'id_1' in tx:
                    fraud_details.append({
                        'id_transacao': f"{tx['id_1']} + {tx['id_2']}",
                        'funcionario': tx.get('funcionario', 'N/A'),
                        'data': tx.get('data', 'N/A'),
                        'valor': tx.get('valor_total', 0),
                        'descricao': f"{tx.get('descricao_1', '')} | {tx.get('descricao_2', '')}",
                        'violation_type': fraud['violation_type'],
                        'severity': fraud['severity'],
                        'rule': fraud['rule'],
                        'reason': fraud['reason']
                    })
        
        if fraud_details:
            import pandas as pd
            df_frauds = pd.DataFrame(fraud_details)
            output_path = 'fraudes_standalone.csv'
            df_frauds.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo salvo: {output_path}")


if __name__ == "__main__":
    main()