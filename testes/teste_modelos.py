import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modelos import instanciar_modelo_sql, instanciar_modelo_analista
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_openai import ChatOpenAI

def testar_modelos() -> None:
    """
    Função de teste para garantir que a comunicação com o OpenRouter 
    e os modelos especializados está funcionando corretamente.
    """
    print("Iniciando testes de conexão com OpenRouter...\n")

    # 1. Instanciando os modelos
    print("⏳ Carregando instâncias...")
    modelo_sql: ChatOpenAI = instanciar_modelo_sql()
    modelo_analista: ChatOpenAI = instanciar_modelo_analista()
    print("✅ Modelos instanciados!\n")

    # 2. Testando o Modelo Especialista em SQL
    print("=========================================")
    print("🧪 TESTE 1: MODELO SQL (Cohere North Mini Code)")
    
    # Criamos o contexto da mensagem
    mensagens_sql = [
        SystemMessage(content="Você é um assistente de banco de dados. Escreva apenas o comando SQL, sem explicações."),
        HumanMessage(content="Crie uma query em PostgreSQL para selecionar todos os usuários ativos da tabela 'clientes'.")
    ]
    
    print("Enviando requisição (aguarde)...")
    resposta_sql: BaseMessage = modelo_sql.invoke(mensagens_sql)
    print("\n🔹 Resposta do Modelo SQL:")
    print(resposta_sql.content)
    print("=========================================\n")

    # 3. Testando o Modelo Analista
    print("=========================================")
    print("🧪 TESTE 2: MODELO ANALISTA (GPT OSS 20B)")
    
    mensagens_analista = [
        SystemMessage(content="Você é um analista de dados conciso. Explique os números em uma frase simples."),
        HumanMessage(content="Nossa análise retornou que as vendas globais caíram de 100 mil para 80 mil no último ano.")
    ]
    
    print("Enviando requisição (aguarde)...")
    resposta_analista: BaseMessage = modelo_analista.invoke(mensagens_analista)
    print("\n🔹 Resposta do Modelo Analista:")
    print(resposta_analista.content)
    print("=========================================\n")

if __name__ == "__main__":
    testar_modelos()