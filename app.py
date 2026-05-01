# app.py — TCC Evasão EaD | Univesp 2026 — v3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Evasão EaD | TCC Univesp",
    page_icon="🎓",
    layout="wide"
)

# ── Paleta dark ───────────────────────────────────────────────────────────────
COR_2023    = "#4CA3CC"   # azul mais claro — legível no dark
COR_2024    = "#E84855"   # vermelho/coral
COR_COM     = "#4DBD8A"   # verde
COR_SEM     = "#F4A259"   # laranja
BG_CARD     = "rgba(255,255,255,0.04)"
BG_GRAF     = "rgba(255,255,255,0.03)"
BORDA       = "rgba(255,255,255,0.10)"
GRID        = "rgba(255,255,255,0.06)"
TEXTO_EIXO  = "#aaaaaa"
FONTE       = "Inter, Arial, sans-serif"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }

  /* --- Bloco ano (2023 / 2024) --- */
  .bloco-ano {
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 20px 24px 18px;
    background: rgba(255,255,255,0.04);
  }
  .bloco-titulo {
    font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #888; margin-bottom: 14px;
  }
  .bloco-row { display: flex; gap: 24px; flex-wrap: wrap; }
  .bloco-item { flex: 1; min-width: 100px; }
  .kpi-label {
    font-size: 11px; color: #777; font-weight: 600;
    text-transform: uppercase; letter-spacing: .4px; margin-bottom: 3px;
  }
  .kpi-value { font-size: 26px; font-weight: 700; color: #e8e8e8; line-height: 1.1; }
  .kpi-desc  { font-size: 11px; color: #666; margin-top: 5px; line-height: 1.45; }

  /* --- Caixa delta --- */
  .delta-box {
    border-radius: 10px;
    padding: 16px 22px;
    background: rgba(232,72,85,0.10);
    border: 1px solid rgba(232,72,85,0.25);
    text-align: center;
  }
  .delta-box.positivo { background: rgba(232,72,85,0.10); border-color: rgba(232,72,85,0.25); }
  .delta-box.negativo { background: rgba(77,189,138,0.10); border-color: rgba(77,189,138,0.25); }
  .delta-valor-pos { font-size: 26px; font-weight: 700; color: #E84855; }
  .delta-valor-neg { font-size: 26px; font-weight: 700; color: #4DBD8A; }
  .delta-desc { font-size: 12px; color: #888; margin-top: 4px; }

  /* --- Premissas --- */
  .premissa-box {
    border-left: 3px solid rgba(244,162,89,0.6);
    border-radius: 6px;
    padding: 14px 18px;
    background: rgba(244,162,89,0.07);
    font-size: 13px; color: #bbb; line-height: 1.65;
  }
  .premissa-box b { color: #e0e0e0; }
  .premissa-box code {
    background: rgba(255,255,255,0.08);
    padding: 1px 5px; border-radius: 3px; font-size: 12px;
  }

  /* --- Tabs --- */
  .tab-instrucao {
    font-size: 13px; color: #888; margin-bottom: 6px; margin-top: 2px;
  }

  /* --- Autores --- */
  .autores-box {
    border-top: 1px solid rgba(255,255,255,0.08);
    padding: 20px 4px 8px;
    font-size: 12.5px; color: #666; line-height: 1.9;
  }
  .autores-box b { color: #999; }
</style>
""", unsafe_allow_html=True)

# ── Dados ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load(nome):
    return pd.read_csv(f"streamlit_data/{nome}.csv")

# KPI — tenta v2 (com IES/cursos distintos), cai para v1
try:
    kpi = load("kpi_v2")
    tem_kpi_v2 = True
except Exception:
    kpi = load("kpi")
    tem_kpi_v2 = False

rede  = load("rede")
reg   = load("regiao")
org   = load("org")
apoio = load("apoio")
dist  = load("distribuicao")
try:
    sexo = load("sexo"); tem_sexo = True
except Exception:
    tem_sexo = False

def kpi_val(col, ano):
    try:
        v = kpi[kpi["ano"] == ano][col].values[0]
        return v if pd.notna(v) else None
    except Exception:
        return None

t23   = kpi_val("taxa_media", 2023) or 0
t24   = kpi_val("taxa_media", 2024) or 0
delta = t24 - t23

n_ies23  = kpi_val("n_instituicoes",    2023)
n_ies24  = kpi_val("n_instituicoes",    2024)
n_cur23  = kpi_val("n_cursos_distintos", 2023)
n_cur24  = kpi_val("n_cursos_distintos", 2024)

def fmt_int(v):
    return f"{int(v):,}".replace(",", ".") if v is not None else "—"

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title("🎓 Evasão no Ensino Superior a Distância no Brasil")
st.caption("TCC — Ciência de Dados | Univesp 2026 · Fonte: Censo da Educação Superior — INEP 2023 e 2024")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
col_23, col_sep, col_24, col_delta = st.columns([5, 0.2, 5, 3])

with col_23:
    st.markdown(f"""
    <div class="bloco-ano">
      <div class="bloco-titulo">📅 2023</div>
      <div class="bloco-row">
        <div class="bloco-item">
          <div class="kpi-label">Instituições EaD</div>
          <div class="kpi-value">{fmt_int(n_ies23)}</div>
          <div class="kpi-desc">IES distintas que oferecem ao menos um curso EaD</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Cursos EaD</div>
          <div class="kpi-value">{fmt_int(n_cur23)}</div>
          <div class="kpi-desc">Cursos distintos na modalidade EaD (graduação)</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Taxa de Evasão</div>
          <div class="kpi-value">{t23:.1%}</div>
          <div class="kpi-desc">Média de desvinculados ÷ ingressantes por curso</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_24:
    st.markdown(f"""
    <div class="bloco-ano">
      <div class="bloco-titulo">📅 2024</div>
      <div class="bloco-row">
        <div class="bloco-item">
          <div class="kpi-label">Instituições EaD</div>
          <div class="kpi-value">{fmt_int(n_ies24)}</div>
          <div class="kpi-desc">IES distintas que oferecem ao menos um curso EaD</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Cursos EaD</div>
          <div class="kpi-value">{fmt_int(n_cur24)}</div>
          <div class="kpi-desc">Cursos distintos na modalidade EaD (graduação)</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Taxa de Evasão</div>
          <div class="kpi-value">{t24:.1%}</div>
          <div class="kpi-desc">Média de desvinculados ÷ ingressantes por curso</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_delta:
    cls_box   = "positivo" if delta > 0 else "negativo"
    cls_valor = "delta-valor-pos" if delta > 0 else "delta-valor-neg"
    sinal     = f"▲ +{delta:.1%}" if delta > 0 else f"▼ {delta:.1%}"
    msg       = "Aumento na evasão — sinal de alerta" if delta > 0 else "Redução na evasão"
    st.markdown(f"""
    <div style="height:100%; display:flex; align-items:center;">
      <div class="delta-box {cls_box}" style="width:100%">
        <div style="font-size:11px;color:#888;font-weight:600;
                    text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">
          Variação da evasão
        </div>
        <div class="{cls_valor}">{sinal}</div>
        <div class="delta-desc">{msg}<br>2023 → 2024</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Premissas ─────────────────────────────────────────────────────────────────
with st.expander("⚠️  Premissas e definições — leia antes de interpretar os dados", expanded=False):
    st.markdown("""
    <div class="premissa-box">
    <b>O que é a taxa de evasão?</b><br>
    Para cada curso: <code>TAXA_EVASAO = QT_SIT_DESVINCULADO / QT_ING</code>.
    O numerador conta alunos que se desvincularam do curso no ano (abandono, desistência formal
    ou exclusão por norma institucional). O denominador é o total de ingressantes naquele curso
    no mesmo ano de referência.<br><br>

    <b>Unidade de análise</b><br>
    O Censo INEP é organizado por <b>curso × instituição</b>. Cada linha representa um curso
    em uma IES específica — não um aluno. Uma mesma universidade aparece tantas vezes
    quantos cursos EaD ela oferece. Por isso os números de vínculos (~400 mil) são maiores
    que o número de cursos ou instituições distintos.<br><br>

    <b>O que são "Cursos EaD" nos KPIs?</b><br>
    Contagem de <b>códigos de curso distintos</b> (ex: Administração, Pedagogia, Direito…)
    presentes na base após o filtro EaD. Um mesmo código pode existir em múltiplas IES —
    o que é contado aqui é a variedade de cursos, não a quantidade de ofertas.<br><br>

    <b>Escopo da base</b><br>
    Apenas cursos de <b>graduação na modalidade EaD</b> com pelo menos 1 ingressante e
    taxa entre 0% e 100%. Cursos com dados ausentes nessas variáveis foram excluídos.
    Dados de pós-graduação, cursos técnicos e presenciais não estão incluídos.<br><br>

    <b>Fonte</b><br>
    Microdados do Censo da Educação Superior, INEP, anos-base 2023 e 2024.
    Acesso em: <a href="https://www.gov.br/inep" target="_blank" style="color:#4CA3CC">gov.br/inep</a>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Helper: layout padrão dos gráficos (dark) ─────────────────────────────────
def layout_dark(fig, ylim=0.65, height=420):
    fig.update_layout(
        height=height,
        plot_bgcolor=BG_GRAF,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=13, color="#cccccc"),
        title_font=dict(size=15, color="#e0e0e0"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.05)",
            bordercolor="rgba(255,255,255,0.10)",
            borderwidth=1,
            font=dict(color="#cccccc", size=12),
            orientation="h", y=-0.20, x=0.5, xanchor="center",
        ),
        xaxis=dict(
            gridcolor=GRID,
            linecolor="rgba(255,255,255,0.10)",
            tickfont=dict(color=TEXTO_EIXO, size=12),
            title_font=dict(color=TEXTO_EIXO),
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor=GRID,
            linecolor="rgba(255,255,255,0.10)",
            tickfont=dict(color=TEXTO_EIXO, size=12),
            title_font=dict(color=TEXTO_EIXO),
            tickformat=".0%",
            range=[0, ylim],
            showgrid=True,
            gridwidth=1,
        ),
        margin=dict(t=55, b=90, l=60, r=20),
        bargap=0.30,
    )
    return fig

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
        labels={y: "Taxa de Evasão", "ano_str": "Ano", x: ""},
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=13, color="#dddddd"),
        width=0.33,
    )
    return layout_dark(fig, ylim=ylim, height=height)

# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="tab-instrucao">Selecione a dimensão para analisar a taxa de evasão:</p>',
            unsafe_allow_html=True)

tabs = st.tabs([
    "🏫  Rede de Ensino",
    "🗺️  Região",
    "🏛️  Organização",
    "💰  Apoio Financeiro",
    "👤  Gênero",
    "📊  Distribuição",
])

# TAB 1 — Rede
with tabs[0]:
    st.subheader("Taxa de Evasão por Rede de Ensino")
    st.caption("Comparativo entre cursos de instituições públicas e privadas.")
    fig = bar_comparativo(rede, "Rede", "taxa_media",
                          "Evasão por Rede de Ensino — 2023 vs 2024", ylim=0.60)
    st.plotly_chart(fig, use_container_width=True)

# TAB 2 — Região
with tabs[1]:
    st.subheader("Taxa de Evasão por Região do Brasil")
    st.caption("Média da taxa de evasão dos cursos EaD por grande região geográfica.")
    fig = bar_comparativo(reg, "Região", "taxa_media",
                          "Evasão por Região — 2023 vs 2024", ylim=0.60)
    st.plotly_chart(fig, use_container_width=True)

# TAB 3 — Organização
with tabs[2]:
    st.subheader("Taxa de Evasão por Tipo de Organização Acadêmica")
    st.caption("Universidades, centros universitários, faculdades e institutos federais.")
    fig = bar_comparativo(org, "Organização", "taxa_media",
                          "Evasão por Organização Acadêmica — 2023 vs 2024", ylim=0.75)
    st.plotly_chart(fig, use_container_width=True)

# TAB 4 — Apoio Financeiro
with tabs[3]:
    st.subheader("Taxa de Evasão por Apoio Financeiro (FIES / ProUni)")
    st.caption("Cursos com e sem beneficiários de programas de financiamento e bolsas.")
    df_ap = apoio.copy()
    df_ap["ano_str"] = df_ap["ano"].astype(str)
    df_ap["texto"]   = df_ap["taxa_media"].map(lambda v: f"{v:.1%}")
    fig = px.bar(
        df_ap, x="Programa", y="taxa_media", color="Situação",
        facet_col="ano_str", barmode="group",
        color_discrete_map={"Com apoio": COR_COM, "Sem apoio": COR_SEM},
        text="texto",
        title="Evasão por Apoio Financeiro — 2023 vs 2024",
        labels={"taxa_media": "Taxa de Evasão", "ano_str": "Ano"},
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=13, color="#dddddd"),
        width=0.33,
    )
    fig = layout_dark(fig, ylim=0.70)
    # Replicar eixo y no facet
    fig.update_layout(
        yaxis2=dict(
            tickformat=".0%", range=[0, 0.70],
            gridcolor=GRID, gridwidth=1,
            tickfont=dict(color=TEXTO_EIXO, size=12),
            showgrid=True,
        )
    )
    st.plotly_chart(fig, use_container_width=True)

# TAB 5 — Gênero
with tabs[4]:
    st.subheader("Taxa de Evasão por Predominância de Gênero")
    st.caption("Cursos agrupados pela predominância do gênero dos ingressantes.")
    if tem_sexo:
        df_s = sexo.copy()
        df_s = df_s.rename(columns={"PREDOM_SEXO": "Gênero predominante"})
        fig = bar_comparativo(df_s, "Gênero predominante", "taxa_media",
                              "Evasão por Gênero Predominante — 2023 vs 2024", ylim=0.60)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Variável PREDOM_SEXO não disponível no arquivo de dados.")

# TAB 6 — Distribuição
with tabs[5]:
    st.subheader("Distribuição da Taxa de Evasão por Curso")
    st.caption("A linha central é a mediana; o box mostra o intervalo interquartil (IQR).")
    fig = go.Figure()
    for ano, cor in [(2023, COR_2023), (2024, COR_2024)]:
        vals = dist[dist["ano"] == ano]["TAXA_EVASAO"]
        fig.add_trace(go.Violin(
            y=vals, name=str(ano),
            box_visible=True, meanline_visible=True,
            fillcolor=cor, opacity=0.55,
            line_color=cor, points=False,
        ))
    fig.update_layout(
        height=430,
        plot_bgcolor=BG_GRAF,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=13, color="#cccccc"),
        title_font=dict(size=15, color="#e0e0e0"),
        yaxis=dict(
            tickformat=".0%", title="Taxa de Evasão",
            gridcolor=GRID, gridwidth=1,
            tickfont=dict(color=TEXTO_EIXO, size=12),
            title_font=dict(color=TEXTO_EIXO),
        ),
        xaxis=dict(
            tickfont=dict(color=TEXTO_EIXO),
            showgrid=False,
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.05)",
            bordercolor="rgba(255,255,255,0.10)",
            borderwidth=1,
            font=dict(color="#cccccc"),
        ),
        margin=dict(t=40, b=40, l=60, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Autores ───────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="autores-box">
<b>Autores:</b>
Edesio de Barros · Euclides Soares Barata · Guilherme de Menezes Vaz de Mello ·
Gustavo Antonio de Paula · Marco Jose Franceschini · Mariana Oliveira Silva ·
Roger Marcio Reis da Silva · Victor Lucas Pedroso Alves<br>
<b>Trabalho de Conclusão de Curso</b> — Bacharelado em Ciência de Dados ·
Universidade Virtual do Estado de São Paulo (Univesp) · 2026
</div>
""", unsafe_allow_html=True)
