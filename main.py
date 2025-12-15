"""
Sistema de Auditoria Dunder Mifflin - Menu Principal

Este é o ponto de entrada principal do sistema.
Permite executar cada agente individualmente ou todos juntos.
"""

import sys
import time
from pathlib import Path
import csv

# Adicionar diretório atual ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

import config


def print_banner():
    """Imprime banner do sistema"""
    print()
    print("=" * 80)
    print(" " * 20 + "SISTEMA DE AUDITORIA DUNDER MIFFLIN")
    print("=" * 80)
    print()


def print_menu():
    """Imprime menu de opções"""
    print("Escolha um agente para executar:")
    print()
    print("  [1] Agente 1: RAG de Compliance (Chatbot)")
    print("  [2] Agente 2: Detector de Teorias da Conspiração")
    print("  [3] Agente 3A: Detector de Fraudes Standalone")
    print("  [4] Agente 3B: Detector de Fraudes Contextuais")
    print("  [5] Executar TODOS os agentes")
    print("  [0] Sair")
    print()


def run_compliance_rag():
    """Executa Agente 1: RAG de Compliance"""
    try:
        from agents.compliance_rag_agent import ComplianceRAGAgent
        
        print("\n" + "=" * 80)
        print("AGENTE 1: RAG DE COMPLIANCE")
        print("=" * 80)
        
        agent = ComplianceRAGAgent()
        
        # Modo interativo
        print("\nChatbot de Compliance iniciado!")
        print("Digite suas perguntas (ou 'sair' para voltar ao menu)\n")
        
        while True:
            pergunta = input("Você: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                break
            
            if not pergunta:
                continue
            
            resposta = agent.query(pergunta)
            print(f"\nAssistente: {resposta}\n")
        
        print("\n✓ Agente 1 finalizado\n")
        
    except ImportError as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o arquivo agents/compliance_rag_agent.py existe.\n")
    except Exception as e:
        print(f"\n❌ Erro ao executar Agente 1: {e}\n")


def run_conspiracy_detector():
    """Executa Agente 2: Detector de Teorias da Conspiração"""
    try:
        from agents.conspiracy_agent import ConspiracyDetectionAgent
        
        print("\n" + "=" * 80)
        print("AGENTE 2: DETECTOR DE TEORIAS DA CONSPIRAÇÃO")
        print("=" * 80)
        
        detector = ConspiracyDetectionAgent()
        
        start_time = time.time()
        results = detector.analyze_emails()
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Tempo total: {elapsed:.2f}s\n")
        print(results['report'])
        
        # Salvar CSV
        if results['suspicious_emails']:
            save_suspicious_emails_csv(results['suspicious_emails'])
            print(f"\n💾 {len(results['suspicious_emails'])} emails suspeitos salvos em: emails_suspeitos.csv")


        
        print("\n✓ Agente 2 finalizado\n")
        
    except ImportError as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o arquivo agents/conspiracy_agent.py existe.\n")
    except Exception as e:
        print(f"\n❌ Erro ao executar Agente 2: {e}\n")


def run_standalone_fraud_detector():
    """Executa Agente 3A: Detector de Fraudes Standalone"""
    try:
        from agents.standalone_fraud_agent import StandaloneFraudDetector
        
        print("\n" + "=" * 80)
        print("AGENTE 3A: DETECTOR DE FRAUDES STANDALONE")
        print("=" * 80)
        
        detector = StandaloneFraudDetector()
        
        start_time = time.time()
        results = detector.analyze_transactions()
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Tempo total: {elapsed:.2f}s\n")
        print(results['report'])
        
        # Salvar CSV
        if results['fraudulent_transactions']:
            save_standalone_frauds_csv(results['fraudulent_transactions'])
            print(f"\n💾 {len(results['fraudulent_transactions'])} violações salvas em: fraudes_standalone.csv")

        
        print("\n✓ Agente 3A finalizado\n")
        
    except ImportError as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o arquivo agents/standalone_fraud_agent.py existe.\n")
    except Exception as e:
        print(f"\n❌ Erro ao executar Agente 3A: {e}\n")


def run_contextual_fraud_detector():
    """Executa Agente 3B: Detector de Fraudes Contextuais"""
    try:
        from agents.contextual_fraud_agent import ContextualFraudDetector
        
        print("\n" + "=" * 80)
        print("AGENTE 3B: DETECTOR DE FRAUDES CONTEXTUAIS")
        print("=" * 80)
        
        detector = ContextualFraudDetector()
        
        start_time = time.time()
        results = detector.analyze_contextual_frauds()
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Tempo total: {elapsed:.2f}s\n")
        print(results['report'])
        
        # Salvar CSV
        if results['contextual_frauds']:
            save_contextual_frauds_csv(results['contextual_frauds'])
            print(f"\n💾 {len(results['contextual_frauds'])} fraudes contextuais salvas em: fraudes_contextuais.csv")
        
        print("\n✓ Agente 3B finalizado\n")
        
    except ImportError as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o arquivo agents/contextual_fraud_agent.py existe.\n")
    except Exception as e:
        print(f"\n❌ Erro ao executar Agente 3B: {e}\n")

def save_suspicious_emails_csv(suspicious_emails, filename="emails_suspeitos.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "de", "para", "data", "assunto",
            "is_suspicious", "severity", "reasoning", "evidence_quotes"
        ])

        for item in suspicious_emails:
            email = item["email"]
            analysis = item["analysis"]

            writer.writerow([
                email.get("de"),
                email.get("para"),
                email.get("data"),
                email.get("assunto"),
                analysis.get("is_suspicious"),
                analysis.get("severity"),
                analysis.get("reasoning"),
                "; ".join(analysis.get("evidence_quotes", []))
            ])


