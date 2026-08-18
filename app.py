import streamlit as st
import pandas as pd
import os
from src.grafo import agente_simplesql

st.set_page_config(
    page_title="SimplesQL",
    page_icon=":bar_chart:",
    layout="wide"
)

# css
st.markdown("""
    <style>
    .stButton>button {
        border: 1px solid #4169E1;
        color: #4169E1;
        border-radius: 6px;
        background-color: transparent;
    }
    .stButton>button:hover {
        background-color: #4169E1;
        color: white;
    }
    div.stSpinner > div > div {
        border-top-color: #4169E1 !important;
    }
    </style>
""", unsafe_allow_html=True)

def renderizar_inicio():
    """Renderiza a página principal de consultas do agente."""
    st.title("Consulta de Dados em Linguagem Natural")
    st.markdown("Faça uma pergunta sobre a base de vendas de jogos. O SimplesQL irá analisar e responder estruturalmente.")

    st.markdown("#### Sugestões de perguntas")
    col1, col2, col3 = st.columns(3)
    
    # botoões de sugestão de perguntas
    if 'pergunta_atual' not in st.session_state:
        st.session_state.pergunta_atual = ""

    if col1.button("10 jogos mais vendidos globalmente"):
        st.session_state.pergunta_atual = "Quais foram os 10 jogos mais vendidos globalmente?"
    if col2.button("Gênero com maior venda no Japão"):
        st.session_state.pergunta_atual = "Qual gênero possui a maior média de vendas no Japão?"
    if col3.button("Comparar Action vs Sports"):
        st.session_state.pergunta_atual = "Como as vendas globais de jogos de ação se comparam às de jogos de esporte?"

    pergunta = st.text_input("Sua pergunta:", value=st.session_state.pergunta_atual)

    if st.button("Executar Análise", type="primary"):
        if pergunta.strip():
            with st.spinner("Planejando query, executando no banco e elaborando relatório..."):
                # prancheta inicial
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
                    resultado = agente_simplesql.invoke(
                        estado_inicial, 
                        {"recursion_limit": 10} # previne loops de auto-correção, apenas redundância para segurança
                    )
                    
                    st.markdown("---")
                    st.markdown(resultado["resposta_final"])
                except Exception as e:
                    st.error(f"Erro na execução do agente: {str(e)}")
        else:
            st.warning("Insira uma pergunta para continuar.")

def renderizar_base():
    """Renderiza a página de auditoria da base de dados bruta."""
    st.title("Base de Dados Bruta")
    st.markdown("Visualize o dataset completo utilizado para embasar as análises e consultas geradas.")
    
    caminho_csv = "db/vgsales.csv"
    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
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
            st.markdown("## SimplesQL")
            
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