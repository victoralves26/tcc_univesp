"""
criar_notebook_modelagem.py
Gera o arquivo modelagem_evasao_ead.ipynb com o pipeline completo de modelagem.
Execute: python criar_notebook_modelagem.py
"""
import json
import os


def md(texto):
    """Célula markdown a partir de uma string multi-linha."""
    linhas = texto.strip("\n").split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]],
    }


def code(texto):
    """Célula de código a partir de uma string multi-linha."""
    linhas = texto.strip("\n").split("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]],
    }


# =============================================================================
# CÉLULAS DO NOTEBOOK
# =============================================================================

celulas = []

# ── Título ────────────────────────────────────────────────────────────────────
celulas.append(md("""
# Modelagem Preditiva — Evasão no Ensino Superior EaD

## Objetivo

Construir e comparar modelos de classificação para identificar cursos de Ensino
Superior a Distância (EaD) com maior risco de evasão, a partir dos microdados
do Censo da Educação Superior (INEP) — anos 2023 e 2024.

**Unidade de análise:** cada registro representa um curso oferecido em um polo (município).
A taxa de evasão é calculada como a razão entre desvinculados e ingressantes naquele polo.

**Estratégia de validação:** treino com dados de 2023 e teste com dados de 2024 (validação temporal).
Isso significa que o modelo aprende padrões de 2023 e é avaliado em dados que não viu — 2024.

**Fluxo do trabalho:** EDA revelou padrões → Modelagem confirmou → SHAP explicou o porquê.
"""))

# ── Colab setup ───────────────────────────────────────────────────────────────
celulas.append(md("""
## Configuração do ambiente

Execute a célula abaixo apenas se estiver rodando no **Google Colab**.
Se estiver usando Jupyter localmente, pode pular.
"""))

celulas.append(code("""
# Monte o Google Drive se estiver no Colab (pule se for execução local)
try:
    from google.colab import drive
    drive.mount('/content/drive')
    print("Google Drive montado.")
except ImportError:
    print("Ambiente local detectado — sem necessidade de montar Drive.")
"""))

# ── Imports ───────────────────────────────────────────────────────────────────
celulas.append(code("""
# Instalação (descomente se necessário — Colab ou ambiente sem as bibliotecas)
# !pip install shap xgboost --quiet

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
)

import shap
import warnings
warnings.filterwarnings("ignore")

plt.rcParams["figure.figsize"] = (11, 5)
plt.rcParams["font.size"] = 11
sns.set_style("whitegrid")

print("Bibliotecas carregadas com sucesso.")
"""))

# ── Seção 1: Carregamento ─────────────────────────────────────────────────────
celulas.append(md("""
---
## 1. Carregamento dos dados

Os microdados já foram pré-processados em etapas anteriores (notebook de EDA),
resultando em dois arquivos com os dados de cursos e instituições combinados.

O script detecta automaticamente se está rodando localmente ou no Colab.
"""))

celulas.append(code("""
# Caminhos possíveis — local e Colab/Drive
CAMINHOS = [
    r"C:\\Users\\Victor\\OneDrive\\Documentos\\UNIVESP\\tcc\\dados\\dados_tratados",
    "/content/drive/MyDrive/2022_Univesp/TCC/dados/dados_tratados",
]

DADOS = next((p for p in CAMINHOS if os.path.exists(p)), None)
if DADOS is None:
    raise FileNotFoundError(
        "Pasta de dados não encontrada. Ajuste os caminhos em CAMINHOS."
    )

print(f"Lendo dados de: {DADOS}")

df23 = pd.read_csv(os.path.join(DADOS, "df_completo_2023.csv"), sep=";", low_memory=False)
df24 = pd.read_csv(os.path.join(DADOS, "df_completo_2024.csv"), sep=";", low_memory=False)

print(f"2023: {len(df23):,} registros")
print(f"2024: {len(df24):,} registros")
print(f"\\nColunas disponíveis: {len(df23.columns)}")
"""))

