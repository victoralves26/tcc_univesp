import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="TCC - Evasão EaD", layout="wide")

st.title("📊 Análise de Evasão no Ensino Superior a Distância")
st.markdown("### Comparação entre os anos de 2023 e 2024")
st.markdown("---")

# ==========================================
# CARREGAR DADOS (com cache para não recarregar toda hora)
# ==========================================
@st.cache_data
def carregar_dados(url, nome):
    """Carrega CSV diretamente do Google Drive"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(BytesIO(response.content), sep=';', encoding='utf-8-sig')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {nome}: {e}")
        return None

# URLs diretas
url_2023 = 'https://drive.google.com/uc?export=download&id=1LSrqZinGmmRFn20S8vUF449t4wQmfjT7'
url_2024 = 'https://drive.google.com/uc?export=download&id=1utCj6vZg1LBfWqXNBoCYCdaJFMrMQAwR'

# Carregar
df_2023 = carregar_dados(url_2023, "2023")
df_2024 = carregar_dados(url_2024, "2024")

if df_2023 is not None and df_2024 is not None:
    st.success(f"✅ Dados carregados! 2023: {df_2023.shape[0]:,} registros | 2024: {df_2024.shape[0]:,} registros")
else:
    st.stop()

# ==========================================
# VISUALIZAÇÃO RÁPIDA
# ==========================================
with st.expander("🔍 Ver primeiras linhas dos dados"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2023")
        st.dataframe(df_2023.head())
    with col2:
        st.subheader("2024")
        st.dataframe(df_2024.head())

# ==========================================
# AQUI VOCÊ INSERE OS GRÁFICOS (QUE VAMOS MONTAR DEPOIS)
# ==========================================
st.markdown("---")
st.subheader("📈 Análises")

# Por enquanto, vamos testar se os dados carregaram corretamente
st.write("Taxa média de evasão 2023:", f"{df_2023['TAXA_EVASAO'].mean():.2%}")
st.write("Taxa média de evasão 2024:", f"{df_2024['TAXA_EVASAO'].mean():.2%}")
