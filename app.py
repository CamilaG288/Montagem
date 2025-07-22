import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

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

# Função para reservar componentes do estoque para os pedidos (com reserva parcial)
def reservar_para_pedidos(pedidos_df, estrutura_dict, estoque_df):
    reservas = []
    estoque_df = estoque_df.rename(columns={
        'Produto': 'COD',
        'Qtde Atual': 'QTDE DISP'
    })
    estoque = estoque_df.set_index('COD').copy()

    for _, pedido in pedidos_df.iterrows():
        cod_produto = str(pedido['Produto']).strip()
        qtd_produzir = pedido['Produzir']
        if cod_produto not in estrutura_dict:
            continue

        status = "Reservado"
        componentes_reservados = []
        for comp, qtd_comp in estrutura_dict[cod_produto]:
            qtd_total = qtd_comp * qtd_produzir
            if comp in estoque.index and estoque.at[comp, 'QTDE DISP'] >= qtd_total:
                componentes_reservados.append((comp, qtd_total))
            elif comp in estoque.index and estoque.at[comp, 'QTDE DISP'] > 0:
                componentes_reservados.append((comp, estoque.at[comp, 'QTDE DISP']))
                status = "Reservado Parcialmente"
            else:
                status = "Reservado Parcialmente" if componentes_reservados else "Não Reservado"

        for comp, qtd in componentes_reservados:
            estoque.at[comp, 'QTDE DISP'] -= qtd

        reservas.append({
            'Cliente': pedido['Cliente'],
            'Nome': pedido['Nome'],
            'Tp.Doc': pedido['Tp.Doc'],
            'Pedido': pedido['Pedido'],
            'Produto': pedido['Produto'],
            'Descricao': pedido['Descricao'],
            'Qtde Abe. Pronta': pedido['Qtde. Abe'],
            'Produzir': pedido['Produzir'],
            'Status': status
        })

    return pd.DataFrame(reservas), estoque.reset_index()

# Função para montar com saldo e curva ABC
def montar_com_estoque_restante(curva_df, estrutura_dict, estoque_df):
    resultados = []
    estoque_df = estoque_df.rename(columns={
        'Produto': 'COD',
        'Qtde Atual': 'QTDE DISP'
    })
    estoque = estoque_df.set_index('COD').copy()

    for _, linha in curva_df.iterrows():
        cod_produto = str(linha['Produto']).strip()
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
reserva_buffer = BytesIO()
montagem_buffer = BytesIO()
reservas_df.to_excel(reserva_buffer, index=False)
montagem_df.to_excel(montagem_buffer, index=False)
reserva_buffer.seek(0)
montagem_buffer.seek(0)
st.download_button("Baixar Reservas", data=reserva_buffer, file_name="reservas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("Baixar Montagem", data=montagem_buffer, file_name="montagem_curva_abc.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
