import re
import duckdb
import textwrap
from langchain_core.output_parsers import StrOutputParser

from src.modelos import instanciar_modelo_sql, instanciar_modelo_analista, instanciar_modelo_graficos
from src.estado import EstadoAnalise
from src.prompts import PROMPT_EXTRAIR_ENTIDADES, PROMPT_GERACAO_SQL, PROMPT_ANALISE_DADOS, PROMPT_PLANEJAMENTO_GRAFICO

from pydantic import BaseModel, Field
from typing import Optional, List

class ConfiguracaoGrafico(BaseModel):
    """Schema para forçar a saída estruturada do modelo de visualização."""
    tipo: Optional[str] = Field(
        description="O tipo de gráfico: 'bar', 'line', 'scatter'. Deixe vazio se for um KPI isolado."
    )
    eixo_x: Optional[str] = Field(description="Nome exato da coluna para o eixo X")
    eixo_y: Optional[str] = Field(description="Nome exato da coluna para o eixo Y")
    justificativa: Optional[str] = Field(description="Justificativa breve da escolha visual")

class PlanejamentoVisual(BaseModel):
    graficos: List[ConfiguracaoGrafico] = Field(
        description="Lista de gráficos a serem renderizados. Retorne uma lista vazia [] se for apenas um KPI."
    )

# Parser que garante que a saída seja sempre uma string limpa
parser = StrOutputParser()

def alinhar_entidades(estado: EstadoAnalise) -> dict:
    """
    Nó 0: Extrai termos da pergunta e busca os equivalentes mais próximos no DuckDB (Fuzzy Matching).
    """
    print("[Nó: Alinhamento Semântico] Buscando correspondências exatas no banco...")
    pergunta = estado["pergunta"]
    
    modelo = instanciar_modelo_sql()
    cadeia_extracao = PROMPT_EXTRAIR_ENTIDADES | modelo | parser
    
    termos_brutos = cadeia_extracao.invoke({"pergunta": pergunta})
    
    if not termos_brutos or termos_brutos.strip() == "":
        print("    ↳ Nenhuma entidade específica detectada.")
        return {"dicas_entidades": "Nenhuma dica de entidade específica."}

    termos = [t.strip() for t in termos_brutos.split(",") if t.strip()] # sanitiza a lista gerada
    dicas_encontradas = []
    
    try:
        conn = duckdb.connect(database=':memory:')
        caminho_csv = "db/vgsales.csv"
        conn.execute(f"CREATE VIEW vgsales AS SELECT * FROM read_csv_auto('{caminho_csv}')")
        
        for termo in termos:
            query_similaridade = f"""
                SELECT Name AS correspondencia, 
                       (CASE WHEN Name ILIKE '%{termo}%' THEN 1.0 ELSE 0.0 END) + 
                       (jaro_winkler_similarity(Name, '{termo}') * 0.5) AS score, 
                       'Nome do Jogo' as tipo
                FROM vgsales
                UNION ALL
                SELECT Publisher AS correspondencia, 
                       (CASE WHEN Publisher ILIKE '%{termo}%' THEN 1.0 ELSE 0.0 END) + 
                       (jaro_winkler_similarity(Publisher, '{termo}') * 0.5) AS score, 
                       'Publicadora' as tipo
                FROM vgsales
                ORDER BY score DESC
                LIMIT 1
                """
            resultado = conn.execute(query_similaridade).fetchone()
            
            if resultado and resultado[1] > 0.6: # intervalo de corte
                dicas_encontradas.append(f"O termo '{termo}' refere-se exatamente a '{resultado[0]}' ({resultado[2]}).")
                print(f"    ↳ Match exato encontrado: '{termo}' -> '{resultado[0]}'")
            else: # fallback: se não houver match de alta confiança, o modelo deve usar ILIKE
                dicas_encontradas.append(
                    f"Não encontramos o termo exato '{termo}'. "
                    f"Para este termo, NUNCA use o operador '='. "
                    f"OBRIGATORIAMENTE use a cláusula ILIKE '%{termo}%'."
                )
                print(f"    ↳ Match fraco. Instruindo uso de ILIKE para '{termo}'.")
    except Exception as e:
        print(f"    ⚠️ Erro ao calcular similaridade: {e}")
        return {"dicas_entidades": ""}
        
    texto_dicas = "\n".join(dicas_encontradas) if dicas_encontradas else "Nenhuma correspondência exata de alta confiança encontrada."
    return {"dicas_entidades": texto_dicas}

def gerar_consulta_sql(estado: EstadoAnalise) -> dict:
    """
    Nó 1: Gera a consulta SQL com base na pergunta do usuário.
    """
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
        "dicas": estado.get("dicas_entidades", ""),
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

    if not consulta:
        print("    ⚠️ Consulta SQL vazia. Marcação como inválida.")
        return {"sql_valido": False, "erro": "A partir da pergunta, não foi possível gerar uma consulta SQL válida. Veja se os dados solicitados podem ser encontdados no banco de dados e tente novamente :/"}
    
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

def planejar_grafico(estado: EstadoAnalise) -> dict:
    """
    Nó 4: Analisa os dados retornados e decide a melhor visualização gráfica.
    """
    print("📊 [Nó: DataViz] Planejando estrutura visual...")
    dados = estado.get("resultado_consulta", [])
    
    if not dados:
        return {"config_grafico": []}
        
    colunas_disponiveis = list(dados[0].keys())
    modelo_graficos = instanciar_modelo_graficos()
    
    modelo_estruturado = modelo_graficos.with_structured_output(PlanejamentoVisual)
    cadeia_viz = PROMPT_PLANEJAMENTO_GRAFICO | modelo_estruturado
    
    try:
        resultado = cadeia_viz.invoke({
            "pergunta": estado["pergunta"],
            "colunas": colunas_disponiveis,
            "dados_crus": dados[:5]
        })
        
        lista_graficos = [g.model_dump() for g in resultado.graficos if g.tipo]
        
        print(f"    ↳ {len(lista_graficos)} gráfico(s) planejado(s).")
        return {"config_grafico": lista_graficos}
        
    except Exception as e:
        print(f"    ⚠️ Falha ao estruturar os gráficos: {e}")
        return {"config_grafico": []}

def gerar_resposta_final(estado: EstadoAnalise) -> dict:
    """
    Nó 5: Interpreta os resultados do banco de dados e monta o relatório final auditável.
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

    if not dados_crus:
        return {
            "dados_encontrados": False,
            "resposta_final": "A consulta foi executada com sucesso, mas nenhum registro correspondente foi encontrado na base de dados com os filtros aplicados."
        }
    

    modelo_analista = instanciar_modelo_analista()
    
    # Cadeia LCEL para a análise
    cadeia_analise = PROMPT_ANALISE_DADOS | modelo_analista | parser
    
    texto_interpretacao = cadeia_analise.invoke({
        "pergunta": pergunta,
        "dados": str(dados_crus)
    })

    # templates evitam inconsistêNcias na formatação
    template_relatorio = textwrap.dedent("""
    ### 📊 Análise
    {analise}

    ---
    ### 🔎 Evidências e Transparência

    **SQL Utilizado:**
    ```sql
    {sql}
    ```

    **Amostra dos Dados Utilizados:**
    ```python
    {dados}
    ```
    """).strip()
    

    relatorio_final = template_relatorio.format(
        analise=texto_interpretacao.strip(),
        sql=sql_utilizado.strip(),
        dados=dados_crus[:5]
    )

    print("✅ Relatório final gerado com sucesso.")
    return {"resposta_final": relatorio_final}