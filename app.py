import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Painel de Montagem", layout="wide")
st.title("🔧 Painel de Montagem de Turbos")

# URLs dos arquivos no GitHub
URL_ESTRUTURA = "https://github.com/CamilaG288/Montagem/raw/main/ESTRUTURAS.xlsx"
URL_CURVA = "https://github.com/CamilaG288/Montagem/raw/main/CURVA%20ABC.xlsx"
URL_ESTOQUE = "https://github.com/CamilaG288/Montagem/raw/main/ALMOX102.xlsx"
URL_PEDIDOS = "https://github.com/CamilaG288/Montagem/raw/main/PEDIDOS.xlsx"

# Função para montar o dicionário de estrutura
@st.cache_data

def montar_estrutura(df):
    estrutura = {}
    df.columns = df.columns.str.strip()  # Remove espaços das colunas
    for _, row in df.iterrows():
        pai = str(row['Produto']).strip()
        col_componente = [col for col in df.columns if 'componente' in col.lower()]
        comp = str(row[col_componente[0]]).strip() if col_componente else ''
        qtd = row['Quantidade']
        if pai not in estrutura:
            estrutura[pai] = []
        estrutura[pai].append((comp, qtd))
    return estrutura

# Carregar os dados
with st.spinner("🔄 Carregando dados..."):
    estrutura_df = pd.read_excel(URL_ESTRUTURA)
    curva_df = pd.read_excel(URL_CURVA)
    estoque_df = pd.read_excel(URL_ESTOQUE)
    pedidos_df = pd.read_excel(URL_PEDIDOS)

# Montar estrutura pai-filho
estrutura_dict = montar_estrutura(estrutura_df)

st.success("✅ Dados carregados com sucesso!")
st.write("Exemplo de estrutura de produto:")
st.write(list(estrutura_dict.items())[:1])