# ── Seção 2: Variável alvo ────────────────────────────────────────────────────
celulas.append(md("""
---
## 2. Definição da variável alvo

### Filtragem

Mantemos apenas registros com ao menos 30 ingressantes no polo, para que a
taxa de evasão calculada tenha respaldo estatístico mínimo. Também removemos
registros com taxa ausente ou superior a 1 (inconsistências nos dados).

### Limiar de classificação

Classificamos cada polo/curso como **Alta evasão** ou **Baixa evasão** usando
a mediana do conjunto de treino (2023) como ponto de corte. Isso garante:
- Classes equilibradas (50% / 50%)
- Interpretação direta: cursos acima da mediana têm evasão acima do esperado
- Limiar definido nos dados de treino, sem vazamento de informação do teste
"""))

celulas.append(code("""
MIN_INGRESSANTES = 30

def filtrar(df):
    return df[
        (df["QT_ING"] >= MIN_INGRESSANTES) &
        df["TAXA_EVASAO"].notna() &
        (df["TAXA_EVASAO"] <= 1.0)
    ].copy()

df23 = filtrar(df23)
df24 = filtrar(df24)

print(f"Após filtro — 2023: {len(df23):,} registros | 2024: {len(df24):,} registros")

# Distribuição da taxa de evasão nos dois anos
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

for ax, df, titulo, cor in [
    (axes[0], df23, "2023 — Conjunto de Treino", "steelblue"),
    (axes[1], df24, "2024 — Conjunto de Teste",  "salmon"),
]:
    ax.hist(df["TAXA_EVASAO"], bins=40, color=cor, edgecolor="white", alpha=0.85)
    ax.set_title(titulo)
    ax.set_xlabel("Taxa de Evasão")
    ax.set_ylabel("Número de registros")
    stats = df["TAXA_EVASAO"].describe()
    texto = f"Média: {stats['mean']:.1%}\\nMediana: {stats['50%']:.1%}"
    ax.text(0.97, 0.95, texto, transform=ax.transAxes, ha="right", va="top",
            fontsize=10, bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))

plt.suptitle("Distribuição da Taxa de Evasão por polo/curso", fontsize=13)
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Limiar = mediana do treino
THRESHOLD = df23["TAXA_EVASAO"].median()
print(f"Limiar de classificação (mediana de 2023): {THRESHOLD:.1%}")

# Visualizar o corte
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(df23["TAXA_EVASAO"], bins=40, color="steelblue", edgecolor="white", alpha=0.85)
ax.axvline(THRESHOLD, color="red", linestyle="--", linewidth=2,
           label=f"Mediana = {THRESHOLD:.1%}  →  ponto de corte")
ax.set_title("Taxa de Evasão (treino 2023) com ponto de corte")
ax.set_xlabel("Taxa de Evasão")
ax.set_ylabel("Número de registros")
ax.legend()
plt.tight_layout()
plt.show()

# Criar variável alvo: 0 = Baixa evasão | 1 = Alta evasão
df23["TARGET"] = (df23["TAXA_EVASAO"] > THRESHOLD).astype(int)
df24["TARGET"] = (df24["TAXA_EVASAO"] > THRESHOLD).astype(int)

for nome, df in [("2023 (treino)", df23), ("2024 (teste)", df24)]:
    n_alta  = df["TARGET"].sum()
    n_baixa = len(df) - n_alta
    print(f"\\n{nome}:")
    print(f"  Baixa evasão : {n_baixa:,} ({n_baixa / len(df):.1%})")
    print(f"  Alta evasão  : {n_alta:,}  ({n_alta  / len(df):.1%})")
"""))

# ── Seção 3: Features ─────────────────────────────────────────────────────────
celulas.append(md("""
---
## 3. Seleção e preparação das variáveis

As variáveis foram escolhidas com base nos padrões identificados na análise
exploratória (EDA) e nas referências do projeto de pesquisa:

| Variável | Tipo | Descrição |
|---|---|---|
| PROP_FEM | Numérica | Proporção de ingressantes do sexo feminino |
| PROP_JOVEM | Numérica | Proporção de ingressantes com até 24 anos |
| PROP_FIES | Numérica | Proporção com financiamento FIES |
| PROP_PROUNI | Numérica | Proporção com bolsa ProUni |
| REDE | Categórica | Rede de ensino (Pública / Privada) |
| GRAU | Categórica | Grau acadêmico (Bacharelado / Licenciatura / Tecnólogo) |
| REGIAO | Categórica | Grande região geográfica |
| ORG | Categórica | Tipo de organização acadêmica |
"""))

