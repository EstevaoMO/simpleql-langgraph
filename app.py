import streamlit as st
import pandas as pd
import os
import re
import time
from src.grafo import agente_simplesql

st.set_page_config(
    page_title="SimplesQL",
    page_icon=":bar_chart:",
    layout="wide"
)

# ---------------------------------------------------------------------------
# THEME / CSS
# ---------------------------------------------------------------------------
PRIMARY = "#4169E1"
PRIMARY_DARK = "#2F4FBF"
PRIMARY_SOFT = "#EEF1FD"
INK = "#1A1D29"
MUTED = "#6B7280"

st.markdown(f"""
    <style>
    #MainMenu, footer {{visibility: hidden;}}

    /* ================================================================
       Tema fixo e explícito (claro), independente da config do usuário.
       Evita texto invisível quando o Streamlit mistura tema claro/escuro.
       ================================================================ */

    .stApp {{
        background-color: #FAFBFF;
    }}

    /* ---------- textos gerais: forçar tinta escura sempre ---------- */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {{
        color: {INK};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {INK} !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }}

    /* ---------- sidebar: fundo branco, texto escuro forçado ---------- */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 1px solid #E7E9F5;
    }}
    section[data-testid="stSidebar"] * {{
        color: {INK} !important;
    }}
    section[data-testid="stSidebar"] a {{
        color: {PRIMARY} !important;
    }}

    /* ---------- hero header block ---------- */
    .simplesql-hero {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(65, 105, 225, 0.25);
    }}
    .simplesql-hero h1, .simplesql-hero h1 * {{
        color: #FFFFFF !important;
        font-weight: 800 !important;
        margin: 0 0 6px 0;
        font-size: 2rem !important;
    }}
    .simplesql-hero p, .simplesql-hero p * {{
        color: rgba(255,255,255,0.92) !important;
        margin: 0;
        font-size: 1rem;
    }}

    /* ---------- markdown output do agente (dentro do card de resposta) ---------- */
    .simplesql-resposta h1, .simplesql-resposta h2, .simplesql-resposta h3,
    .simplesql-resposta h4, .simplesql-resposta h5, .simplesql-resposta h6 {{
        color: {PRIMARY_DARK} !important;
        margin-top: 0.6em;
        margin-bottom: 0.4em;
    }}
    .simplesql-resposta p, .simplesql-resposta li {{
        color: {INK} !important;
        line-height: 1.6;
    }}
    .simplesql-resposta table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.8em 0;
    }}
    .simplesql-resposta th {{
        background-color: {PRIMARY_SOFT};
        color: {PRIMARY_DARK} !important;
        font-weight: 700;
        text-align: left;
        padding: 8px 12px;
        border-bottom: 2px solid {PRIMARY};
    }}
    .simplesql-resposta td {{
        padding: 8px 12px;
        border-bottom: 1px solid #EDEFF7;
        color: {INK} !important;
    }}
    .simplesql-resposta code {{
        background-color: {PRIMARY_SOFT};
        color: {PRIMARY_DARK} !important;
        padding: 2px 6px;
        border-radius: 4px;
    }}
    .simplesql-resposta blockquote {{
        border-left: 3px solid {PRIMARY};
        margin: 0.6em 0;
        padding-left: 12px;
        color: {MUTED} !important;
    }}

    /* ---------- suggestion buttons (outline style) ---------- */
    .stButton>button {{
        border: 1.5px solid {PRIMARY} !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        font-weight: 500 !important;
        padding: 0.55em 1em !important;
        transition: all 0.15s ease-in-out;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .stButton>button, .stButton>button * {{
        color: {PRIMARY} !important;
    }}
    .stButton>button:hover {{
        background-color: {PRIMARY} !important;
        border-color: {PRIMARY} !important;
    }}
    .stButton>button:hover, .stButton>button:hover * {{
        color: #FFFFFF !important;
    }}

    /* primary CTA button — sempre fundo azul solido + texto branco */
    .stButton>button[kind="primary"] {{
        background-color: {PRIMARY} !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.65em 1.4em !important;
    }}
    .stButton>button[kind="primary"], .stButton>button[kind="primary"] * {{
        color: #FFFFFF !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: {PRIMARY_DARK} !important;
    }}

    /* ---------- text input: fundo branco, texto escuro, placeholder cinza ---------- */
    .stTextInput>div>div {{
        background-color: #FFFFFF !important;
    }}
    .stTextInput>div>div>input {{
        background-color: #FFFFFF !important;
        color: {INK} !important;
        border-radius: 10px !important;
        border: 1.5px solid #D7DAEB !important;
        padding: 0.7em 1em !important;
    }}
    .stTextInput>div>div>input::placeholder {{
        color: {MUTED} !important;
        opacity: 1;
    }}
    .stTextInput>div>div>input:focus {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(65, 105, 225, 0.15);
    }}

    /* ---------- spinner / status ---------- */
    div.stSpinner > div > div {{
        border-top-color: {PRIMARY} !important;
    }}
    div[data-testid="stStatusWidget"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #E7E9F5 !important;
        border-radius: 10px !important;
    }}

    /* ---------- response card ---------- */
    .simplesql-resposta {{
        background: #FFFFFF;
        color: {INK};
        border: 1px solid #E7E9F5;
        border-left: 4px solid {PRIMARY};
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 18px;
        box-shadow: 0 2px 10px rgba(20, 20, 50, 0.05);
    }}
    .simplesql-resposta * {{
        color: {INK} !important;
    }}

    /* ---------- dataframe / metric cards ---------- */
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid #E7E9F5;
        border-radius: 10px;
        padding: 12px 16px;
    }}
    div[data-testid="stMetric"] * {{
        color: {INK} !important;
    }}

    /* ---------- badges / suggestion label ---------- */
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

# ---------------------------------------------------------------------------
# Mensagens dinâmicas de progresso, mapeadas por nó do LangGraph.
# Ajuste as chaves para bater com os nomes reais dos nós em src/grafo.py
# ---------------------------------------------------------------------------
MENSAGENS_POR_NO = {
    "planejar_query": "🧠 Interpretando sua pergunta e planejando a consulta SQL...",
    "gerar_sql": "🧠 Interpretando sua pergunta e planejando a consulta SQL...",
    "validar_sql": "🔍 Validando a sintaxe da query gerada...",
    "executar_sql": "⚙️ Executando a consulta no banco de dados...",
    "corrigir_sql": "🛠️ Ajustando a query após um erro de execução...",
    "gerar_resposta": "✍️ Elaborando o relatório final com os resultados...",
    "elaborar_resposta": "✍️ Elaborando o relatório final com os resultados...",
}

MENSAGEM_PADRAO_SEQUENCIA = [
    "🧠 Interpretando sua pergunta...",
    "🗂️ Planejando a consulta SQL...",
    "⚙️ Executando no banco de dados...",
    "✍️ Elaborando o relatório final...",
]


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
    """
    Executa o grafo do agente exibindo o progresso em tempo real.
    Tenta usar agente_simplesql.stream() para refletir o nó atual do
    LangGraph; se o streaming não estiver disponível, cai para uma
    sequência simulada de mensagens (evita travar a experiência).
    """
    resultado_final = None

    with st.status("Iniciando análise...", expanded=True) as status:
        try:
            for evento in agente_simplesql.stream(
                estado_inicial,
                {"recursion_limit": 10}
            ):
                for nome_no, valor_no in evento.items():
                    mensagem = MENSAGENS_POR_NO.get(
                        nome_no, f"⚙️ Processando etapa: {nome_no}..."
                    )
                    status.update(label=mensagem, state="running")
                    st.write(mensagem)
                    if isinstance(valor_no, dict):
                        resultado_final = valor_no if resultado_final is None else {**resultado_final, **valor_no}
                    else:
                        resultado_final = valor_no

            status.update(label="Análise concluída!", state="complete")

        except AttributeError:
            # fallback: o grafo compilado não expõe .stream()
            for msg in MENSAGEM_PADRAO_SEQUENCIA:
                status.update(label=msg, state="running")
                st.write(msg)
                time.sleep(0.5)
            resultado_final = agente_simplesql.invoke(
                estado_inicial, {"recursion_limit": 10}
            )
            status.update(label="Análise concluída!", state="complete")

    return resultado_final


def renderizar_inicio():
    """Renderiza a página principal de consultas do agente."""
    st.markdown("""
        <div class="simplesql-hero">
            <h1>📊 Consulta de Dados em Linguagem Natural</h1>
            <p>Faça uma pergunta sobre a base de vendas de jogos. O SimplesQL irá analisar e responder estruturalmente.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="simplesql-label">Sugestões de perguntas</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    # botões de sugestão de perguntas
    if 'pergunta_atual' not in st.session_state:
        st.session_state.pergunta_atual = ""

    if col1.button("🏆 10 jogos mais vendidos globalmente", use_container_width=True):
        st.session_state.pergunta_atual = "Quais foram os 10 jogos mais vendidos globalmente?"
    if col2.button("🇯🇵 Gênero com maior venda no Japão", use_container_width=True):
        st.session_state.pergunta_atual = "Qual gênero possui a maior média de vendas no Japão?"
    if col3.button("⚔️ Comparar Action vs Sports", use_container_width=True):
        st.session_state.pergunta_atual = "Como as vendas globais de jogos de ação se comparam às de jogos de esporte?"

    st.markdown("<br>", unsafe_allow_html=True)
    pergunta = st.text_input("Sua pergunta:", value=st.session_state.pergunta_atual, placeholder="Ex: Quais plataformas mais venderam na Europa?")

    executar = st.button("Executar Análise", type="primary")

    if executar:
        if pergunta.strip():
            estado_inicial = {
                "pergunta": pergunta,
                "consulta_sql": "",
                "sql_valido": False,
                "resultado_consulta": [],
                "resposta_final": "",
                "erro": None,
                "tentativas_correcao": 0
            }

            try:
                resultado = executar_agente_com_status(estado_inicial)

                # Abre a div estilizada, deixa o st.markdown nativo processar
                # o conteúdo (negrito, tabelas, listas etc.) e fecha a div.
                # Renderizar o markdown direto dentro de uma f-string HTML
                # faz o Streamlit tratar tudo como texto literal e perder
                # a formatação — por isso os três blocos separados abaixo.
                st.markdown('<div class="simplesql-resposta">', unsafe_allow_html=True)
                st.markdown(limpar_indentacao_markdown(resultado["resposta_final"]))
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro na execução do agente: {str(e)}")
        else:
            st.warning("Insira uma pergunta para continuar.")


def renderizar_base():
    """Renderiza a página de auditoria da base de dados bruta."""
    st.markdown("""
        <div class="simplesql-hero">
            <h1>🗃️ Base de Dados Bruta</h1>
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
    """Função principal que gerencia a barra lateral e o roteamento da aplicação."""
    with st.sidebar:
        # Logo
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("## 📊 SimplesQL")

        st.markdown("---")

        # Menu de Navegação
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