def save_standalone_frauds_csv(fraudulent_transactions, filename="fraudes_standalone.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not fraudulent_transactions:
            return

        # Cabeçalho dinâmico baseado nas chaves
        writer.writerow(fraudulent_transactions[0].keys())

        for tx in fraudulent_transactions:
            writer.writerow(tx.values())


def save_contextual_frauds_csv(contextual_frauds, filename="fraudes_contextuais.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not contextual_frauds:
            return

        writer.writerow(contextual_frauds[0].keys())

        for fraud in contextual_frauds:
            writer.writerow(fraud.values())

def run_all_agents():
    """Executa todos os agentes em sequência"""
    print("\n" + "=" * 80)
    print("EXECUTANDO TODOS OS AGENTES")
    print("=" * 80)
    
    total_start = time.time()
    
    # Agente 2: Conspiração
    print("\n[1/3] Executando Agente 2: Detector de Teorias da Conspiração...")
    run_conspiracy_detector()
    
    # Agente 3A: Fraudes Standalone
    print("\n[2/3] Executando Agente 3A: Detector de Fraudes Standalone...")
    run_standalone_fraud_detector()
    
    # Agente 3B: Fraudes Contextuais
    print("\n[3/3] Executando Agente 3B: Detector de Fraudes Contextuais...")
    run_contextual_fraud_detector()
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 80)
    print(f"✅ TODOS OS AGENTES EXECUTADOS EM {total_elapsed:.2f}s")
    print("=" * 80)
    print("\nArquivos gerados:")
    print("  • emails_suspeitos.csv")
    print("  • fraudes_standalone.csv")
    print("  • fraudes_contextuais.csv")
    print()


def main():
    """Função principal"""
    print_banner()
    config.print_config_info()
    
    # Verificar arquivos de dados
    try:
        config.check_data_files()
        print("✓ Todos os arquivos de dados encontrados\n")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    
    # Menu interativo
    while True:
        print_menu()
        
        try:
            choice = input("Escolha uma opção [0-5]: ").strip()
            
            if choice == '0':
                print("\n👋 Encerrando sistema...\n")
                break
            
            elif choice == '1':
                run_compliance_rag()
            
            elif choice == '2':
                run_conspiracy_detector()
            
            elif choice == '3':
                run_standalone_fraud_detector()
            
            elif choice == '4':
                run_contextual_fraud_detector()
            
            elif choice == '5':
                run_all_agents()
            
            else:
                print("\n❌ Opção inválida. Escolha um número de 0 a 5.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando sistema...\n")
            break
        
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()