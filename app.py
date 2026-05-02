# app.py — TCC Evasão EaD | Univesp 2026 — v7
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Evasão EaD | TCC Univesp",
    page_icon="🎓",
    layout="wide"
)

COR_2023   = "#4CA3CC"
COR_2024   = "#E84855"
COR_COM    = "#4DBD8A"
COR_SEM    = "#F4A259"
BG_GRAF    = "rgba(255,255,255,0.03)"
GRID       = "rgba(255,255,255,0.06)"
TEXTO_EIXO = "#aaaaaa"
FONTE      = "Inter, Arial, sans-serif"

COR_CAT = {
    "Baixa (0–25%)":     "#4DBD8A",
    "Média (25–50%)":    "#F4A259",
    "Alta (50–75%)":     "#E84855",
    "Crítica (75–100%)": "#9B2335",
}

st.markdown("""
<style>
  .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
  .bloco-ano {
    border: 1px solid rgba(255,255,255,0.10); border-radius: 12px;
    padding: 20px 24px 18px; background: rgba(255,255,255,0.04);
  }
  .bloco-titulo {
    font-size: 17px; font-weight: 700; color: #cccccc;
    text-align: center; margin-bottom: 18px; letter-spacing: 0.3px;
  }
  .bloco-row { display: flex; gap: 20px; flex-wrap: wrap; }
  .bloco-item { flex: 1; min-width: 90px; }
  .kpi-label {
    font-size: 11px; color: #777; font-weight: 600;
    letter-spacing: .4px; margin-bottom: 3px;
  }
  .kpi-value    { font-size: 24px; font-weight: 700; color: #e8e8e8; line-height: 1.1; }
  .kpi-value-sm { font-size: 24px; font-weight: 700; color: #e8e8e8; line-height: 1.1; }
  .kpi-desc  { font-size: 11px; color: #666; margin-top: 5px; line-height: 1.45; }
  .delta-box {
    border-radius: 10px; padding: 16px 22px;
    border: 1px solid rgba(232,72,85,0.25);
    background: rgba(232,72,85,0.10); text-align: center;
  }
  .delta-box.negativo {
    background: rgba(77,189,138,0.10); border-color: rgba(77,189,138,0.25);
  }
  .delta-valor-pos { font-size: 26px; font-weight: 700; color: #E84855; }
  .delta-valor-neg { font-size: 26px; font-weight: 700; color: #4DBD8A; }
  .delta-desc { font-size: 12px; color: #888; margin-top: 4px; }
  .premissa-box {
    border-left: 3px solid rgba(244,162,89,0.6); border-radius: 6px;
    padding: 14px 18px; background: rgba(244,162,89,0.07);
    font-size: 13px; color: #bbb; line-height: 1.65;
  }
  .premissa-box b { color: #e0e0e0; }
  .premissa-box code {
    background: rgba(255,255,255,0.08); padding: 1px 5px;
    border-radius: 3px; font-size: 12px;
  }
  .tab-instrucao { font-size: 13px; color: #888; margin-bottom: 6px; }
  .autores-box {
    border-top: 1px solid rgba(255,255,255,0.08); padding: 20px 4px 8px;
    font-size: 12.5px; color: #666; line-height: 1.9;
  }
  .autores-box b { color: #999; }
</style>
""", unsafe_allow_html=True)

# ── Carregamento de dados ──────────────────────────────────────────────────────
_DATA_VERSION = "20260502-v6"  # atualizar sempre que os CSVs mudarem de formato

@st.cache_data
def load(nome, version=_DATA_VERSION):
    return pd.read_csv(f"streamlit_data/{nome}.csv")

try:
    kpi = load("kpi_v2")
except Exception:
    kpi = load("kpi")

rede  = load("rede")
reg   = load("regiao")
org   = load("org")
apoio = load("apoio")

try:
    dist_faixas = load("dist_faixas"); tem_dist = True
except Exception:
    tem_dist = False

try:
    genero = load("genero"); tem_genero = True
except Exception:
    tem_genero = False

try:
    grau = load("grau"); tem_grau = True
except Exception:
    tem_grau = False

try:
    top_cursos = load("top_cursos"); tem_top = True
