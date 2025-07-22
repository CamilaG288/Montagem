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
    df.columns = df.columns.str.strip()
    for _, row in df.iterrows():
        pai = str(row['Produto']).strip()
        comp = str(row['Componente']).strip()
        qtd = row['Quantidade']
        if pai not in estrutura:
            estrutura[pai] = []
        estrutura[pai].append((comp, qtd))
    return estrutura

# Função para reservar componentes do estoque para os pedidos
def reservar_para_pedidos(pedidos_df, estrutura_dict, estoque_df):
    reservas = []
    estoque_df.columns = estoque_df.columns.str.strip().str.upper()
    cod_cols = [col for col in estoque_df.columns if 'COD' in col]
    qtd_cols = [col for col in estoque_df.columns if 'QTDE' in col or 'DISP' in col]
    if not cod_cols or not qtd_cols:
        raise ValueError("Colunas 'COD' ou 'QTDE DISP' não encontradas no estoque.")
    estoque_df = estoque_df.rename(columns={cod_cols[0]: 'COD', qtd_cols[0]: 'QTDE DISP'})
    estoque = estoque_df.set_index('COD').copy()

    for _, pedido in pedidos_df.iterrows():
        cod_produto = str(pedido['Produto']).strip()
        qtd_produzir = pedido['Produzir']
        if cod_produto not in estrutura_dict:
            continue
        pode_atender = True
        for comp, qtd_comp in estrutura_dict[cod_produto]:
            qtd_total = qtd_comp * qtd_produzir
            if comp not in estoque.index or estoque.at[comp, 'QTDE DISP'] < qtd_total:
                pode_atender = False
                break
        if pode_atender:
            for comp, qtd_comp in estrutura_dict[cod_produto]:
                qtd_total = qtd_comp * qtd_produzir
                estoque.at[comp, 'QTDE DISP'] -= qtd_total
            reservas.append({**pedido, 'Status': 'Reservado'})
        else:
            reservas.append({**pedido, 'Status': 'Estoque insuficiente'})

    return pd.DataFrame(reservas), estoque.reset_index()

# Função para montar com saldo e curva ABC
def montar_com_estoque_restante(curva_df, estrutura_dict, estoque_df):
    resultados = []
    estoque_df.columns = estoque_df.columns.str.strip().str.upper()
    cod_cols = [col for col in estoque_df.columns if 'COD' in col]
    qtd_cols = [col for col in estoque_df.columns if 'QTDE' in col or 'DISP' in col]
    if not cod_cols or not qtd_cols:
        raise ValueError("Colunas 'COD' ou 'QTDE DISP' não encontradas no estoque.")
    estoque_df = estoque_df.rename(columns={cod_cols[0]: 'COD', qtd_cols[0]: 'QTDE DISP'})
    estoque = estoque_df.set_index('COD').copy()

    for _, linha in curva_df.iterrows():
        cod_produto = str(linha['COD']).strip()
        max_montar = float('inf')
        if cod_produto not in estrutura_dict:
            continue
        for comp, qtd_comp in estrutura_dict[cod_produto]:
            if comp not in estoque.index or estoque.at[comp, 'QTDE DISP'] <= 0:
                max_montar = 0
                break
            max_montar = min(max_montar, estoque.at[comp, 'QTDE DISP'] // qtd_comp)
        if max_montar > 0:
            for comp, qtd_comp in estrutura_dict[cod_produto]:
                estoque.at[comp, 'QTDE DISP'] -= qtd_comp * max_montar
            resultados.append({'Produto': cod_produto, 'Qtd Montar': int(max_montar)})
    return pd.DataFrame(resultados)

# Carregar os dados
with st.spinner("🔄 Carregando dados..."):
    estrutura_df = pd.read_excel(URL_ESTRUTURA)
    curva_df = pd.read_excel(URL_CURVA)
    estoque_df = pd.read_excel(URL_ESTOQUE)
    pedidos_df = pd.read_excel(URL_PEDIDOS)

# Montar estrutura pai-filho
estrutura_dict = montar_estrutura(estrutura_df)

st.success("✅ Dados carregados com sucesso!")
st.subheader("📋 Estrutura de Produto")
st.write(list(estrutura_dict.items())[:1])

# Reservar para pedidos
st.subheader("📦 Reservas para Pedidos")
reservas_df, estoque_atualizado = reservar_para_pedidos(pedidos_df, estrutura_dict, estoque_df)
st.dataframe(reservas_df)

# Montagem com saldo
st.subheader("⚙️ Montagem com Saldo (Curva ABC)")
montagem_df = montar_com_estoque_restante(curva_df, estrutura_dict, estoque_atualizado)
st.dataframe(montagem_df)

# Baixar resultados
st.subheader("⬇️ Baixar Resultados")
reserva_excel = reservas_df.to_excel(index=False)
montagem_excel = montagem_df.to_excel(index=False)
st.download_button("Baixar Reservas", data=reserva_excel, file_name="reservas.xlsx")
st.download_button("Baixar Montagem", data=montagem_excel, file_name="montagem_curva_abc.xlsx")
