"""
Agente 1: Chatbot de Consulta de Compliance (RAG)

Este agente é responsável por responder perguntas sobre as regras de compliance
usando Retrieval-Augmented Generation (RAG) com ChromaDB.

Arquitetura:
- Vector Store: ChromaDB
- Embeddings: ChromaDB default (all-MiniLM-L6-v2)
- LLM: Groq (Llama 3.1 70B ou modelo configurado)
- Retrieval: Top-k similarity search
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict
import config
from utils.document_loader import load_compliance_policy, split_text_for_rag
from utils.llm_adapter import LLMAdapter


class ComplianceRAGAgent:
    """
    Agente de RAG para consultas sobre política de compliance
    Compatível com múltiplos provedores de LLM via LLMAdapter
    """
    
    def __init__(self):
        # Usar adaptador universal de LLM
        self.llm = LLMAdapter()
        
        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(config.CHROMA_PERSIST_DIR)
        )
        
        # Tentar obter coleção existente ou criar nova
        try:
            self.collection = self.chroma_client.get_collection(
                name=config.COLLECTION_NAME
            )
            print("✓ Coleção ChromaDB carregada")
        except:
            print("Criando nova coleção ChromaDB...")
            self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Inicializa o vector store com a política de compliance"""
        # Carregar política
        policy_text = load_compliance_policy(str(config.COMPLIANCE_POLICY_PATH))
        
        # Dividir em chunks
        chunks = split_text_for_rag(policy_text, chunk_size=800, chunk_overlap=150)
        
        # Criar coleção
        # ChromaDB usa embeddings padrão (all-MiniLM-L6-v2) automaticamente
        self.collection = self.chroma_client.create_collection(
            name=config.COLLECTION_NAME,
            metadata={"description": "Dunder Mifflin Compliance Policy"}
        )
        
        # Adicionar chunks ao vector store
        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                ids=[f"chunk_{i}"],
                metadatas=[{"chunk_id": i, "source": "politica_compliance.txt"}]
            )
        
        print(f"✓ Vector store inicializado com {len(chunks)} chunks")
    
    def _retrieve_relevant_chunks(self, query: str, n_results: int = 4) -> List[str]:
        """
        Recupera chunks relevantes para a query
        
        Args:
            query: Pergunta do usuário
            n_results: Número de chunks a retornar (padrão: 4)
            
        Returns:
            Lista de chunks relevantes
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results['documents'][0] if results['documents'] else []
    
    def query(self, user_question: str) -> str:
        """
        Responde pergunta do usuário usando RAG
        
        Args:
            user_question: Pergunta do funcionário
            
        Returns:
            Resposta fundamentada na política de compliance
        """
        # Recuperar chunks relevantes
        relevant_chunks = self._retrieve_relevant_chunks(user_question, n_results=4)
        
        if not relevant_chunks:
            return "Desculpe, não encontrei informações relevantes na política de compliance para responder sua pergunta."
        
        # Construir contexto
        context = "\n\n---\n\n".join(relevant_chunks)
        
        # System prompt otimizado para Groq/Llama
        system_prompt = """Você é um assistente especializado em compliance da Dunder Mifflin.
Sua função é ajudar funcionários a entender e seguir as políticas de compliance da empresa.

REGRAS IMPORTANTES:
1. Responda APENAS com base no contexto fornecido da política de compliance
2. Se a informação não estiver no contexto, diga explicitamente que não encontrou
3. Seja preciso e cite seções específicas quando relevante (ex: "De acordo com a Seção 1.1...")
4. Use um tom profissional mas acessível e direto
5. Se houver valores monetários ou prazos, cite-os exatamente como aparecem na política
6. Sempre que possível, explique PORQUÊ a regra existe (contexto/motivação)
7. Seja conciso mas completo - não invente informações além do contexto fornecido"""

        user_prompt = f"""CONTEXTO DA POLÍTICA DE COMPLIANCE:
{context}

PERGUNTA DO FUNCIONÁRIO:
{user_question}

Por favor, responda à pergunta com base apenas nas informações do contexto acima. Seja direto e preciso."""

        # Usar adaptador LLM (funciona com Groq)
        answer = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return answer
    
    def reset_vector_store(self):
        """Reseta o vector store (útil para testes)"""
        try:
            self.chroma_client.delete_collection(name=config.COLLECTION_NAME)
            print("✓ Vector store resetado")
        except:
            print("Nenhum vector store para resetar")


def main():
    """Teste interativo do agente"""
    print("=" * 80)
    print("AGENTE 1: CHATBOT DE CONSULTA DE COMPLIANCE")
    print("=" * 80)
    print()
    
    # Mostrar configuração do LLM
    config.print_config_info()
    
    agent = ComplianceRAGAgent()
    
    # Perguntas de teste
    test_questions = [
        "Qual é o limite de gastos que posso fazer sem aprovação?",
        "Posso comprar equipamento de karaokê para uma apresentação de vendas?",
        "Quem aprova despesas entre $50 e $500?",
        "Posso dividir uma compra de $800 em duas notas fiscais de $400?",
        "Posso ser reembolsado por um jantar no Hooters com um cliente?"
    ]
    
    print("\n" + "="*80)
    print("TESTES AUTOMÁTICOS")
    print("="*80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}: {question}")
        print(f"{'='*80}")
        
        import time
        start_time = time.time()
        answer = agent.query(question)
        elapsed = time.time() - start_time
        
        print(f"\nRESPOSTA:\n{answer}")
        print(f"\n⏱️  Tempo: {elapsed:.2f}s")
    
    # Modo interativo
    print("\n" + "="*80)
    print("MODO INTERATIVO (digite 'sair' para encerrar)")
    print("="*80)
    
    while True:
        question = input("\n📋 Sua pergunta: ").strip()
        if question.lower() in ['sair', 'exit', 'quit', 'voltar']:
            break
        if question:
            import time
            start_time = time.time()
            answer = agent.query(question)
            elapsed = time.time() - start_time
            
            print(f"\n💡 Resposta: {answer}")
            print(f"⏱️  Tempo: {elapsed:.2f}s\n")
            print("-" * 80)


if __name__ == "__main__":
    main()