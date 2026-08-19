import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
# Configurando conexão do OpenRouter
URL_BASE_OPENROUTER = "https://openrouter.ai/api/v1"
CHAVE_API = os.getenv("OPENROUTER_API_KEY")
CABECALHOS_OPENROUTER = {
    "HTTP-Referer": "https://github.com/EstevaoMO/simplesql-langgraph",
    "X-Title": "SimplesQL"
}

def instanciar_modelo_sql(temp: float = 0.0) -> ChatOpenAI:
    """
    Retorna o modelo especializado em geração de código e SQL.
    A temperatura padrão é 0.0 para garantir previsibilidade na sintaxe.
    """
    modelo_sql: ChatOpenAI = ChatOpenAI(
        model="cohere/north-mini-code:free", 
        openai_api_key=CHAVE_API,
        openai_api_base=URL_BASE_OPENROUTER,
        temperature=temp,
        default_headers=CABECALHOS_OPENROUTER
    )
    return modelo_sql

def instanciar_modelo_analista(temp: float = 0.2) -> ChatOpenAI:
    """
    Retorna o modelo especializado em interpretação de texto e síntese.
    A temperatura padrão é 0.2 para garantir certa interpretabilidade.
    """
    modelo_analista: ChatOpenAI = ChatOpenAI(
        model="openai/gpt-oss-20b:free", #"google/gemma-4-31b-it:free"
        openai_api_key=CHAVE_API,
        openai_api_base=URL_BASE_OPENROUTER,
        temperature=temp,
        default_headers=CABECALHOS_OPENROUTER
    )
    return modelo_analista

def instanciar_modelo_graficos(temp: float = 0.0) -> ChatOpenAI:
    """
    Retorna o modelo especializado em geração de gráficos a partir de texto e síntese.
    A temperatura padrão é 0.0 para garantir previsibilidade na geração.
    """
    modelo_graficos: ChatOpenAI = ChatOpenAI(
        model="google/gemma-4-26b-a4b-it:free",
        openai_api_key=CHAVE_API,
        openai_api_base=URL_BASE_OPENROUTER,
        temperature=temp,
        default_headers=CABECALHOS_OPENROUTER
    )
    return modelo_graficos