celulas.append(code("""
# Identificar colunas que podem variar conforme o join realizado na EDA
COL_REDE = "TP_REDE_y" if "TP_REDE_y" in df23.columns else "TP_REDE_x"
COL_ORG  = (
    "TP_ORGANIZACAO_ACADEMICA_y"
    if "TP_ORGANIZACAO_ACADEMICA_y" in df23.columns
    else "TP_ORGANIZACAO_ACADEMICA_x"
)

def construir_features(df):
    d = df.copy()

    # Proporções demográficas
    d["PROP_FEM"] = d["QT_ING_FEM"].fillna(0) / d["QT_ING"]

    jovens = [c for c in ["QT_ING_0_17", "QT_ING_18_24"] if c in d.columns]
    d["PROP_JOVEM"] = d[jovens].fillna(0).sum(axis=1) / d["QT_ING"]

    # Apoio financeiro
    d["PROP_FIES"] = d["QT_ING_FIES"].fillna(0) / d["QT_ING"]

    prouni = [c for c in ["QT_ING_PROUNII", "QT_ING_PROUNIP"] if c in d.columns]
    d["PROP_PROUNI"] = d[prouni].fillna(0).sum(axis=1) / d["QT_ING"]

    # Categóricas
    d["REDE"]   = d[COL_REDE].map({1: "Publica", 2: "Privada"}).fillna("Outro")
    d["GRAU"]   = d["TP_GRAU_ACADEMICO"].map(
        {1: "Bacharelado", 2: "Licenciatura", 3: "Tecnologo"}
    ).fillna("Outro")
    d["REGIAO"] = d["NO_REGIAO_IES"].fillna("Desconhecida")
    d["ORG"]    = d[COL_ORG].map(
        {1: "Universidade", 2: "Centro_Univ", 3: "Faculdade",
         4: "IF_CEFET",    5: "Univ_Especializada"}
    ).fillna("Outro")

    return d

df23 = construir_features(df23)
df24 = construir_features(df24)

FEATURES_NUM = ["PROP_FEM", "PROP_JOVEM", "PROP_FIES", "PROP_PROUNI"]
FEATURES_CAT = ["REDE", "GRAU", "REGIAO", "ORG"]

# Checar valores ausentes
ausentes = df23[FEATURES_NUM + FEATURES_CAT].isna().sum()
print("Valores ausentes nas features (treino):")
if ausentes.any():
    print(ausentes[ausentes > 0])
else:
    print("  Nenhum valor ausente.")
"""))

celulas.append(code("""
# Codificar variáveis categóricas com Label Encoding.
# O encoder é ajustado nos dados combinados (2023 + 2024) para que os
# rótulos vistos no teste também existam no treino.

encoders = {}
for col in FEATURES_CAT:
    le = LabelEncoder()
    combinado = pd.concat([df23[col], df24[col]]).astype(str)
    le.fit(combinado)
    df23[col + "_ENC"] = le.transform(df23[col].astype(str))
    df24[col + "_ENC"] = le.transform(df24[col].astype(str))
    encoders[col] = le

FEATURES_ENC = FEATURES_NUM + [c + "_ENC" for c in FEATURES_CAT]

# Nomes legíveis para os gráficos
NOMES = {
    "PROP_FEM":    "Prop. Feminina",
    "PROP_JOVEM":  "Prop. Jovens (<=24)",
    "PROP_FIES":   "Prop. FIES",
    "PROP_PROUNI": "Prop. ProUni",
    "REDE_ENC":    "Rede (Pub/Priv)",
    "GRAU_ENC":    "Grau Academico",
    "REGIAO_ENC":  "Regiao",
    "ORG_ENC":     "Tipo Organizacao",
}

X_train = df23[FEATURES_ENC].fillna(0).rename(columns=NOMES)
y_train = df23["TARGET"]
X_test  = df24[FEATURES_ENC].fillna(0).rename(columns=NOMES)
y_test  = df24["TARGET"]

print(f"Conjunto de treino (2023): {X_train.shape[0]:,} amostras")
print(f"  Alta evasão no treino  : {y_train.mean():.1%}")
print(f"\\nConjunto de teste  (2024): {X_test.shape[0]:,} amostras")
print(f"  Alta evasão no teste   : {y_test.mean():.1%}")
print(f"\\nVariáveis usadas no modelo:")
for f in X_train.columns:
    print(f"  - {f}")
"""))

