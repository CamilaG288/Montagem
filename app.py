import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Painel de Montagem", layout="wide")
st.title("\U0001F527 Painel de Montagem de Turbos")

# URLs dos arquivos do GitHub
URL_ESTRUTURA = "https://github.com/CamilaG288/Turbos_montaveis/raw/main/ESTRUTURAS.xlsx"
URL_ESTOQUE = "https://github.com/CamilaG288/Turbos_montaveis/raw/main/ALMOX102.xlsx"
URL_CURVA = "https://github.com/CamilaG288/Turbos_montaveis/raw/main/CURVA%20ABC.xlsx"
URL_PEDIDOS = "https://github.com/CamilaG288/Turbos_montaveis/raw/main/PEDIDOS.xlsx"

# Função para converter DataFrame em Excel

def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Carregamento com cache
@st.cache_data

def carregar_dados():
    estrutura = pd.read_excel(URL_ESTRUTURA)
    estoque = pd.read_excel(URL_ESTOQUE)
    curva = pd.read_excel(URL_CURVA)
    pedidos = pd.read_excel(URL_PEDIDOS)
    return estrutura, estoque, curva, pedidos

estrutura, estoque, curva, pedidos = carregar_dados()

# Padronização de colunas
estrutura.columns = estrutura.columns.str.strip()
estoque.columns = estoque.columns.str.strip()
curva.columns = curva.columns.str.strip()
pedidos.columns = pedidos.columns.str.strip()

# Dicionário da estrutura (pai -> [(filho, qtd)])
def montar_estrutura(df):
    estrutura_dict = {}
    for _, row in df.iterrows():
        pai = str(row['Produto']).strip()
        comp = str(row['Componente']).strip()
        qtd = row['Quantidade']
        estrutura_dict.setdefault(pai, []).append((comp, qtd))
    return estrutura_dict

estrutura_dict = montar_estrutura(estrutura)

# Dicionário de estoque
estoque_dict = dict(zip(estoque['Produto'].astype(str).str.strip(), estoque['Qtde Atual']))

# Reservar componentes para os pedidos
reservas = {}
pedidos_ordenados = pedidos.sort_values(by='Data Prevista')

for _, row in pedidos_ordenados.iterrows():
    produto = str(row['Descricao']).strip()
    qtd_produzir = row['Produzir']

    if produto not in estrutura_dict:
        continue

    pode_atender = True
    necessidade = {}

    for comp, qtd_comp in estrutura_dict[produto]:
        total_necessario = qtd_produzir * qtd_comp
        disponivel = estoque_dict.get(comp, 0)

        if disponivel < total_necessario:
            pode_atender = False
            break

        necessidade[comp] = total_necessario

    if pode_atender:
        for comp, total in necessidade.items():
            estoque_dict[comp] -= total
        reservas[produto] = reservas.get(produto, 0) + qtd_produzir

# Montagens com estoque restante via Curva ABC
montados_abc = {}
curva_ordenada = curva.sort_values(by='SEQUENCIA')

for _, row in curva_ordenada.iterrows():
    produto = str(row['Produto']).strip()
    max_montar = float('inf')

    if produto not in estrutura_dict:
        continue

    for comp, qtd_comp in estrutura_dict[produto]:
        disponivel = estoque_dict.get(comp, 0)
        if qtd_comp > 0:
            max_montar = min(max_montar, disponivel // qtd_comp)

    if max_montar > 0 and max_montar != float('inf'):
        for comp, qtd_comp in estrutura_dict[produto]:
            estoque_dict[comp] -= qtd_comp * max_montar
        montados_abc[produto] = int(max_montar)

# Exibição dos resultados
st.subheader("\U0001F4CB Pedidos Atendidos")
df_reservas = pd.DataFrame([{'Produto': k, 'Qtde Atendida': v} for k, v in reservas.items()])
st.dataframe(df_reservas)
st.download_button("\U0001F4BE Baixar Pedidos Atendidos", to_excel_bytes(df_reservas), file_name="pedidos_atendidos.xlsx")

st.subheader("\U0001F9F0 Montagens com Estoque Restante (Curva ABC)")
df_abc = pd.DataFrame([{'Produto': k, 'Qtde Montada': v} for k, v in montados_abc.items()])
st.dataframe(df_abc)
st.download_button("\U0001F4BE Baixar Montagens ABC", to_excel_bytes(df_abc), file_name="montagem_curva_abc.xlsx")
