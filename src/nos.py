import re
import duckdb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.modelos import instanciar_modelo_sql, instanciar_modelo_analista
from src.estado import EstadoAnalise
from src.prompts import PROMPT_GERACAO_SQL, PROMPT_ANALISE_DADOS

# Parser que garante que a saída seja sempre uma string limpa
parser = StrOutputParser()

def gerar_consulta_sql(estado: EstadoAnalise) -> dict:
    print("[Nó: Geração de SQL] Traduzindo pergunta para DuckDB...")
    
    pergunta_usuario = estado["pergunta"]
    erro_anterior = estado.get("erro")
    
    tentativas = estado.get("tentativas_correcao", 0) # fallback para 0 se não existir
    
    # Contexto dinâmico de correção
    if erro_anterior and tentativas > 0:
        instrucao_correcao = f"ATENÇÃO: Sua tentativa anterior falhou com o seguinte erro do banco de dados:\n{erro_anterior}\nPor favor, corrija a sintaxe SQL."
        print(f"    🔄 Tentativa de correção: {tentativas + 1}")
    else:
        instrucao_correcao = ""
    
    modelo = instanciar_modelo_sql()
    cadeia = PROMPT_GERACAO_SQL | modelo | parser
    
    resposta_bruta = cadeia.invoke({
        "pergunta": pergunta_usuario,
        "instrucao_correcao": instrucao_correcao
    })
    
    sql_limpo = resposta_bruta.replace("```sql", "").replace("```", "").strip() # correção redundante para segurança, caso o modelo insira blocos de markdown
    print(f"    ↳ SQL Gerado: {sql_limpo}")
    
    return {
        "consulta_sql": sql_limpo,
        "tentativas_correcao": tentativas + 1,
        "erro": None
    }

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

def gerar_resposta_final(estado: EstadoAnalise) -> dict:
    """
    Nó 4: Interpreta os resultados do banco de dados e monta o relatório final auditável.
    """
    print("[Nó: Análise] Redigindo relatório final...")
    
    pergunta = estado["pergunta"]
    dados_crus = estado.get("resultado_consulta", [])
    sql_utilizado = estado.get("consulta_sql", "N/A")
    erro = estado.get("erro")

    # Mensagem caso ainda haja um erro no fluxo, mesmo após a execução do SQL
    if erro:
        relatorio_erro = f"**Não foi possível concluir a análise.**\n\nMotivo: {erro}"
        return {"resposta_final": relatorio_erro}

    modelo_analista = instanciar_modelo_analista()
    
    # Cadeia LCEL para a análise
    cadeia_analise = PROMPT_ANALISE_DADOS | modelo_analista | parser
    
    texto_interpretacao = cadeia_analise.invoke({
        "pergunta": pergunta,
        "dados": str(dados_crus)
    })
        
    relatorio_final = f"""### 📊 Análise
        {texto_interpretacao}

        ---
        ### 🔎 Evidências e Transparência

        **SQL Utilizado:**
        ```sql
        {sql_utilizado}
        ```

        **Amostra dos Dados Utilizados:**
        {dados_crus[:5]}
        """

    print("✅ Relatório final gerado com sucesso.")
    return {"resposta_final": relatorio_final}