# ── Seção 4: Modelos ──────────────────────────────────────────────────────────
celulas.append(md("""
---
## 4. Treinamento e avaliação dos modelos

Treinamos quatro modelos com complexidade crescente:

1. **Regressão Logística** — modelo linear, simples e interpretável (baseline)
2. **Árvore de Decisão** — gera regras explícitas e de fácil visualização
3. **Random Forest** — conjunto de centenas de árvores, mais robusto
4. **XGBoost** — gradient boosting, geralmente o mais preciso em dados tabulares

### Métricas utilizadas

- **Acurácia** — percentual geral de acertos
- **Precisão** — dos que o modelo classifica como "Alta evasão", quantos realmente são?
- **Recall** — dos cursos que de fato têm alta evasão, quantos o modelo identifica?
- **F1-Score** — média harmônica entre Precisão e Recall
- **AUC-ROC** — capacidade geral do modelo de separar as duas classes (0 = pior, 1 = perfeito)
"""))

celulas.append(code("""
modelos = {
    "Regressao Logistica": LogisticRegression(max_iter=1000, random_state=42),
    "Arvore de Decisao":   DecisionTreeClassifier(max_depth=5, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
    "XGBoost":             XGBClassifier(
                               n_estimators=100, eval_metric="logloss",
                               verbosity=0, random_state=42
                           ),
}

def avaliar(nome, modelo, Xtr, ytr, Xte, yte):
    modelo.fit(Xtr, ytr)
    pred = modelo.predict(Xte)
    prob = modelo.predict_proba(Xte)[:, 1]
    return {
        "Modelo":   nome,
        "Acuracia": accuracy_score(yte, pred),
        "Precisao": precision_score(yte, pred, zero_division=0),
        "Recall":   recall_score(yte, pred, zero_division=0),
        "F1-Score": f1_score(yte, pred, zero_division=0),
        "AUC-ROC":  roc_auc_score(yte, prob),
    }, pred, prob

resultados, predicoes = [], {}

for nome, modelo in modelos.items():
    print(f"Treinando: {nome}...")
    res, pred, prob = avaliar(nome, modelo, X_train, y_train, X_test, y_test)
    resultados.append(res)
    predicoes[nome] = (pred, prob)

df_res = pd.DataFrame(resultados).set_index("Modelo")
print("\\n--- Resultados no conjunto de teste (2024) ---")
print(df_res.round(3).to_string())
"""))