except Exception:
    tem_top = False

# ── Extração de KPIs ──────────────────────────────────────────────────────────
def kpi_val(col, ano):
    try:
        v = kpi[kpi["ano"] == ano][col].values[0]
        return v if pd.notna(v) else None
    except Exception:
        return None

t23    = kpi_val("taxa_media",    2023) or 0
t24    = kpi_val("taxa_media",    2024) or 0
med23  = kpi_val("taxa_mediana",  2023)
med24  = kpi_val("taxa_mediana",  2024)
delta  = t24 - t23
n_ies23  = kpi_val("n_instituicoes",     2023)
n_ies24  = kpi_val("n_instituicoes",     2024)
n_cur23  = kpi_val("n_cursos_distintos", 2023)
n_cur24  = kpi_val("n_cursos_distintos", 2024)

def fmt_int(v):
    return f"{int(v):,}".replace(",", ".") if v is not None else "—"

def fmt_pct(v):
    return f"{v:.1%}" if v is not None else "—"

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
_col_titulo, _col_logo = st.columns([8, 1.4])
with _col_titulo:
    st.title("🎓 Evasão no Ensino Superior a Distância no Brasil")
    st.caption("TCC — Ciência de Dados | Univesp 2026 · Fonte: Censo da Educação Superior — INEP 2023 e 2024")
with _col_logo:
    _logo = "assets/logo_univesp.png"
    if os.path.exists(_logo):
        st.image(_logo, width=140)
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
col_23, _, col_24, col_delta = st.columns([5, 0.2, 5, 3])

