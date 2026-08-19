## PROJETO: Detalhes Técnicos

<p align="center">
	<img src="logo.png" alt="SimplesQL logo" width="420" />
</p>

## Visão geral
Este documento descreve a arquitetura, os componentes, as dependências e as decisões técnicas do projeto SimplesQL. O objetivo é fornecer contexto suficiente para desenvolvedores que queiram entender, estender ou implantar o sistema.

## Arquitetura
- Orquestração baseada em grafo: o fluxo de análise é modelado por um grafo de estados (`src/grafo.py`) usando `langgraph`. Cada nó do grafo é uma função que recebe e retorna partes do `EstadoAnalise`.
- Extração de entidades: extrai da pergunta do usuário com fuzzy match & interpretação de LLMs as melhores correspondências de entidades no banco (ex.: x360 ≈ Xbox360).
- Geração de SQL: um modelo especializado (instanciado em `src/modelos.py`) recebe um prompt (`src/prompts.py`) e retorna apenas uma string SQL.
- Validação: o nó de validação (`src/nos.py`) rejeita consultas que contenham comandos destrutivos (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE TABLE).
- Execução: as queries válidas são executadas em DuckDB contra um CSV local (`db/vgsales.csv`) montado como view em memória.
- Interpretação: um modelo analista interpreta o resultado e gera um relatório formatado e auditável.

## Principais módulos
- `src/grafo.py`: monta e compila o `StateGraph`, define rotas condicionais e cria a instância do agente.
- `src/nos.py`: implementa os nós do pipeline — gerar SQL, validar, executar no DuckDB e gerar a resposta final.
- `src/modelos.py`: carregamento das credenciais (`dotenv`) e construção de instâncias `ChatOpenAI` para os papéis de `modelo_sql` e `modelo_analista`.
- `src/prompts.py`: contém `ChatPromptTemplate` com instruções rígidas para geração de SQL e interpretação de dados.
- `src/estado.py`: definição de `EstadoAnalise` (TypedDict) que padroniza o estado trocado entre os nós.

## Exigências e variáveis de ambiente
- Python 3.10+ recomendado.
- Variáveis:
  - `OPENROUTER_API_KEY`: chave usada pelos adaptadores `langchain_openai` (definida por `dotenv` ou variáveis de ambiente).

## Como rodar localmente
1. Crie e ative um virtualenv.
2. Instale as dependências mínimas:

```
pip install -r requirements.txt
```

3. Defina a variável de ambiente `OPENROUTER_API_KEY` (ou crie um `.env`).
4. Rode os scripts de teste/simulação em `testes/`:

```
python testes/teste_fluxo_completo.py
```

## Observações de segurança e auditoria
- O projeto já implementa uma camada de validação simples contra comandos destrutivos. Em produção, recomendo:
  - Lista branca de colunas/alias aceitos.
  - Timeouts/limites de resultados do DuckDB.
  - Logs estruturados de cada passo (entrada do LLM, SQL gerado, output do DB, relatório final).

## Testes
- Há scripts de teste em `testes/` que simulam o fluxo e validam a integração entre módulos. Eles são executáveis como scripts independentes (não dependem de `pytest`, mas podem ser adaptados para ele).

## Contato e contribuição
- Abra issues para discutir mudanças e PRs para enviar contribuições. Siga o estilo e a estrutura já existente em `src/`.