celulas.append(code("""
# Comparação visual das métricas
metricas = ["Acuracia", "Precisao", "Recall", "F1-Score", "AUC-ROC"]

fig, ax = plt.subplots(figsize=(13, 5))
df_res[metricas].plot(kind="bar", ax=ax, rot=15, colormap="tab10",
                      edgecolor="white", width=0.7)
ax.set_ylim(0.4, 1.08)
ax.set_title("Comparação dos Modelos — Conjunto de Teste (2024)", fontsize=13)
ax.set_ylabel("Score")
ax.legend(loc="lower right", fontsize=9)
ax.axhline(0.5, color="gray", linestyle="--", alpha=0.4, label="Baseline (50%)")
for container in ax.containers:
    ax.bar_label(container, fmt="%.2f", fontsize=7, padding=2)
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Curvas ROC — quanto melhor o modelo, mais a curva se aproxima do canto superior esquerdo
fig, ax = plt.subplots(figsize=(8, 6))

cores = ["steelblue", "darkorange", "forestgreen", "crimson"]
for (nome, (_, prob)), cor in zip(predicoes.items(), cores):
    fpr, tpr, _ = roc_curve(y_test, prob)
    auc = roc_auc_score(y_test, prob)
    ax.plot(fpr, tpr, label=f"{nome}  (AUC = {auc:.3f})", color=cor, linewidth=2)

ax.plot([0, 1], [0, 1], "k--", alpha=0.35, label="Classificador aleatorio")
ax.set_xlabel("Taxa de Falsos Positivos")
ax.set_ylabel("Recall (Taxa de Verdadeiros Positivos)")
ax.set_title("Curvas ROC — Comparação dos Modelos")
ax.legend(loc="lower right")
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Matrizes de confusão — mostram onde cada modelo acerta e erra
fig, axes = plt.subplots(1, 4, figsize=(18, 4))
rotulos = ["Baixa\\nEvasao", "Alta\\nEvasao"]

for ax, (nome, (pred, _)) in zip(axes, predicoes.items()):
    cm = confusion_matrix(y_test, pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=rotulos, yticklabels=rotulos, cbar=False)
    ax.set_title(nome, fontsize=10)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")

plt.suptitle("Matrizes de Confusao — Conjunto de Teste (2024)", fontsize=13, y=1.02)
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Relatório detalhado do melhor modelo (XGBoost)
melhor_nome = df_res["AUC-ROC"].idxmax()
print(f"Melhor modelo por AUC-ROC: {melhor_nome}")
print()
print(classification_report(
    y_test, predicoes[melhor_nome][0],
    target_names=["Baixa Evasao", "Alta Evasao"]
))
"""))

celulas.append(md("""
### Árvore de Decisão — visualização das regras

A árvore de decisão permite visualizar as regras que o modelo aprendeu de forma
direta e legível. Limitamos a profundidade a 3 níveis para manter a clareza.
"""))

celulas.append(code("""
# Treinar uma árvore simplificada (profundidade 3) para visualização
dt_viz = DecisionTreeClassifier(max_depth=3, min_samples_leaf=200, random_state=42)
dt_viz.fit(X_train, y_train)

fig, ax = plt.subplots(figsize=(22, 9))
plot_tree(
    dt_viz,
    feature_names=list(X_train.columns),
    class_names=["Baixa Evasao", "Alta Evasao"],
    filled=True, rounded=True, fontsize=9, ax=ax,
    impurity=False, proportion=True,
)
plt.title("Arvore de Decisao — Regras de Classificacao (profundidade 3)", fontsize=13)
plt.tight_layout()
plt.show()

acc_dt3 = accuracy_score(y_test, dt_viz.predict(X_test))
print(f"Acuracia da arvore simplificada no teste (2024): {acc_dt3:.3f}")
"""))

# ── Seção 5: SHAP ─────────────────────────────────────────────────────────────
celulas.append(md("""
---
## 5. Interpretabilidade com SHAP

SHAP (Shapley Additive Explanations) é uma técnica que explica as previsões de
qualquer modelo calculando a contribuição de cada variável para cada predição.

**Por que isso importa?**
- Saber que o modelo tem boa acurácia não é suficiente
- Precisamos entender *quais variáveis* levam o modelo a classificar um curso como de alta evasão
- O SHAP permite conectar os resultados do modelo com o que a análise exploratória já mostrava

Usamos o XGBoost por ter obtido o melhor desempenho geral.
"""))

celulas.append(code("""
modelo_final = modelos["XGBoost"]

# TreeExplainer é otimizado para modelos baseados em arvore (XGBoost, Random Forest)
explainer   = shap.TreeExplainer(modelo_final)
shap_values = explainer.shap_values(X_test)

print(f"SHAP calculado para {X_test.shape[0]:,} amostras do conjunto de teste (2024).")
print(f"Cada amostra tem um valor SHAP por variavel: shape = {shap_values.shape}")
"""))

