from typing import TypedDict, List, Dict, Optional

class EstadoAnalise(TypedDict):
    """
    Define a estrutura de dados que circulará pelo nosso grafo.
    Cada nó receberá esse estado e retornará um dicionário apenas com as chaves que deseja atualizar.
    """
    pergunta: str                 # A pergunta original do usuário em linguagem natural
    consulta_sql: str             # O código SQL gerado pelo LLM especialista em código
    sql_valido: bool              # Flag de segurança indicando se a query passou nas validações
    resultado_consulta: List[Dict]# Os dados retornados pelo DuckDB
    resposta_final: str           # O relatório final gerado pelo LLM analista
    erro: Optional[str]           # Mensagem de erro (útil para o modelo tentar corrigir a query)