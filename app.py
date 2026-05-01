# app.py — TCC Evasão EaD | Univesp 2026 — v2
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Evasão EaD | TCC Univesp",
    page_icon="🎓",
    layout="wide"
)

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_2023 = "#2E86AB"
COR_2024 = "#E84855"
COR_COM  = "#3BB273"
COR_SEM  = "#F4A259"
BG       = "#fafafa"

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #fafafa; }
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }

    /* Card de KPI customizado */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 18px 20px 14px 20px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        height: 100%;
    }
    .kpi-label  { font-size: 12px; color: #888; font-weight: 600;
                  text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
    .kpi-value  { font-size: 28px; font-weight: 700; color: #1a1a2e; line-height: 1.1; }
    .kpi-delta-bad  { font-size: 13px; color: #E84855; font-weight: 600; margin-top: 3px; }
    .kpi-delta-good { font-size: 13px; color: #3BB273; font-weight: 600; margin-top: 3px; }
    .kpi-desc   { font-size: 11.5px; color: #999; margin-top: 6px; line-height: 1.4; }

    /* Caixa de premissas */
    .premissa-box {
        background: #fff8e1;
        border-left: 4px solid #F4A259;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 6px;
        font-size: 13.5px;
        color: #444;
        line-height: 1.6;
    }
    /* Rodapé de autores */
    .autores-box {
        background: white;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.07);
        font-size: 13px;
        color: #555;
        line-height: 1.8;
    }
    .autores-box h4 { color: #1a1a2e; margin-bottom: 8px; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# ── Carga de dados ─────────────────────────────────────────────────────────────
@st.cache_data
def load(nome):
    return pd.read_csv(f"streamlit_data/{nome}.csv")

kpi   = load("kpi")
rede  = load("rede")
reg   = load("regiao")
org   = load("org")
apoio = load("apoio")
dist  = load("distribuicao")
try:
    sexo = load("sexo")
    tem_sexo = True
except Exception:
    tem_sexo = False

n23 = int(kpi[kpi.ano == 2023]["n_cursos"].values[0])
n24 = int(kpi[kpi.ano == 2024]["n_cursos"].values[0])
t23 = float(kpi[kpi.ano == 2023]["taxa_media"].values[0])
t24 = float(kpi[kpi.ano == 2024]["taxa_media"].values[0])
delta = t24 - t23

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title("🎓 Evasão no Ensino Superior a Distância no Brasil")
st.caption("TCC — Ciência de Dados | Univesp 2026 · Fonte: Censo da Educação Superior — INEP 2023 e 2024")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Vínculos EaD — 2023</div>
        <div class="kpi-value">{n23:,.0f}</div>
        <div class="kpi-desc">
            Total de vínculos ativos em cursos superiores
            na modalidade EaD registrados no Censo INEP 2023.
        </div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Vínculos EaD — 2024</div>
        <div class="kpi-value">{n24:,.0f}</div>
        <div class="kpi-desc">
            Total de vínculos ativos em cursos superiores
            na modalidade EaD registrados no Censo INEP 2024.
        </div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Taxa Média de Evasão — 2023</div>
        <div class="kpi-value">{t23:.1%}</div>
        <div class="kpi-desc">
            <b>Cálculo:</b> Desvinculados ÷ Ingressantes, por curso.<br>
            Média entre todos os cursos EaD com ingressantes em 2023.
        </div>
    </div>""", unsafe_allow_html=True)

with c4:
    delta_class = "kpi-delta-bad" if delta > 0 else "kpi-delta-good"
    delta_sinal = f"▲ +{delta:.1%}" if delta > 0 else f"▼ {delta:.1%}"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Taxa Média de Evasão — 2024</div>
        <div class="kpi-value">{t24:.1%}</div>
        <div class="{delta_class}">{delta_sinal} em relação a 2023</div>
        <div class="kpi-desc">
            <b>Cálculo:</b> Desvinculados ÷ Ingressantes, por curso.<br>
            Média entre todos os cursos EaD com ingressantes em 2024.
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Premissas ─────────────────────────────────────────────────────────────────
with st.expander("⚠️ Premissas e definições dos dados — leia antes de interpretar", expanded=False):
    st.markdown("""
    <div class="premissa-box">
    <b>O que é a "taxa de evasão"?</b><br>
    Para cada curso, calculamos: <code>TAXA_EVASAO = QT_SIT_DESVINCULADO / QT_ING</code>.<br>
    O numerador (<b>QT_SIT_DESVINCULADO</b>) conta os alunos que se desvincularam do curso no ano —
    por abandono, desistência formal ou exclusão por norma institucional.<br>
    O denominador (<b>QT_ING</b>) é o total de ingressantes naquele curso no mesmo ano de referência.<br><br>

    <b>Unidade de análise</b><br>
    Os dados do Censo INEP são agregados por <b>curso × instituição</b>, não por aluno individual.
    Portanto, os valores representam taxas médias de evasão entre cursos — não a probabilidade
    de um aluno específico evadir.<br><br>

    <b>Recorte da base</b><br>
    Foram mantidos apenas cursos na modalidade <b>EaD</b> (educação a distância), com pelo menos
    1 ingressante e taxa de evasão entre 0% e 100%. Cursos com dados ausentes nessas variáveis
    foram excluídos.<br><br>

    <b>Sobre os totais (401 mil / 379 mil)</b><br>
    Esses números representam o total de <b>vínculos curso-IES</b> na base após o recorte EaD —
    não o número de alunos individuais nem de instituições. Uma mesma instituição aparece
    múltiplas vezes, uma entrada por curso oferecido.<br><br>

    <b>Fonte</b><br>
    Microdados do Censo da Educação Superior, INEP, anos-base 2023 e 2024.
    Acesso público em <a href="https://www.gov.br/inep" target="_blank">gov.br/inep</a>.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Função auxiliar para gráficos de barra ────────────────────────────────────
def bar_comparativo(df, x, y, title, ylim=0.65, height=420):
    df = df.copy()
    df["ano_str"] = df["ano"].astype(str)
    df["texto"]   = df[y].map(lambda v: f"{v:.1%}")

    fig = px.bar(
        df, x=x, y=y, color="ano_str",
        barmode="group",
        color_discrete_map={"2023": COR_2023, "2024": COR_2024},
        text="texto",
        title=title,
        labels={y: "Taxa Média de Evasão", "ano_str": "Ano", x: ""},
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=13, color="#333"),
        width=0.35,
    )
    fig.update_layout(
        height=height,
        yaxis_tickformat=".0%",
        yaxis_range=[0, ylim],
        plot_bgcolor="white",
        paper_bgcolor=BG,
        font=dict(family="Inter, Arial, sans-serif", size=13),
        legend=dict(title="Ano", orientation="h", y=-0.18, x=0.5,
                    xanchor="center"),
        margin=dict(t=55, b=80, l=55, r=20),
        bargap=0.3,
    )
    fig.update_xaxes(tickfont=dict(size=13))
    return fig

# ── Abas de gráficos ──────────────────────────────────────────────────────────
tabs = st.tabs(["🏫 Rede de Ensino", "🗺️ Região", "🏛️ Organização",
                "💰 Apoio Financeiro", "👤 Sexo", "📊 Distribuição"])

# TAB 1 — Rede
with tabs[0]:
    st.subheader("Taxa de Evasão por Rede de Ensino")
    st.caption("Comparativo entre cursos de instituições públicas e privadas nos dois anos.")
    fig = bar_comparativo(rede, "Rede", "taxa_media",
                          "Evasão por Rede de Ensino — 2023 vs 2024", ylim=0.60, height=430)
    st.plotly_chart(fig, use_container_width=True)

# TAB 2 — Região
with tabs[1]:
    st.subheader("Taxa de Evasão por Região do Brasil")
    st.caption("Média da taxa de evasão dos cursos EaD por grande região geográfica.")
    fig = bar_comparativo(reg, "Região", "taxa_media",
                          "Evasão por Região — 2023 vs 2024", ylim=0.60, height=430)
    st.plotly_chart(fig, use_container_width=True)

# TAB 3 — Organização
with tabs[2]:
    st.subheader("Taxa de Evasão por Tipo de Organização Acadêmica")
    st.caption("Universidades, centros universitários, faculdades e institutos federais.")
    fig = bar_comparativo(org, "Organização", "taxa_media",
                          "Evasão por Organização Acadêmica — 2023 vs 2024", ylim=0.75, height=430)
    st.plotly_chart(fig, use_container_width=True)

# TAB 4 — Apoio Financeiro
with tabs[3]:
    st.subheader("Taxa de Evasão por Apoio Financeiro (FIES / ProUni)")
    st.caption("Comparação entre cursos com e sem beneficiários de programas de apoio financeiro.")
    df_ap = apoio.copy()
    df_ap["ano_str"] = df_ap["ano"].astype(str)
    df_ap["texto"]   = df_ap["taxa_media"].map(lambda v: f"{v:.1%}")
    fig = px.bar(
        df_ap, x="Programa", y="taxa_media", color="Situação",
        facet_col="ano_str", barmode="group",
        color_discrete_map={"Com apoio": COR_COM, "Sem apoio": COR_SEM},
        text="texto",
        title="Evasão por Apoio Financeiro — 2023 vs 2024",
        labels={"taxa_media": "Taxa Média de Evasão", "ano_str": "Ano"},
    )
    fig.update_traces(textposition="outside", textfont=dict(size=13), width=0.35)
    fig.update_layout(
        height=430,
        yaxis_tickformat=".0%",
        yaxis_range=[0, 0.70],
        yaxis2_tickformat=".0%",
        yaxis2_range=[0, 0.70],
        plot_bgcolor="white",
        paper_bgcolor=BG,
        font=dict(family="Inter, Arial, sans-serif", size=13),
        margin=dict(t=55, b=80, l=55, r=20),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)

# TAB 5 — Sexo
with tabs[4]:
    st.subheader("Taxa de Evasão por Predominância de Sexo")
    st.caption("Cursos agrupados pela predominância do sexo dos ingressantes.")
    if tem_sexo:
        fig = bar_comparativo(sexo, "PREDOM_SEXO", "taxa_media",
                              "Evasão por Predominância de Sexo — 2023 vs 2024",
                              ylim=0.60, height=430)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Variável PREDOM_SEXO não disponível no arquivo de dados.")

# TAB 6 — Distribuição
with tabs[5]:
    st.subheader("Distribuição da Taxa de Evasão por Curso")
    st.caption("Cada ponto representa um curso EaD. A linha central é a mediana; o box mostra o IQR.")
    fig = go.Figure()
    for ano, cor in [(2023, COR_2023), (2024, COR_2024)]:
        vals = dist[dist["ano"] == ano]["TAXA_EVASAO"]
        fig.add_trace(go.Violin(
            y=vals, name=str(ano),
            box_visible=True, meanline_visible=True,
            fillcolor=cor, opacity=0.60,
            line_color=cor, points=False,
        ))
    fig.update_layout(
        height=430,
        yaxis_tickformat=".0%",
        yaxis_title="Taxa de Evasão",
        plot_bgcolor="white",
        paper_bgcolor=BG,
        font=dict(family="Inter, Arial, sans-serif", size=13),
        legend=dict(title="Ano"),
        margin=dict(t=40, b=40, l=55, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Autores ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div class="autores-box">
<h4>👥 Autores do Trabalho</h4>
Edesio de Barros &nbsp;·&nbsp;
Euclides Soares Barata &nbsp;·&nbsp;
Guilherme de Menezes Vaz de Mello &nbsp;·&nbsp;
Gustavo Antonio de Paula &nbsp;·&nbsp;
Marco Jose Franceschini &nbsp;·&nbsp;
Mariana Oliveira Silva &nbsp;·&nbsp;
Roger Marcio Reis da Silva &nbsp;·&nbsp;
Victor Lucas Pedroso Alves
<br><br>
<b>Trabalho de Conclusão de Curso</b> — Bacharelado em Ciência de Dados<br>
Universidade Virtual do Estado de São Paulo (Univesp) · São Paulo, 2026
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
