import streamlit as st
import pandas as pd
import os
import re
import ast
import json
import time
from src.grafo import agente_simplesql

st.set_page_config(
    page_title="SimplesQL",
    page_icon="./favicon.png",
    layout="wide"
)

# css
PRIMARY = "#4169E1"
PRIMARY_DARK = "#2F4FBF"

st.markdown(f"""
    <style>
    /* Ocultar barra superior, menu e rodapé */
    #MainMenu, footer, header {{visibility: hidden;}}

    /* Fundo da aplicação */
    .stApp {{
        background-color: #FAFBFF;
    }}

    /* ---------- Hero Block ---------- */
    .simplesql-hero {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(65, 105, 225, 0.25);
    }}
    .simplesql-hero h1, .simplesql-hero p {{
        color: #FFFFFF !important;
        margin: 0;
    }}
    .simplesql-hero h1 {{
        font-weight: 800 !important;
        margin-bottom: 6px;
    }}

    /* ---------- Response Card ---------- */
    .simplesql-resposta {{
        background: #FFFFFF;
        border: 1px solid #E7E9F5;
        border-left: 4px solid {PRIMARY};
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 18px;
        box-shadow: 0 2px 10px rgba(20, 20, 50, 0.05);
        color: #1A1D29;
    }}

    /* ---------- Botões ---------- */
    .stButton>button {{
        border: 1.5px solid {PRIMARY} !important;
        border-radius: 10px !important;
        color: {PRIMARY} !important;
        background-color: #FFFFFF !important;
        transition: all 0.15s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: {PRIMARY} !important;
        color: #FFFFFF !important;
    }}
    .stButton>button[kind="primary"] {{
        background-color: {PRIMARY} !important;
        color: #FFFFFF !important;
        border: none !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: {PRIMARY_DARK} !important;
    }}

    /* ---------- Spinner / Status ---------- */
    div.stSpinner > div > div {{
        border-top-color: {PRIMARY} !important;
    }}
    
    .simplesql-label {{
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: {PRIMARY} !important;
        margin-bottom: 6px;
    }}
    </style>
""", unsafe_allow_html=True)

# Dicionários e Funções Auxiliares
MENSAGENS_POR_NO = {
    "alinhar_entidades": "Identificando entidades e termos relevantes na pergunta...",
    "gerar_sql": "Interpretando sua pergunta e planejando a consulta SQL...",
    "validar_sql": "Validando a sintaxe da query gerada...",
    "executar_sql": "Executando a consulta no banco de dados...",
    "corrigir_sql": "Ajustando a query após um erro de execução...",
    "gerar_resposta": "Elaborando o relatório final com os resultados...",
}

MENSAGEM_PADRAO_SEQUENCIA = [
    "🧠 Interpretando sua pergunta...",
    "🗂️ Planejando a consulta SQL...",
    "⚙️ Executando no banco de dados...",
    "✍️ Elaborando o relatório final...",
]

# def formatar_amostras_de_dados(texto: str) -> str:
#     """Garante que listas de dicionários sejam renderizadas como blocos JSON."""
#     if not texto: return texto
#     linhas = texto.split("\n")
#     saida = []
#     padrao = re.compile(r"^\[\s*\{.*\}\s*\]$")

#     for linha in linhas:
#         if padrao.match(linha.strip()):
#             try:
#                 dados = ast.literal_eval(linha.strip())
#                 saida.append("```json\n" + json.dumps(dados, indent=2, ensure_ascii=False, default=str) + "\n```")
#                 continue
#             except:
#                 pass
#         saida.append(linha)
#     return "\n".join(saida)

 
def limpar_indentacao_markdown(texto: str) -> str:
    """
    Remove espaços de indentação no início das linhas que fazem o Streamlit
    (markdown) interpretar erroneamente trechos como bloco de código
    (4+ espaços de indentação = code block em markdown).
 
    Isso normalmente acontece quando a string de resposta é montada dentro
    de um bloco de código Python já indentado (ex: dentro de uma função),
    preservando a indentação do próprio código-fonte.
    """
    if not texto:
        return texto
 
    linhas = texto.split("\n")
    dentro_de_bloco_codigo = False
    linhas_limpas = []
 
    for linha in linhas:
        marcador_fence = re.match(r"^\s*```", linha)
        if marcador_fence:
            dentro_de_bloco_codigo = not dentro_de_bloco_codigo
            linhas_limpas.append(linha.strip())
            continue
 
        if dentro_de_bloco_codigo:
            # dentro de bloco de código real: só remove a indentação "externa"
            linhas_limpas.append(linha.lstrip() if linha.strip() else linha)
        else:
            linhas_limpas.append(linha.lstrip())
 
    return "\n".join(linhas_limpas)


