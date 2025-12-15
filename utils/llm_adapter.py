"""
Adaptador universal para diferentes provedores de LLM
Suporta: Groq
"""
from typing import Optional
import config


class LLMAdapter:
    """
    Adaptador que abstrai diferenças entre provedores de LLM
    """
    
    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.model = config.MODEL_NAME
        
        if self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=config.GROQ_API_KEY)
            
        else:
            raise ValueError(f"Provider não suportado: {self.provider}")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Gera resposta do LLM de forma unificada
        
        Args:
            system_prompt: Instruções do sistema
            user_prompt: Pergunta/prompt do usuário
            temperature: Temperatura (0-1), padrão do config
            max_tokens: Máximo de tokens, padrão do config
            
        Returns:
            Resposta do LLM como string
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.MAX_TOKENS
        
        if self.provider == "groq":
            return self._generate_groq(system_prompt, user_prompt, temperature, max_tokens)
    
    def _generate_groq(self, system_prompt: str, user_prompt: str, 
                       temperature: float, max_tokens: int) -> str:
        """Gera resposta usando Groq"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def __repr__(self):
        return f"LLMAdapter(provider={self.provider}, model={self.model})"