# SimplesQL: Assistente SQL com LangGraph

<p align="center">
	<img src="logo-bg.png" alt="SimplesQL logo" width="420" />
</p>

Uma ferramenta minimalista que traduz linguagem natural em consultas SQL seguras, executa-as sobre um dataset CSV com DuckDB e gera um relatório interpretável e auditável usando modelos de linguagem.

## Demo
Acesse o projeto em: [https://simpleql.streamlit.app/](https://simpleql.streamlit.app/)

## Objetivo do projeto
- Provar um fluxo prático e auditável que combina geração de SQL por LLMs, validação de segurança e execução em DuckDB.
- Demonstrar orquestração baseada em grafos de estado (LangGraph) para pipelines de análise de dados.
- Explorar capacidade de criação de fluxos inteligentes com a ferramenta LangGraph.

## Principais conceitos
- Tradução controlada: o LLM gera apenas a consulta SQL, orientada por prompts e regras rígidas.
- Validação de segurança: o sistema detecta e bloqueia comandos destrutivos antes da execução.
- Execução reprodutível: a consulta roda em DuckDB sobre um CSV local, preservando auditabilidade.

## Tecnologias e componentes
- Linguagem: Python (scripts em `/src/`).
- Orquestração: `langgraph` para definir o grafo de estados e transições.
- LLMs: adaptadores em `langchain_core` e `langchain_openai` via OpenRouter (variável de ambiente `OPENROUTER_API_KEY`).
- Banco in-memory: `duckdb` para carregar `db/vgsales.csv` e executar consultas SQL.
- Configuração: `python-dotenv` para variáveis sensíveis

## Começando (rápido)
1. Crie um ambiente Python e ative-o (recomendado: 3.10+).
2. Instale dependências (exemplo):

```
pip install python-dotenv langchain-core langchain-openai langgraph duckdb
```

3. Crie um .env com a chave do OpenRouter:

```
OPENROUTER_API_KEY="sua_chave_aqui"
```

4. Rode um teste rápido do fluxo completo:

```
python testes/teste_fluxo_completo.py
```

## Documentação técnica
- Para detalhes sobre arquitetura, módulos, fluxos e dependências recomendadas, veja [`PROJETO.md`](https://github.com/EstevaoMO/simpleql-langgraph/blob/main/PROJETO.md).

## Contribuições
- Bug reports, melhorias de prompts e ajustes de segurança são bem-vindos. Abra uma issue ou um PR.

## Base de dados
- A base de dados utilizada para o projeto pode ser encontrada em: [https://www.kaggle.com/datasets/gregorut/videogamesales](https://www.kaggle.com/datasets/gregorut/videogamesales)