with col_23:
    st.markdown(f"""
    <div class="bloco-ano">
      <div class="bloco-titulo">📅 2023</div>
      <div class="bloco-row">
        <div class="bloco-item">
          <div class="kpi-label">Instituições EaD</div>
          <div class="kpi-value">{fmt_int(n_ies23)}</div>
          <div class="kpi-desc">IES distintas com ao menos um curso EaD</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Cursos EaD</div>
          <div class="kpi-value">{fmt_int(n_cur23)}</div>
          <div class="kpi-desc">Cursos distintos na modalidade EaD (graduação)</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Média de Evasão</div>
          <div class="kpi-value">{t23:.1%}</div>
          <div class="kpi-desc">Desvinculados ÷ ingressantes, média entre os cursos</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Mediana de Evasão</div>
          <div class="kpi-value kpi-value-sm">{fmt_pct(med23)}</div>
          <div class="kpi-desc">Valor central — menos afetado por extremos</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

with col_24:
    st.markdown(f"""
    <div class="bloco-ano">
      <div class="bloco-titulo">📅 2024</div>
      <div class="bloco-row">
        <div class="bloco-item">
          <div class="kpi-label">Instituições EaD</div>
          <div class="kpi-value">{fmt_int(n_ies24)}</div>
          <div class="kpi-desc">IES distintas com ao menos um curso EaD</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Cursos EaD</div>
          <div class="kpi-value">{fmt_int(n_cur24)}</div>
          <div class="kpi-desc">Cursos distintos na modalidade EaD (graduação)</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Média de Evasão</div>
          <div class="kpi-value">{t24:.1%}</div>
          <div class="kpi-desc">Desvinculados ÷ ingressantes, média entre os cursos</div>
        </div>
        <div class="bloco-item">
          <div class="kpi-label">Mediana de Evasão</div>
          <div class="kpi-value kpi-value-sm">{fmt_pct(med24)}</div>
          <div class="kpi-desc">Valor central — menos afetado por extremos</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

with col_delta:
    cls_box   = "negativo" if delta < 0 else ""
    cls_valor = "delta-valor-neg" if delta < 0 else "delta-valor-pos"
    sinal     = f"▲ +{delta:.1%}" if delta > 0 else f"▼ {delta:.1%}"
    msg       = "Aumento na evasão — sinal de alerta" if delta > 0 else "Redução na evasão"
    st.markdown(f"""
    <div style="height:100%;display:flex;align-items:center;">
      <div class="delta-box {cls_box}" style="width:100%">
        <div style="font-size:11px;color:#888;font-weight:600;
                    text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">
          Variação da evasão
        </div>
        <div class="{cls_valor}">{sinal}</div>
        <div class="delta-desc">{msg}<br>2023 → 2024</div>
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Premissas ─────────────────────────────────────────────────────────────────
with st.expander("⚠️  Premissas e definições — leia antes de interpretar os dados",
                 expanded=False):
    st.markdown(f"""
    <div class="premissa-box">

    <b>Instituições EaD ({fmt_int(n_ies23)} em 2023 · {fmt_int(n_ies24)} em 2024)</b><br>
    Contagem de <b>IES distintas</b> (Instituições de Ensino Superior) com ao menos um curso
    de graduação na modalidade EaD no Censo INEP do respectivo ano. Inclui universidades,
    centros universitários, faculdades e institutos federais. Não contempla cursos técnicos,
    livres ou de pós-graduação.<br><br>

    <b>Cursos EaD ({fmt_int(n_cur23)} em 2023 · {fmt_int(n_cur24)} em 2024)</b><br>
    Contagem de <b>cursos distintos</b> pelo código de curso do INEP na modalidade EaD.
    Um mesmo curso (ex: Administração) pode existir em várias IES — o indicador mede a
    variedade de cursos oferecidos, não o volume total de ofertas. Base restrita a
    graduação (bacharelado, licenciatura e tecnólogo).<br><br>

    <b>Média vs. Mediana de Evasão</b><br>
    — <b>Média ({t23:.1%} em 2023 · {t24:.1%} em 2024):</b> calculada por curso como
    <code>QT_SIT_DESVINCULADO / QT_ING</code>, depois calculada a média entre todos os cursos.<br>
    — <b>Mediana ({fmt_pct(med23)} em 2023 · {fmt_pct(med24)} em 2024):</b> valor central da
    distribuição — indica o ponto onde metade dos cursos tem evasão abaixo e metade acima.<br><br>

    <b>Atenção: unidade de análise</b><br>
    Os dados do Censo INEP são organizados por <b>curso × IES</b>, não por aluno individual.
    Os indicadores refletem comportamentos médios dos cursos — não a probabilidade de
    um aluno específico evadir.<br><br>

    <b>Fonte:</b>
    Microdados do Censo da Educação Superior, INEP, anos-base 2023 e 2024.
    Acesso em: <a href="https://www.gov.br/inep" target="_blank"
    style="color:#4CA3CC">gov.br/inep</a>

    </div>""", unsafe_allow_html=True)

st.divider()

# ── Helpers ───────────────────────────────────────────────────────────────────
def layout_dark(fig, ylim=0.65, height=420, yformat=".0%", ytitle="Taxa de Evasão"):
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
            orientation="h", y=-0.22, x=0.5, xanchor="center",
        ),
        xaxis=dict(
            gridcolor=GRID, linecolor="rgba(255,255,255,0.10)",
            tickfont=dict(color=TEXTO_EIXO, size=12),
            title_font=dict(color=TEXTO_EIXO),
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor=GRID, linecolor="rgba(255,255,255,0.10)",
            tickfont=dict(color=TEXTO_EIXO, size=12),
            title_font=dict(color=TEXTO_EIXO),
            title=ytitle, tickformat=yformat,
            range=[0, ylim], showgrid=True, gridwidth=1,
        ),
        margin=dict(t=55, b=95, l=65, r=20),
        bargap=0.30,
    )
    return fig

def bar_comparativo(df, x, y, title, ylim=0.65, height=420):
    df = df.copy()
    df["ano_str"] = df["ano"].astype(str)
    df["texto"]   = df[y].map(lambda v: f"{v:.1%}")
    fig = px.bar(
        df, x=x, y=y, color="ano_str", barmode="group",
        color_discrete_map={"2023": COR_2023, "2024": COR_2024},
        text="texto", title=title,
        labels={y: "Taxa de Evasão", "ano_str": "", x: ""},
    )
    fig.update_traces(textposition="outside",
                      textfont=dict(size=13, color="#dddddd"), width=0.33)
    fig = layout_dark(fig, ylim=ylim, height=height)
    fig.update_layout(legend=dict(
        orientation="h", x=0.5, xanchor="center",
        y=1.04, yanchor="bottom", title_text="",
    ), margin=dict(t=70, b=60, l=65, r=20))
    return fig

# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="tab-instrucao">Selecione a dimensão para analisar a taxa de evasão:</p>',
            unsafe_allow_html=True)

tabs = st.tabs([
    "🏫  Rede de Ensino",
    "🗺️  Região",
    "🏛️  Organização",
    "🎓  Grau Acadêmico",
    "💰  Apoio Financeiro",
    "👤  Gênero",
    "📊  Distribuição",
    "🏆  Top Cursos",
])

# ── Rede de Ensino ────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Taxa de Evasão por Rede de Ensino")
    st.caption("Comparativo entre cursos de instituições públicas e privadas.")
    st.plotly_chart(bar_comparativo(rede, "Rede", "taxa_media",
        "Evasão por Rede de Ensino — 2023 vs 2024", ylim=0.60),
        use_container_width=True)

# ── Região ────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Taxa de Evasão por Região do Brasil")
    st.caption("Média da taxa de evasão dos cursos EaD por grande região geográfica.")
    st.plotly_chart(bar_comparativo(reg, "Região", "taxa_media",
        "Evasão por Região — 2023 vs 2024", ylim=0.60),
        use_container_width=True)

# ── Organização ───────────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Taxa de Evasão por Tipo de Organização Acadêmica")
    st.caption("Universidades, centros universitários, faculdades e institutos federais.")
    st.plotly_chart(bar_comparativo(org, "Organização", "taxa_media",
        "Evasão por Organização Acadêmica — 2023 vs 2024", ylim=0.75),
        use_container_width=True)

# ── Grau Acadêmico ────────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("Taxa de Evasão por Grau Acadêmico")
    st.caption("Comparativo entre Bacharelado, Licenciatura e Tecnólogo na modalidade EaD.")
    if tem_grau:
        st.plotly_chart(bar_comparativo(grau, "Grau", "taxa_media",
            "Evasão por Grau Acadêmico — 2023 vs 2024", ylim=0.65),
            use_container_width=True)
    else:
        st.info("Arquivo grau.csv não encontrado. Execute gerar_agregados.py.")

# ── Apoio Financeiro ──────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Taxa de Evasão por Apoio Financeiro (FIES / ProUni)")
    st.caption("Cursos com e sem beneficiários de programas de financiamento e bolsas.")
    df_ap = apoio.copy()
    df_ap["ano_str"] = df_ap["ano"].astype(str)
    df_ap["texto"]   = df_ap["taxa_media"].map(lambda v: f"{v:.1%}")
    fig = px.bar(df_ap, x="Programa", y="taxa_media", color="Situação",
                 facet_col="ano_str", barmode="group",
                 color_discrete_map={"Com apoio": COR_COM, "Sem apoio": COR_SEM},
                 text="texto", title="Evasão por Apoio Financeiro — 2023 vs 2024",
                 labels={"taxa_media": "Taxa de Evasão", "ano_str": "Ano"})
    fig.update_traces(textposition="outside",
                      textfont=dict(size=13, color="#dddddd"), width=0.33)
    fig = layout_dark(fig, ylim=0.70)
    fig.update_layout(yaxis2=dict(tickformat=".0%", range=[0, 0.70],
                                  gridcolor=GRID, gridwidth=1,
                                  tickfont=dict(color=TEXTO_EIXO, size=12),
                                  showgrid=True))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("FIES: Fundo de Financiamento Estudantil. ProUni: Programa Universidade para Todos. "
               "Cursos 'Com apoio' têm ao menos um ingressante beneficiário do programa.")

# ── Gênero ────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("Taxa de Evasão por Predominância de Gênero")
    st.caption("Cursos agrupados pela predominância do gênero dos ingressantes "
               "(Feminino > 60%, Masculino > 60%, ou Equilibrado).")
    if tem_genero:
        st.plotly_chart(bar_comparativo(genero, "Gênero predominante", "taxa_media",
            "Evasão por Gênero Predominante — 2023 vs 2024", ylim=0.60),
            use_container_width=True)
    else:
        st.info("Arquivo genero.csv não encontrado. Execute gerar_agregados.py.")

# ── Distribuição ──────────────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("Distribuição dos Cursos EaD por Taxa de Evasão")
    st.caption("Quantos cursos se enquadram em cada faixa de evasão? "
               "Alterne entre a visão detalhada (10% em 10%) e a visão por categorias.")

    if not tem_dist:
        st.warning("Arquivo dist_faixas.csv não encontrado.")
    else:
        opcao = st.selectbox(
            "Granularidade das faixas:",
            options=["Detalhada", "Resumida"],
        )
        tipo_sel = "10pct" if opcao == "Detalhada" else "categorias"
        df_d = dist_faixas[dist_faixas["tipo"] == tipo_sel].copy()
        df_d["ano_str"] = df_d["ano"].astype(str)
        df_d["texto"]   = df_d["pct_cursos"].map(lambda v: f"{v:.1%}")

        if tipo_sel == "10pct":
            fig = px.bar(
                df_d, x="Faixa", y="n_cursos", color="ano_str",
                barmode="group",
                color_discrete_map={"2023": COR_2023, "2024": COR_2024},
                text="texto",
                title="Distribuição dos Cursos EaD por Faixa de Evasão — 2023 vs 2024",
                labels={"n_cursos": "Nº de Cursos", "Faixa": "Faixa de Evasão", "ano_str": ""},
            )
            fig.update_traces(textposition="outside",
                              textfont=dict(size=11, color="#dddddd"), width=0.38)
            fig = layout_dark(fig, ylim=df_d["n_cursos"].max() * 1.18,
                              height=440, yformat=",d", ytitle="Número de Cursos")
            fig.update_layout(
                xaxis=dict(tickangle=-40, tickfont=dict(size=11, color=TEXTO_EIXO)),
                legend=dict(orientation="h", x=0.5, xanchor="center",
                            y=1.04, yanchor="bottom", title_text=""),
                margin=dict(t=70, b=60, l=65, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Visão detalhada — cada barra mostra quantos cursos EaD têm evasão "
                       "naquela faixa de 10 pontos percentuais. O rótulo indica a proporção "
                       "sobre o total de cursos do ano.")
        else:
            ordem_cat = ["Baixa (0–25%)", "Média (25–50%)",
                         "Alta (50–75%)", "Crítica (75–100%)"]
            fig = px.bar(
                df_d, x="ano_str", y="pct_cursos", color="Faixa",
                barmode="stack",
                color_discrete_map=COR_CAT,
                category_orders={"Faixa": ordem_cat},
                text="texto",
                title="Proporção de Cursos EaD por Categoria de Evasão — 2023 vs 2024",
                labels={"pct_cursos": "Proporção de Cursos", "ano_str": "Ano", "Faixa": "Categoria"},
            )
            fig.update_traces(textposition="inside",
                              textfont=dict(size=13, color="white", family=FONTE),
                              insidetextanchor="middle")
            fig = layout_dark(fig, ylim=1.05, height=440,
                              yformat=".0%", ytitle="Proporção de Cursos")
            fig.update_layout(
                xaxis=dict(tickfont=dict(size=14, color="#cccccc")),
                legend=dict(orientation="v", x=1.02, xanchor="left",
                            y=0.5, yanchor="middle", title_text=""),
                bargap=0.45,
                margin=dict(t=55, b=60, l=65, r=160),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Visão resumida — cada segmento mostra a proporção dos cursos na "
                       "categoria: Baixa (0–25%), Média (25–50%), Alta (50–75%) e "
                       "Crítica (75–100%). Cursos com evasão acima de 50% (Alta + Crítica) "
                       "indicam sinal de alerta.")

# ── Top Cursos ────────────────────────────────────────────────────────────────
with tabs[7]:
    st.subheader("Cursos EaD com Maior Taxa de Evasão")
    st.caption(
        "Taxa agregada nacionalmente por nome de curso — soma de ingressantes e evadidos "
        "de todas as instituições. Use os filtros para recortar a análise por rede, grau e região."
    )

    if not tem_top:
        st.info("Arquivo top_cursos.csv não encontrado. Execute gerar_agregados.py.")
    else:
        # ── Filtros compartilhados ────────────────────────────────────────────
        redes_disp   = sorted(top_cursos["Rede"].dropna().unique())
        graus_disp   = sorted(top_cursos["Grau"].dropna().unique())
        regioes_disp = sorted(top_cursos["NO_REGIAO_IES"].dropna().unique())

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            sel_rede = st.multiselect(
                "Rede de Ensino", redes_disp, default=redes_disp, key="top_rede"
            )
        with fc2:
            sel_grau = st.multiselect(
                "Grau Acadêmico", graus_disp, default=graus_disp, key="top_grau"
            )
        with fc3:
            sel_regiao = st.multiselect(
                "Região", regioes_disp, default=regioes_disp, key="top_regiao"
            )

        MIN_ING = 500  # mínimo de ingressantes nacionais por curso

        def get_top(ano):
            """Filtra, agrega por curso e retorna top 15 com numeração."""
            df_f = top_cursos[
                (top_cursos["ano"] == ano) &
                (top_cursos["Rede"].isin(sel_rede if sel_rede else redes_disp)) &
                (top_cursos["Grau"].isin(sel_grau if sel_grau else graus_disp)) &
                (top_cursos["NO_REGIAO_IES"].isin(sel_regiao if sel_regiao else regioes_disp))
            ]
            agg = (
                df_f.groupby("NO_CURSO")
                .agg(Ingressantes=("QT_ING_TOTAL", "sum"),
                     Evadidos=("QT_DESV_TOTAL", "sum"))
                .reset_index()
            )
            agg = agg[agg["Ingressantes"] >= MIN_ING].copy()
            agg["TAXA_EVASAO"] = agg["Evadidos"] / agg["Ingressantes"]
            agg["Taxa de Evasão"] = agg["TAXA_EVASAO"].map(lambda v: f"{v:.1%}")
            agg = agg.sort_values("TAXA_EVASAO", ascending=False).head(15).reset_index(drop=True)
            agg["Curso"] = (agg.index + 1).astype(str) + ". " + agg["NO_CURSO"]
            return agg

        def chart_top(df_top, ano, cor):
            """Gráfico horizontal de barras para o top cursos de um ano."""
            fig = px.bar(
                df_top, x="TAXA_EVASAO", y="Curso",
                orientation="h",
                text="Taxa de Evasão",
                title=f"Top 15 — {ano}",
                labels={"TAXA_EVASAO": "Taxa de Evasão", "Curso": ""},
            )
            fig.update_traces(
                marker_color=cor,
                textposition="outside",
                textfont=dict(size=11, color="#dddddd"),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Taxa de Evasão: <b>%{x:.1%}</b><br>"
                    "<extra></extra>"
                ),
            )
            fig.update_layout(
                height=480,
                plot_bgcolor=BG_GRAF,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family=FONTE, size=11, color="#cccccc"),
                title_font=dict(size=14, color="#e0e0e0"),
                showlegend=False,
                yaxis=dict(autorange="reversed",
                           tickfont=dict(color=TEXTO_EIXO, size=10),
                           gridcolor=GRID),
                xaxis=dict(tickformat=".0%", range=[0, 1.08],
                           tickfont=dict(color=TEXTO_EIXO, size=10),
                           gridcolor=GRID, showgrid=True),
                margin=dict(t=50, b=30, l=220, r=60),
            )
            return fig

        # ── Layout lado a lado ────────────────────────────────────────────────
        col23, col24 = st.columns(2)

        for col, ano, cor in [(col23, 2023, COR_2023), (col24, 2024, COR_2024)]:
            with col:
                df_top = get_top(ano)
                if df_top.empty:
                    st.warning(f"Nenhum curso com ≥ {MIN_ING} ingressantes nos filtros selecionados ({ano}).")
                else:
                    st.plotly_chart(chart_top(df_top, ano, cor),
                                    use_container_width=True)
                    st.dataframe(
                        df_top[["Curso", "Ingressantes", "Evadidos", "Taxa de Evasão"]],
                        use_container_width=True, hide_index=True,
                    )

        st.caption(
            f"Mínimo de {MIN_ING:,} ingressantes nacionais por curso para entrar no ranking. "
            "Taxa calculada como total de evadidos ÷ total de ingressantes de todas as instituições "
            "e polos dentro dos filtros selecionados."
        )

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
