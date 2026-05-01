# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Evasão EaD | TCC Univesp",
    page_icon="🎓",
    layout="wide"
)

COR_2023, COR_2024 = "#2E86AB", "#E84855"
COR_COM, COR_SEM   = "#3BB273", "#F4A259"

@st.cache_data
def load(nome):
    return pd.read_csv(f"streamlit_data/{nome}.csv")

# Cabeçalho
st.title("🎓 Evasão no Ensino Superior a Distância no Brasil")
st.caption("TCC — Ciência de Dados | Univesp 2026 · Fonte: Censo INEP 2023-2024")
st.divider()

# KPIs
kpi = load("kpi")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cursos EaD 2023", f"{kpi[kpi.ano==2023]['n_cursos'].values[0]:,.0f}")
c2.metric("Cursos EaD 2024", f"{kpi[kpi.ano==2024]['n_cursos'].values[0]:,.0f}")
t23 = kpi[kpi.ano==2023]['taxa_media'].values[0]
t24 = kpi[kpi.ano==2024]['taxa_media'].values[0]
c3.metric("Taxa Média 2023", f"{t23:.1%}")
c4.metric("Taxa Média 2024", f"{t24:.1%}", delta=f"{t24-t23:+.1%}")

st.divider()

tabs = st.tabs(["🏫 Rede", "🗺️ Região", "🏛️ Organização",
                "💰 Apoio Financeiro", "👤 Sexo", "📊 Distribuição"])

def bar_chart(df, x, y, title, ylim=0.65):
    fig = px.bar(df, x=x, y=y, color="ano", barmode="group",
                 color_discrete_map={2023: COR_2023, 2024: COR_2024},
                 text=df[y].map(lambda v: f"{v:.1%}"),
                 title=title,
                 labels={y: "Taxa Média de Evasão", "ano": "Ano"})
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, ylim],
                      plot_bgcolor="white", paper_bgcolor="#fafafa")
    return fig

with tabs[0]:
    df = load("rede")
    st.plotly_chart(bar_chart(df, "Rede", "taxa_media",
                    "Evasão por Rede de Ensino"), use_container_width=True)

with tabs[1]:
    df = load("regiao")
    st.plotly_chart(bar_chart(df, "Região", "taxa_media",
                    "Evasão por Região"), use_container_width=True)

with tabs[2]:
    df = load("org")
    st.plotly_chart(bar_chart(df, "Organização", "taxa_media",
                    "Evasão por Organização Acadêmica", ylim=0.75),
                    use_container_width=True)

with tabs[3]:
    df = load("apoio")
    fig = px.bar(df, x="Programa", y="taxa_media", color="Situação",
                 facet_col="ano", barmode="group",
                 color_discrete_map={"Com apoio": COR_COM, "Sem apoio": COR_SEM},
                 text=df["taxa_media"].map(lambda v: f"{v:.1%}"),
                 title="Evasão por Apoio Financeiro")
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 0.70],
                      plot_bgcolor="white", paper_bgcolor="#fafafa")
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    try:
        df = load("sexo")
        st.plotly_chart(bar_chart(df, "PREDOM_SEXO", "taxa_media",
                        "Evasão por Predominância de Sexo"),
                        use_container_width=True)
    except Exception:
        st.info("Variável PREDOM_SEXO não disponível nos dados.")

with tabs[5]:
    df = load("distribuicao")
    fig = go.Figure()
    for ano, cor in [(2023, COR_2023), (2024, COR_2024)]:
        vals = df[df["ano"] == ano]["TAXA_EVASAO"]
        fig.add_trace(go.Violin(y=vals, name=str(ano), box_visible=True,
                                meanline_visible=True, fillcolor=cor,
                                opacity=0.65, line_color=cor, points=False))
    fig.update_layout(title="Distribuição da Taxa de Evasão",
                      yaxis_tickformat=".0%",
                      plot_bgcolor="white", paper_bgcolor="#fafafa")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Uma Investigação sobre os Fatores da Evasão no Ensino Superior a Distância no Brasil · Univesp 2026")
