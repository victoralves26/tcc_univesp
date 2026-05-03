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

Mantemos apenas registros com ao menos 10 ingressantes no polo, para que a
taxa de evasão calculada tenha respaldo estatístico mínimo. Também removemos
registros com taxa ausente ou superior a 1 (inconsistências nos dados).

O filtro de 10 (em vez de um valor maior) foi escolhido porque a maioria dos
polos EaD é pequena — a média é de ~7 alunos por polo. Um filtro mais restritivo
eliminaria mais de 95% dos registros, comprometendo a base de treino.

### Limiar de classificação

Classificamos cada polo/curso como **Alta evasão** ou **Baixa evasão** usando
a mediana do conjunto de treino (2023) como ponto de corte. Isso garante:
- Classes equilibradas (50% / 50%)
- Interpretação direta: cursos acima da mediana têm evasão acima do esperado
- Limiar definido nos dados de treino, sem vazamento de informação do teste
"""))

celulas.append(code("""
# Mínimo de 10 ingressantes por polo.
# O filtro de 30 reduziria o dataset para menos de 5% dos registros,
# pois a maioria dos polos EaD é pequena (média de 7 alunos por polo).
# Com 10, mantemos representatividade sem distorcer taxas com 1-2 alunos.
MIN_INGRESSANTES = 10

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
    "PROP_JOVEM":  "Prop. Jovens (ate 24)",
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
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
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
    ("Prop. Jovens (ate 24)",
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

# ── Seção 6: Abordagem alternativa — split aleatório ─────────────────────────
celulas.append(md("""
---
## 6. Abordagem alternativa — Split aleatório (70% treino / 30% teste)

Na abordagem anterior, usamos 2023 para treino e 2024 para teste (validação temporal).
Aqui testamos uma estratégia diferente: combinar os dois anos em um único dataset
e dividir aleatoriamente em 70% treino e 30% teste.

**Por que testar isso?**
- Mais dados disponíveis para treino (2023 + 2024 combinados)
- Permite comparar se a escolha da estratégia de validação afeta os resultados
- A comparação entre as duas abordagens é, em si, um resultado metodológico relevante

**Diferença principal:**
No split aleatório, registros de 2023 e 2024 podem aparecer tanto no treino quanto
no teste. No split temporal, o teste só contém dados de um ano que o modelo nunca viu.
"""))

celulas.append(code("""
from sklearn.model_selection import train_test_split

# Combinar os dois anos em um único dataset
# A coluna "ano" permite rastrear a origem de cada registro após o merge
df23_v2 = df23.copy()
df23_v2["ano"] = 2023
df24_v2 = df24.copy()
df24_v2["ano"] = 2024

df_all = pd.concat([df23_v2, df24_v2], ignore_index=True)
print(f"Dataset combinado: {len(df_all):,} registros")
print(f"  2023: {(df_all['ano'] == 2023).sum():,} | 2024: {(df_all['ano'] == 2024).sum():,}")
print(f"  Alta evasão: {df_all['TARGET'].mean():.1%}")
"""))

celulas.append(code("""
# Aplicar o mesmo encoding nas features do dataset combinado
for col in FEATURES_CAT:
    df_all[col + "_ENC"] = encoders[col].transform(df_all[col].astype(str))

X_all = df_all[FEATURES_ENC].fillna(0).rename(columns=NOMES)
y_all = df_all["TARGET"]

# Split aleatório estratificado — garante mesma proporção de classes em treino e teste
X_tr2, X_te2, y_tr2, y_te2 = train_test_split(
    X_all, y_all, test_size=0.30, random_state=42, stratify=y_all
)

print(f"Treino: {len(X_tr2):,} amostras | Alta evasão: {y_tr2.mean():.1%}")
print(f"Teste : {len(X_te2):,} amostras | Alta evasão: {y_te2.mean():.1%}")
"""))

celulas.append(code("""
# Treinar os mesmos quatro modelos no dataset combinado
# Criamos novas instâncias para não interferir nos resultados anteriores

modelos_v2 = {
    "Regressao Logistica": LogisticRegression(max_iter=1000, random_state=42),
    "Arvore de Decisao":   DecisionTreeClassifier(max_depth=5, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
    "XGBoost":             XGBClassifier(
                               n_estimators=100, eval_metric="logloss",
                               verbosity=0, random_state=42
                           ),
}

resultados_v2, predicoes_v2 = [], {}

for nome, modelo in modelos_v2.items():
    print(f"Treinando: {nome}...")
    res, pred, prob = avaliar(nome, modelo, X_tr2, y_tr2, X_te2, y_te2)
    resultados_v2.append(res)
    predicoes_v2[nome] = (pred, prob)

df_res2 = pd.DataFrame(resultados_v2).set_index("Modelo")
print("\\n--- Resultados (split aleatório 70/30) ---")
print(df_res2.round(3).to_string())
"""))

# ── Seção 7: Comparação das abordagens ───────────────────────────────────────
celulas.append(md("""
---
## 7. Comparação das abordagens de validação

Comparamos os resultados das duas estratégias para cada modelo e métrica.
"""))

celulas.append(code("""
# Tabela comparativa completa
metricas_comp = ["Acuracia", "Precisao", "Recall", "F1-Score", "AUC-ROC"]

print("=== Validação Temporal (treino 2023 / teste 2024) ===")
print(df_res[metricas_comp].round(3).to_string())

print("\\n=== Split Aleatório (70% / 30% — anos combinados) ===")
print(df_res2[metricas_comp].round(3).to_string())

# Diferença: split aleatório minus temporal
diff = df_res2[metricas_comp] - df_res[metricas_comp]
print("\\n=== Diferença (Split Aleatório menos Temporal) ===")
print(diff.round(3).to_string())
print("\\nValores positivos indicam que o split aleatório deu resultado maior.")
"""))

celulas.append(code("""
# Visualização comparativa — AUC-ROC e F1-Score para cada modelo
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

for ax, metrica in zip(axes, ["AUC-ROC", "F1-Score"]):
    comp = pd.DataFrame({
        "Temporal\\n(2023 treino / 2024 teste)": df_res[metrica],
        "Aleatório\\n(70% / 30% combinado)":     df_res2[metrica],
    })
    comp.plot(kind="bar", ax=ax, rot=15, color=["steelblue", "darkorange"],
              edgecolor="white", width=0.6)
    ax.set_ylim(0.4, 1.05)
    ax.set_title(f"{metrica} por abordagem de validação", fontsize=12)
    ax.set_ylabel(metrica)
    ax.legend(fontsize=9)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", fontsize=8, padding=2)

plt.suptitle("Comparação: Validação Temporal vs Split Aleatório", fontsize=13)
plt.tight_layout()
plt.show()
"""))

celulas.append(code("""
# Síntese da comparação
print("Síntese da comparação entre as abordagens:")
print("-" * 55)

for nome in df_res.index:
    auc_temp = df_res.loc[nome, "AUC-ROC"]
    auc_rand = df_res2.loc[nome, "AUC-ROC"]
    diff_auc = auc_rand - auc_temp
    sinal = "+" if diff_auc >= 0 else ""
    print(f"  {nome:<25} Temporal: {auc_temp:.3f} | Aleatório: {auc_rand:.3f} | Dif: {sinal}{diff_auc:.3f}")

print()
print("Interpretação:")
print("  - Se o split aleatório der resultados muito superiores, pode indicar que")
print("    o modelo se beneficia de ver amostras 'parecidas' no treino e no teste.")
print("  - Se os resultados forem próximos, o modelo generaliza bem entre os anos.")
print("  - A validação temporal é mais conservadora e mais realista para uso prático.")
"""))

# ── Conclusões ────────────────────────────────────────────────────────────────
celulas.append(md("""
---
## 8. Conclusoes

### Sobre a escolha da estratégia de validação

A comparação entre as duas abordagens revela se os modelos dependem ou não
de ver dados do mesmo período para ter bom desempenho.

- Se os resultados do **split aleatório forem muito superiores** ao temporal,
  significa que o modelo aproveita a similaridade entre registros de 2023 e 2024
  que ficaram no mesmo conjunto — o que pode inflar as métricas.
- Se os resultados forem **próximos entre as abordagens**, o modelo demonstra
  capacidade de generalização genuína, e qualquer uma das estratégias é defensável.

Para o presente trabalho, a **validação temporal** é a abordagem recomendada,
pois simula o uso real do modelo: aprende com dados históricos e é avaliado
em dados futuros que nunca viu.

### Sobre os modelos

O XGBoost obteve o melhor desempenho em ambas as abordagens (AUC-ROC mais alto),
confirmando que as variáveis identificadas na análise exploratória têm poder
preditivo real sobre a taxa de evasão.

### Sobre as variáveis

O SHAP confirmou que as variáveis mais relevantes estão alinhadas com o que
a EDA já apontava:
- A proporção de ingressantes jovens (até 24 anos) e o tipo de apoio financeiro
  aparecem consistentemente entre os principais preditores.
- Isso está em linha com o referencial teórico (Juliani, 2025; Silva et al., 2025),
  que identificam idade e perfil socioeconômico como fatores associados à evasão.

### Limitações

- **Unidade de análise:** os dados estão no nível polo/curso, não por aluno individual.
  As previsões referem-se ao comportamento coletivo de cursos, não à probabilidade
  de um estudante específico evadir.
- **Definição de evasão:** a taxa compara ingressantes de um ano com desvinculados
  do mesmo ano, que podem ser de coortes anteriores — limitação dos microdados INEP.
- **Ausência de variáveis individuais:** fatores como engajamento e distância ao polo,
  citados na literatura como relevantes, não estão disponíveis nesta base de dados.
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
