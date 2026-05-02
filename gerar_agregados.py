"""
gerar_agregados.py
Gera os CSVs de streamlit_data/ a partir dos df_completo já processados.
Execute: python gerar_agregados.py
"""

import os
import pandas as pd

# ── Caminhos ──────────────────────────────────────────────────────────────────
DATA_DIR  = r"C:\Users\Victor\OneDrive\Documentos\UNIVESP\tcc\dados"
TRAT_DIR  = os.path.join(DATA_DIR, "dados_tratados")
IES_2023  = os.path.join(DATA_DIR, "microdados_censo_da_educacao_superior_2023",
                         "dados", "MICRODADOS_ED_SUP_IES_2023.CSV")
IES_2024  = os.path.join(DATA_DIR, "microdados_censo_da_educacao_superior_2024",
                         "dados", "MICRODADOS_ED_SUP_IES_2024.CSV")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "streamlit_data")
os.makedirs(OUT_DIR, exist_ok=True)

SEP = ";"

# ── Carregar dados ────────────────────────────────────────────────────────────
print("Carregando df_completo_2023.csv...")
df23 = pd.read_csv(os.path.join(TRAT_DIR, "df_completo_2023.csv"), sep=SEP, low_memory=False).copy()
df23["ano"] = 2023

print("Carregando df_completo_2024.csv...")
df24 = pd.read_csv(os.path.join(TRAT_DIR, "df_completo_2024.csv"), sep=SEP, low_memory=False).copy()
df24["ano"] = 2024

print(f"Registros carregados: {len(df23):,} (2023) | {len(df24):,} (2024)")

# ── Nomes das IES (join para top_cursos) ─────────────────────────────────────
print("Carregando nomes das IES...")
ies23 = pd.read_csv(IES_2023, sep=SEP, encoding="latin-1", usecols=["CO_IES", "NO_IES", "SG_IES"])
ies24 = pd.read_csv(IES_2024, sep=SEP, encoding="latin-1", usecols=["CO_IES", "NO_IES", "SG_IES"])

# ── Mapeamentos ───────────────────────────────────────────────────────────────
MAPA_REDE = {1: "Pública", 2: "Privada"}
MAPA_GRAU = {1: "Bacharelado", 2: "Licenciatura", 3: "Tecnólogo"}


def derivar_colunas(df):
    df = df.copy()
    # Gênero predominante (derivado de QT_ING_FEM e QT_ING_MASC)
    fem  = df["QT_ING_FEM"].fillna(0)
    masc = df["QT_ING_MASC"].fillna(0)
    total = fem + masc
    prop_fem = fem / total.replace(0, pd.NA)
    df["GENERO_PREDOM"] = pd.NA
    df.loc[prop_fem > 0.6,  "GENERO_PREDOM"] = "Feminino predominante"
    df.loc[prop_fem < 0.4,  "GENERO_PREDOM"] = "Masculino predominante"
    df.loc[(prop_fem >= 0.4) & (prop_fem <= 0.6), "GENERO_PREDOM"] = "Equilibrado"

    # ProUni total = Integral + Parcial
    col_i = "QT_ING_PROUNII" if "QT_ING_PROUNII" in df.columns else None
    col_p = "QT_ING_PROUNIP" if "QT_ING_PROUNIP" in df.columns else None
    if col_i and col_p:
        df["QT_ING_PROUNI_TOTAL"] = df[col_i].fillna(0) + df[col_p].fillna(0)
    elif col_i:
        df["QT_ING_PROUNI_TOTAL"] = df[col_i].fillna(0)

    return df


df23 = derivar_colunas(df23)
df24 = derivar_colunas(df24)


# ── Funções de agregação ──────────────────────────────────────────────────────
def agg_por(df, col_grupo, nome_col, ano):
    return (
        df.dropna(subset=[col_grupo])
        .groupby(col_grupo)["TAXA_EVASAO"]
        .agg(taxa_media="mean", n_cursos="count")
        .reset_index()
        .rename(columns={col_grupo: nome_col})
        .assign(ano=ano)
    )


def salvar(df, nome):
    path = os.path.join(OUT_DIR, nome)
    df.to_csv(path, index=False)
    print(f"  OK {nome} - {len(df)} linhas")


# ── 1. genero.csv ─────────────────────────────────────────────────────────────
print("\n[1/4] Gerando genero.csv...")
g23 = agg_por(df23, "GENERO_PREDOM", "Gênero predominante", 2023)
g24 = agg_por(df24, "GENERO_PREDOM", "Gênero predominante", 2024)
salvar(pd.concat([g23, g24], ignore_index=True), "genero.csv")

# ── 2. grau.csv ───────────────────────────────────────────────────────────────
print("[2/4] Gerando grau.csv...")
df23["Grau"] = df23["TP_GRAU_ACADEMICO"].map(MAPA_GRAU)
df24["Grau"] = df24["TP_GRAU_ACADEMICO"].map(MAPA_GRAU)
gr23 = agg_por(df23, "Grau", "Grau", 2023)
gr24 = agg_por(df24, "Grau", "Grau", 2024)
salvar(pd.concat([gr23, gr24], ignore_index=True), "grau.csv")

# ── 3. apoio.csv (FIES + ProUni) ─────────────────────────────────────────────
print("[3/4] Gerando apoio.csv...")
rows = []
for df, ano in [(df23, 2023), (df24, 2024)]:
    for col_qt, label in [("QT_ING_FIES", "FIES"), ("QT_ING_PROUNI_TOTAL", "ProUni")]:
        if col_qt not in df.columns:
            print(f"    ! Coluna {col_qt} nao encontrada - {label} ignorado")
            continue
        mask_com = df[col_qt] > 0
        rows.append({
            "Programa": label, "Situação": "Com apoio",
            "taxa_media": df.loc[mask_com, "TAXA_EVASAO"].mean(),
            "n_cursos": int(mask_com.sum()), "ano": ano,
        })
        rows.append({
            "Programa": label, "Situação": "Sem apoio",
            "taxa_media": df.loc[~mask_com, "TAXA_EVASAO"].mean(),
            "n_cursos": int((~mask_com).sum()), "ano": ano,
        })
salvar(pd.DataFrame(rows), "apoio.csv")

# ── 4. top_cursos.csv ─────────────────────────────────────────────────────────
# Agrega por Curso × Rede × Grau × Região (sem instituição).
# O app filtra por essas dimensões e depois agrega ao nível de curso para exibir.
# Dados são por polo (município) — soma todos os polos de todas as IES por grupo.
print("[4/4] Gerando top_cursos.csv...")
col_rede = "TP_REDE_y" if "TP_REDE_y" in df23.columns else "TP_REDE_x"

tops = []
for df, ano in [(df23, 2023), (df24, 2024)]:
    df_t = df.copy()
    df_t["Rede"] = df_t[col_rede].map(MAPA_REDE)

    agg = (
        df_t.groupby(["NO_CURSO", "Rede", "Grau", "NO_REGIAO_IES"])
        .agg(
            QT_ING_TOTAL=("QT_ING", "sum"),
            QT_DESV_TOTAL=("QT_SIT_DESVINCULADO", "sum"),
        )
        .reset_index()
        .assign(ano=ano)
    )
    tops.append(agg)

salvar(pd.concat(tops, ignore_index=True), "top_cursos.csv")

print("\nConcluido! Arquivos gerados em streamlit_data/")
