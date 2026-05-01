import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pickle, os

# --- Configuração da página ---
st.set_page_config(
    page_title="Evasão EaD | TCC Univesp",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilo customizado ---
st.markdown("""
<style>
    .main { background-color: #fafafa; }
    .block-container { padding-top: 2rem; }
    h1 { color: #1a1a2e; font-family: Inter, sans-serif; }
    h2, h3 { color: #2E86AB; }
    .stMetric { background: white; border-radius: 8px;
                padding: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
</style>
""", unsafe_allow_html=True)

COR_2023, COR_2024 = "#2E86AB", "#E84855"
COR_PUBLICA, COR_PRIVADA = "#3BB273", "#F4A259"

# --- Carregar dados salvos pelo notebook ---
# Os dados precisam ter sido salvos em parquet pelo notebook principal.
# Adicione ao seu notebook (após os merges):
#
#   df_completo_2023[features + ["TAXA_EVASAO"]].to_parquet("ead_2023.parquet")
#   df_completo_2024[features + ["TAXA_EVASAO"]].to_parquet("ead_2024.parquet")

@st.cache_data
def carregar_dados():
    df23 = pd.read_parquet("ead_2023.parquet")
    df24 = pd.read_parquet("ead_2024.parquet")
    return df23, df24

try:
    df23, df24 = carregar_dados()
    dados_ok = True
except Exception as e:
    st.error(f"Dados não encontrados. Salve os parquets no notebook primeiro. Erro: {e}")
    dados_ok = False

if not dados_ok:
    st.stop()

# --- Sidebar ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Logo_Univesp.svg/320px-Logo_Univesp.svg.png",
                 width=160)
st.sidebar.title("Filtros")
anos = st.sidebar.multiselect("Anos", ["2023", "2024"], default=["2023", "2024"])
df_sel = {
    "2023": df23 if "2023" in anos else None,
    "2024": df24 if "2024" in anos else None,
}

# --- Cabeçalho ---
st.title("🎓 Evasão no Ensino Superior a Distância no Brasil")
st.markdown("**TCC — Ciência de Dados | Univesp 2026** · Dados: Censo INEP 2023-2024")
st.divider()

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cursos EaD 2023", f"{len(df23):,.0f}")
col2.metric("Cursos EaD 2024", f"{len(df24):,.0f}")
col3.metric("Taxa Média 2023", f"{df23['TAXA_EVASAO'].mean():.1%}")
col4.metric("Taxa Média 2024", f"{df24['TAXA_EVASAO'].mean():.1%}",
            delta=f"{(df24['TAXA_EVASAO'].mean() - df23['TAXA_EVASAO'].mean()):.1%}")

st.divider()

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏫 Rede de Ensino", "🗺️ Região", "🏛️ Org. Acadêmica",
    "💰 Apoio Financeiro", "👤 Perfil Demográfico"
])

# TAB 1 — Rede
with tab1:
    st.subheader("Evasão por Rede de Ensino (Pública vs Privada)")
    rows = []
    for ano, df in [("2023", df23), ("2024", df24)]:
        if df is not None:
            for cod, label in [(1, "Pública"), (2, "Privada")]:
                taxa = df[df["TP_REDE_y"] == cod]["TAXA_EVASAO"].mean()
                rows.append({"Rede": label, "Ano": ano, "Taxa": taxa})
    df_rede = pd.DataFrame(rows)
    fig = px.bar(df_rede, x="Rede", y="Taxa", color="Ano", barmode="group",
                 color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                 text=df_rede["Taxa"].map(lambda v: f"{v:.1%}"))
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.65],
                      plot_bgcolor="white", paper_bgcolor="#fafafa")
    st.plotly_chart(fig, use_container_width=True)

