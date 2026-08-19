import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.estado import EstadoAnalise
from src.nos import (
    alinhar_entidades, 
    gerar_consulta_sql, 
    validar_consulta_sql, 
    executar_consulta_sql, 
    planejar_grafico,
    gerar_resposta_final
)

def testar_fluxo_completo() -> None:
    print("🚀 Iniciando Teste do Fluxo Completo (com DataViz)...\n")
    
    estado_simulado: EstadoAnalise = {
        "pergunta": "Compare as vendas globais do Wii Sports e do Tetris", 
        "dicas_entidades": "",
        "consulta_sql": "",
        "sql_valido": False,
        "resultado_consulta": [],
        "dados_encontrados": True,
        "resposta_final": "",
        "erro": None,
        "tentativas_correcao": 0,
        "config_grafico": None 
    }
    
    print(f"👤 Pergunta: '{estado_simulado['pergunta']}'\n" + "-" * 50)
    
    estado_simulado.update(alinhar_entidades(estado_simulado))
    estado_simulado.update(gerar_consulta_sql(estado_simulado))
    estado_simulado.update(validar_consulta_sql(estado_simulado))
    
    if not estado_simulado.get("sql_valido"):
        print(f"\n🚨 FLUXO ABORTADO: {estado_simulado.get('erro')}")
        return
        
    estado_simulado.update(executar_consulta_sql(estado_simulado))
    estado_simulado.update(planejar_grafico(estado_simulado))
    estado_simulado.update(gerar_resposta_final(estado_simulado))
    
    print("\n================ RELATÓRIO FINAL ================\n")
    print(estado_simulado["resposta_final"])
    print("\n================ CONFIGURAÇÃO DO GRÁFICO ================\n")
    print(estado_simulado.get("config_grafico"))
    print("\n========================================================")

if __name__ == "__main__":
    testar_fluxo_completo()