import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.estado import EstadoAnalise
from src.nos import (
    alinhar_entidades, 
    gerar_consulta_sql, 
    validar_consulta_sql, 
    executar_consulta_sql, 
    gerar_resposta_final
)

def testar_fluxo_completo() -> None:
    """
    Testa todo o pipeline linearmente: alinhamento semântico, extração da intenção, 
    geração do SQL, validação, execução no DuckDB e interpretação final.
    """
    print("🚀 Iniciando Teste do Fluxo Completo do SimplesQL...\n")
    
    estado_simulado: EstadoAnalise = {
        "pergunta": "Qual vendeu mais, gta 5 ou red dead?",
        "dicas_entidades": "",
        "consulta_sql": "",
        "sql_valido": False,
        "resultado_consulta": [],
        "resposta_final": "",
        "erro": None,
        "tentativas_correcao": 0,
        "dados_encontrados": True
    }
    
    print(f"👤 Pergunta do Usuário: '{estado_simulado['pergunta']}'\n")
    print("-" * 50)
    
    atualizacao_alinhamento = alinhar_entidades(estado_simulado)
    estado_simulado.update(atualizacao_alinhamento)
    print(f"    [Estado Atualizado] Dicas geradas: \n{estado_simulado['dicas_entidades']}\n")
    
    atualizacao_geracao = gerar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_geracao) 
    
    atualizacao_validacao = validar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_validacao)
    
    atualizacao_execucao = executar_consulta_sql(estado_simulado)
    estado_simulado.update(atualizacao_execucao)
    
    atualizacao_analise = gerar_resposta_final(estado_simulado)
    estado_simulado.update(atualizacao_analise)
    
    print("\n================ RELATÓRIO FINAL GERADO ================\n")
    print(estado_simulado["resposta_final"])
    print("\n========================================================")

if __name__ == "__main__":
    testar_fluxo_completo()