# TAB 2 — Região
with tab2:
    st.subheader("Evasão por Região")
    mapa_regiao = {1: "Norte", 2: "Nordeste", 3: "Centro-Oeste",
                   4: "Sudeste", 5: "Sul"}
    rows = []
    for ano, df in [("2023", df23), ("2024", df24)]:
        if df is not None and "CO_REGIAO" in df.columns:
            df = df.copy()
            df["Região"] = df["CO_REGIAO"].map(mapa_regiao)
            r = df.groupby("Região")["TAXA_EVASAO"].mean().reset_index()
            r["Ano"] = ano
            rows.append(r)
    if rows:
        df_reg = pd.concat(rows)
        fig = px.bar(df_reg, x="Região", y="TAXA_EVASAO", color="Ano",
                     barmode="group",
                     color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                     text=df_reg["TAXA_EVASAO"].map(lambda v: f"{v:.1%}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.65],
                          plot_bgcolor="white", paper_bgcolor="#fafafa")
        st.plotly_chart(fig, use_container_width=True)

# TAB 3 — Organização Acadêmica
with tab3:
    st.subheader("Evasão por Tipo de Organização Acadêmica")
    mapa_org = {1: "Universidade", 2: "Centro Univ.", 3: "Faculdade",
                4: "IF / CEFET", 5: "Univ. Especializada"}
    rows = []
    for ano, df in [("2023", df23), ("2024", df24)]:
        if df is not None:
            col = next((c for c in ["TP_ORGANIZACAO_ACADEMICA_x", "TP_ORGANIZACAO_ACADEMICA"]
                        if c in df.columns), None)
            if col:
                df = df.copy()
                df["Organização"] = df[col].map(mapa_org)
                r = df.dropna(subset=["Organização"]).groupby("Organização")["TAXA_EVASAO"].mean().reset_index()
                r["Ano"] = ano
                rows.append(r)
    if rows:
        df_org = pd.concat(rows)
        fig = px.bar(df_org, x="Organização", y="TAXA_EVASAO", color="Ano",
                     barmode="group",
                     color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                     text=df_org["TAXA_EVASAO"].map(lambda v: f"{v:.1%}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.75],
                          plot_bgcolor="white", paper_bgcolor="#fafafa")
        st.plotly_chart(fig, use_container_width=True)

# TAB 4 — Apoio Financeiro
with tab4:
    st.subheader("Evasão por Apoio Financeiro (FIES / ProUni)")
    rows = []
    for ano, df in [("2023", df23), ("2024", df24)]:
        if df is not None:
            for col_qt, label in [("QT_ING_FIES", "FIES"),
                                   ("QT_ING_PROUNI_PARCIAL", "ProUni")]:
                if col_qt in df.columns:
                    rows.append({"Programa": label, "Situação": "Com apoio",
                                 "Taxa": df[df[col_qt] > 0]["TAXA_EVASAO"].mean(), "Ano": ano})
                    rows.append({"Programa": label, "Situação": "Sem apoio",
                                 "Taxa": df[df[col_qt] == 0]["TAXA_EVASAO"].mean(), "Ano": ano})
    if rows:
        df_ap = pd.DataFrame(rows)
        fig = px.bar(df_ap, x="Programa", y="Taxa", color="Situação",
                     facet_col="Ano", barmode="group",
                     color_discrete_map={"Com apoio": COR_PUBLICA, "Sem apoio": COR_PRIVADA},
                     text=df_ap["Taxa"].map(lambda v: f"{v:.1%}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.70],
                          plot_bgcolor="white", paper_bgcolor="#fafafa")
        st.plotly_chart(fig, use_container_width=True)

# TAB 5 — Demográfico
with tab5:
    st.subheader("Evasão por Perfil Demográfico")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Por Predominância de Sexo**")
        rows = []
        for ano, df in [("2023", df23), ("2024", df24)]:
            if df is not None and "PREDOM_SEXO" in df.columns:
                r = df.groupby("PREDOM_SEXO")["TAXA_EVASAO"].mean().reset_index()
                r["Ano"] = ano
                rows.append(r)
        if rows:
            df_sexo = pd.concat(rows)
            fig = px.bar(df_sexo, x="PREDOM_SEXO", y="TAXA_EVASAO", color="Ano",
                         barmode="group",
                         color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                         text=df_sexo["TAXA_EVASAO"].map(lambda v: f"{v:.1%}"),
                         labels={"PREDOM_SEXO": "", "TAXA_EVASAO": "Taxa de Evasão"})
            fig.update_traces(textposition="outside")
            fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.65],
                              plot_bgcolor="white", paper_bgcolor="#fafafa", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Por Origem Escolar**")
        rows = []
        for ano, df in [("2023", df23), ("2024", df24)]:
            if df is not None and "PREDOM_ORIGEM" in df.columns:
                r = df.groupby("PREDOM_ORIGEM")["TAXA_EVASAO"].mean().reset_index()
                r["Ano"] = ano
                rows.append(r)
        if rows:
            df_orig = pd.concat(rows)
            fig = px.bar(df_orig, x="PREDOM_ORIGEM", y="TAXA_EVASAO", color="Ano",
                         barmode="group",
                         color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                         text=df_orig["TAXA_EVASAO"].map(lambda v: f"{v:.1%}"),
                         labels={"PREDOM_ORIGEM": "", "TAXA_EVASAO": "Taxa de Evasão"})
            fig.update_traces(textposition="outside")
            fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.65],
                              plot_bgcolor="white", paper_bgcolor="#fafafa", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("TCC — Uma Investigação sobre os Fatores da Evasão no Ensino Superior a Distância no Brasil · Univesp 2026")