def executar_agente_com_status(estado_inicial):
    """Executa o grafo do agente exibindo o progresso em tempo real."""
    resultado_final = None
    with st.status("Iniciando análise...", expanded=True) as status:
        try:
            for evento in agente_simplesql.stream(estado_inicial, {"recursion_limit": 10}):
                for nome_no, valor_no in evento.items():
                    mensagem = MENSAGENS_POR_NO.get(nome_no, f"⚙️ Processando: {nome_no}...")
                    status.update(label=mensagem, state="running")
                    if isinstance(valor_no, dict):
                        resultado_final = valor_no if resultado_final is None else {**resultado_final, **valor_no}
                    else:
                        resultado_final = valor_no
            status.update(label="Análise concluída!", state="complete")
        except AttributeError:
            for msg in MENSAGEM_PADRAO_SEQUENCIA:
                status.update(label=msg, state="running")
                time.sleep(0.5)
            resultado_final = agente_simplesql.invoke(estado_inicial, {"recursion_limit": 10})
            status.update(label="Análise concluída!", state="complete")
    return resultado_final

def renderizar_inicio():
    st.markdown("""
        <div class="simplesql-hero">
            <h1>Agente consultor de dados</h1>
            <p>Faça uma pergunta em linguagem natural sobre a base de vendas de jogos. O <strong>SimplesQL</strong> irá analisar e responder estruturalmente, de forma a minimizar alucinações e erros.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="simplesql-label">Sugestões de perguntas</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    if 'pergunta_atual' not in st.session_state:
        st.session_state.pergunta_atual = ""

    if col1.button("🏆 10 jogos mais vendidos globalmente", use_container_width=True):
        st.session_state.pergunta_atual = "Quais foram os 10 jogos mais vendidos globalmente?"
    if col2.button("🇯🇵 Gênero com maior venda no Japão", use_container_width=True):
        st.session_state.pergunta_atual = "Qual gênero possui a maior média de vendas no Japão?"
    if col3.button("⚔️ Comparar Action vs Sports", use_container_width=True):
        st.session_state.pergunta_atual = "Como as vendas globais de jogos de ação se comparam às de jogos de esporte?"

    pergunta = st.text_input("Sua pergunta:", value=st.session_state.pergunta_atual, placeholder="Ex: Quais plataformas mais venderam na Europa?")

    if st.button("Executar Análise", type="primary"):
        if pergunta.strip():
            estado_inicial = {
                "pergunta": pergunta,
                "dicas_entidades": "",
                "consulta_sql": "",
                "sql_valido": False,
                "resultado_consulta": [],
                "resposta_final": "",
                "erro": None,
                "tentativas_correcao": 0,
                "dados_encontrados": True
            }
            try:
                resultado = executar_agente_com_status(estado_inicial)
                
                if resultado.get("dados_encontrados", True):
                    st.markdown('<div class="simplesql-resposta">', unsafe_allow_html=True)
                    st.markdown(resultado.get("resposta_final", ""))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("**Nenhum dado encontrado**", icon="ℹ️")
                    st.markdown(f"> {resultado.get('resposta_final', '')}")
                    
            except Exception as e: # caso crítico
                st.error("Tente novamente, não foi possível processar sua query :/", icon="🚨")
                st.markdown(f"""
                        ```bash
                        [ERRO DE EXECUÇÃO]
                        {str(e)}""")

def renderizar_base():
    st.markdown("""
        <div class="simplesql-hero">
            <h1>Base de dados bruta</h1>
            <p>Visualize o dataset completo utilizado para embasar as análises e consultas geradas.</p>
        </div>
    """, unsafe_allow_html=True)

    caminho_csv = "db/vgsales.csv"
    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de registros", f"{len(df):,}".replace(",", "."))
        if "Platform" in df.columns:
            c2.metric("Plataformas únicas", df["Platform"].nunique())
        if "Genre" in df.columns:
            c3.metric("Gêneros únicos", df["Genre"].nunique())
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error(f"Arquivo não encontrado em: {caminho_csv}. Verifique o diretório.")

def main():
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("## 📊 SimplesQL")
        
        st.markdown("---")
        pagina = st.radio("Navegação", ["Início", "Base de Dados"])
        st.markdown("---")
        st.markdown("### Créditos e Fontes")
        st.markdown("[Kaggle: Video Game Sales](https://www.kaggle.com/datasets/gregorut/videogamesales)")

    if pagina == "Início":
        renderizar_inicio()
    elif pagina == "Base de Dados":
        renderizar_base()

if __name__ == "__main__":
    main()