from langgraph.graph import StateGraph, END
from src.estado import EstadoAnalise
from src.nos import (
    alinhar_entidades,
    gerar_consulta_sql,
    validar_consulta_sql,
    executar_consulta_sql,
    gerar_resposta_final
)

LIMITE_TENTATIVAS = 2

def rotear_apos_validacao(estado: EstadoAnalise) -> str:
    """
    Decide o próximo passo após a validação de segurança (busca por DROP/DELETE).
    """
    if estado.get("sql_valido"):
        return "executar_sql"
    
    # Se o SQL for perigoso, verifica se ainda temos tentativas
    if estado.get("tentativas_correcao", 0) < LIMITE_TENTATIVAS:
        return "gerar_sql" # auto-correção
        
    return "gerar_resposta" #segue para gerar o relatório de erro

def rotear_apos_execucao(estado: EstadoAnalise) -> str:
    """
    Decide o próximo passo após rodar a query no DuckDB.
    """
    # Se o DuckDB retornou um erro de sintaxe ou coluna inexistente
    if estado.get("erro"):
        if estado.get("tentativas_correcao", 0) < LIMITE_TENTATIVAS:
            return "gerar_sql"
        return "gerar_resposta"
        
    return "gerar_resposta"

def compilar_grafo():
    """
    Monta a estrutura do agente, definindo os nós e os caminhos (arestas).
    """
    workflow = StateGraph(EstadoAnalise)

    workflow.add_node("alinhar_entidades", alinhar_entidades)
    workflow.add_node("gerar_sql", gerar_consulta_sql)
    workflow.add_node("validar_sql", validar_consulta_sql)
    workflow.add_node("executar_sql", executar_consulta_sql)
    workflow.add_node("gerar_resposta", gerar_resposta_final)

    workflow.set_entry_point("alinhar_entidades")

    workflow.add_edge("alinhar_entidades", "gerar_sql")
    workflow.add_edge("gerar_sql", "validar_sql")
    workflow.add_edge("gerar_resposta", END)

    # Arestas condicionais
    workflow.add_conditional_edges(
        "validar_sql", 
        rotear_apos_validacao
    )
    
    workflow.add_conditional_edges(
        "executar_sql",
        rotear_apos_execucao
    )
    
    # Compila o grafo
    app = workflow.compile()
    
    return app


agente_simplesql = compilar_grafo()