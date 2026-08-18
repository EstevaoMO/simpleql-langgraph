import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.estado import EstadoAnalise
from src.nos import gerar_consulta_sql, validar_consulta_sql, executar_consulta_sql

def testar_fluxo_ate_banco() -> None:
    """
    Testa a extração da intenção, geração do SQL, validação e execução no DuckDB.
    Simula o estado do LangGraph rodando as funções sequencialmente.
    """
    print("Iniciando Teste do Fluxo de Banco de Dados...\n")
    
    estado_simulado: EstadoAnalise = {
        "pergunta": "Quais foram os 5 jogos com maiores vendas globais em toda a história?",
        "consulta_sql": "",
        "sql_valido": False,
        "resultado_consulta": [],
        "resposta_final": "",
        "erro": None
    }
    
    atualizacao_geracao = gerar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_geracao) # Mmscla o resultado na prancheta
    
    atualizacao_validacao = validar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_validacao)
    
    atualizacao_execucao = executar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_execucao)
    
    print("\n================ RESULTADO FINAL DA EXTRAÇÃO ================")
    print(f"Pergunta: {estado_simulado['pergunta']}")
    print(f"SQL Válido: {estado_simulado['sql_valido']}")
    
    if estado_simulado["erro"]:
         print(f"Erro capturado: {estado_simulado['erro']}")
    else:
        print("\nDados extraídos (Primeiros 5 registros):")
        for linha in estado_simulado['resultado_consulta']:
            print(f" - {linha}")
    print("=============================================================\n")

if __name__ == "__main__":
    testar_fluxo_ate_banco()