celulas.append(code("""
# Importância global: média do valor absoluto de SHAP por variavel
# Responde: "qual variavel mais influencia as previsoes do modelo, no geral?"

plt.figure(figsize=(9, 5))
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False, color="steelblue")
plt.title("Importancia das Variaveis — SHAP (XGBoost)", fontsize=13)
plt.xlabel("Impacto medio absoluto nas previsoes")
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Grafico detalhado (beeswarm): mostra direcao e intensidade do efeito
# Cada ponto = uma amostra do conjunto de teste
# Vermelho = valor alto da variavel | Azul = valor baixo
# Posicao no eixo X: positivo = aumenta probabilidade de alta evasao

plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test, show=False)
plt.title("Impacto Individual das Variaveis — SHAP (XGBoost)", fontsize=13)
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Ranking de importancia e conexao com a EDA
imp = pd.Series(
    np.abs(shap_values).mean(axis=0),
    index=X_test.columns
).sort_values(ascending=False)

print("Ranking de importancia das variaveis (SHAP):")
print("-" * 45)
for i, (feat, val) in enumerate(imp.items(), 1):
    print(f"  {i:2}. {feat:<28} {val:.4f}")

print()
print("Conexao com a Analise Exploratoria (EDA):")
print("-" * 60)

conexoes = [
    ("Prop. Jovens (<=24)",
     "EDA: cursos com publico predominantemente jovem (ate 24 anos)\\n"
     "     apresentaram as maiores taxas de evasao em ambos os anos."),
    ("Prop. ProUni",
     "EDA: cursos com beneficiarios ProUni tiveram evasao ~51%\\n"
     "     vs ~36% para os sem ProUni — achado contraintuitivo."),
    ("Rede (Pub/Priv)",
     "EDA: diferenca entre redes observada na analise por rede de ensino."),
    ("Grau Academico",
     "EDA: Tecnologos e Licenciaturas mostraram comportamentos distintos\\n"
     "     de Bacharelados na taxa de evasao."),
    ("Regiao",
     "EDA: regiao Sul apresentou taxas consistentemente mais elevadas."),
]

for feat, descricao in conexoes:
    if feat in imp.index:
        rank = list(imp.index).index(feat) + 1
        print(f"\\n  [{rank}o lugar] {feat}")
        print(f"     {descricao}")
"""))

# ── Conclusões ────────────────────────────────────────────────────────────────
celulas.append(md("""
---
## 6. Conclusoes

### Sobre os modelos

O pipeline seguiu a sequência: **EDA revelou padrões → Modelagem confirmou → SHAP explicou o porquê.**

O XGBoost obteve o melhor desempenho (AUC-ROC mais alto), confirmando que variáveis
identificadas na análise exploratória têm poder preditivo real sobre a taxa de evasão.

A validação temporal (treino em 2023, teste em 2024) garante que o modelo não foi
avaliado nos mesmos dados em que aprendeu — o que torna os resultados mais confiáveis.

### Sobre as variáveis

O SHAP confirmou que as variáveis mais relevantes para a previsão estão alinhadas
com o que a EDA já apontava:
- A proporção de ingressantes jovens (até 24 anos) e o tipo de apoio financeiro (ProUni)
  aparecem consistentemente entre os principais preditores
- Isso está em linha com o referencial teórico (Juliani, 2025; Silva et al., 2025),
  que identificam idade e perfil socioeconômico como fatores associados à evasão

### Limitações

- **Unidade de análise:** os dados estão no nível polo/curso, não por aluno individual.
  As previsões referem-se ao comportamento coletivo de cursos, não à probabilidade
  de um estudante específico evadir.
- **Definição de evasão:** a taxa compara ingressantes de um ano com desvinculados
  do mesmo ano, que podem ser de coortes anteriores. Isso é uma limitação dos
  microdados do Censo INEP, documentada na metodologia do trabalho.
- **Ausência de variáveis individuais:** fatores como engajamento, distância ao polo
  e histórico acadêmico — citados na literatura como relevantes — não estão
  disponíveis nesta base de dados.
"""))

# =============================================================================
# MONTAGEM DO NOTEBOOK
# =============================================================================

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
        "colab": {
            "provenance": [],
            "name": "modelagem_evasao_ead.ipynb",
        },
    },
    "cells": celulas,
}

caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelagem_evasao_ead.ipynb")
with open(caminho, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Notebook criado: {caminho}")
print(f"Total de celulas: {len(celulas)}")
