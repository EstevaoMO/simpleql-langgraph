import re
import duckdb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.modelos import instanciar_modelo_sql
from src.estado import EstadoAnalise
from src.prompts import PROMPT_GERACAO_SQL

# Parser que garante que a saída seja sempre uma string limpa
parser = StrOutputParser()

def gerar_consulta_sql(estado: EstadoAnalise) -> dict:
    """
    Nó 1: Recebe a pergunta do usuário e gera a consulta SQL utilizando o modelo especialista.
    """
    print("[Nó: Geração de SQL] Traduzindo pergunta para DuckDB...")
    
    pergunta_usuario = estado["pergunta"]
    
    # Cadeia LCEL: Prompt -> LLM -> Saída Limpa (String)
    modelo = instanciar_modelo_sql()
    cadeia = PROMPT_GERACAO_SQL | modelo | parser
    
    resposta_bruta = cadeia.invoke({"pergunta": pergunta_usuario})
    
    # Tratamento de segurança para garantir que a resposta seja apenas a consulta SQL limpa
    sql_limpo = resposta_bruta.replace("```sql", "").replace("```", "").strip()
    print(f"    ↳ SQL Gerado: {sql_limpo}") # debug

    return {"consulta_sql": sql_limpo}

def validar_consulta_sql(estado: EstadoAnalise) -> dict:
    """
    Nó 2: Analisa a string do SQL gerado em busca de comandos destrutivos.
    Retorna se a query é válida ou não.
    """
    print("[Nó: Validação de SQL] Verificando segurança da query...")
    
    consulta = estado.get("consulta_sql", "").upper()
    
    # Lista de palavras-chave proibidas que alteram o banco de dados
    comandos_proibidos = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE TABLE"]
    
    for comando in comandos_proibidos:
        # Usamos regex para encontrar a palavra inteira (\b)
        padrao = rf"\b{comando}\b"
        if re.search(padrao, consulta):
            erro_msg = f"Falha de Segurança: A consulta contém o comando proibido '{comando}'."
            print(f"    🚨 {erro_msg}")
            return {"sql_valido": False, "erro": erro_msg}
            
    print("    ✅ SQL validado com sucesso. Nenhuma operação destrutiva encontrada.")
    return {"sql_valido": True, "erro": None}

def executar_consulta_sql(estado: EstadoAnalise) -> dict:
    """
    Nó 3: Conecta ao DuckDB, cria uma visualização em memória do CSV e executa a query.
    """
    print("[Nó: Execução] Rodando a consulta no DuckDB...")
    
    # Se a query não for válida, aborta a execução
    if not estado.get("sql_valido"):
        print("    ⚠️ Execução abortada devido a SQL inválido.")
        return {"resultado_consulta": []}
        
    consulta = estado["consulta_sql"]
    
    try:
        conn = duckdb.connect(database=':memory:')
        
        caminho_csv = "db/vgsales.csv"
        conn.execute(f"CREATE VIEW vgsales AS SELECT * FROM read_csv_auto('{caminho_csv}')")
        
        df_resultado = conn.execute(consulta).fetchdf()
        
        # Converte o DataFrame para uma lista de dicionários
        dados_finais = df_resultado.to_dict(orient="records")
        
        print(f"    ✅ Consulta retornou {len(dados_finais)} linha(s).")
        return {"resultado_consulta": dados_finais, "erro": None}
        
    except Exception as e: # Se o DuckDB estourar um erro
        erro_msg = f"Erro na execução do banco de dados: {str(e)}"
        print(f"    🚨 {erro_msg}")
        return {"erro": erro_msg}