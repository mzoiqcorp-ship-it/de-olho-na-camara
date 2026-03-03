import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="De Olho na Câmara", page_icon="🔎", layout="wide")

st.title("🔎 De Olho na Câmara")
st.markdown("### Monitor Automático de Gastos Parlamentares")

# 2. LISTA DE "ALVOS" PARA O TOP 5 (Deputados que mais movimentam a cota)
# Coloquei IDs conhecidos por gastar muito para o sistema ser rápido
LISTA_ALVOS = [
    74328, 204528, 204507, 178887, 141450, 160511, 178957, 178901, 133439, 178881,
    204554, 204421, 178996, 178927, 178937, 178882, 204507, 204454, 204465, 204471
]

@st.cache_data(ttl=3600)
def buscar_ranking_automatico():
    ranking = []
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    # Busca o nome dos deputados da lista
    url_deps = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    all_deps = requests.get(url_deps).json()['dados']
    dict_nomes = {d['id']: d['nome'] for d in all_deps if d['id'] in LISTA_ALVOS}

    for id_dep in LISTA_ALVOS:
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}/despesas?ano={ano_atual}&mes={mes_atual}&ordem=DESC"
        res = requests.get(url).json()
        if res['dados']:
            total = sum(d['valorDocumento'] for d in res['dados'])
            ranking.append({"nome": dict_nomes.get(id_dep, "Desconhecido"), "total": total, "id": id_dep})
    
    return sorted(ranking, key=lambda x: x['total'], reverse=True)[:5]

# 3. INTERFACE DO TOP 5 AUTOMÁTICO
st.subheader(f"🔥 Top 5 Maiores Gastos de {datetime.now().strftime('%B/%Y')}")
st.caption("Valores somados automaticamente do mês atual.")

with st.spinner("Calculando ranking em tempo real..."):
    top_5 = buscar_ranking_automatico()

if top_5:
    cols = st.columns(5)
    for i, dep_top in enumerate(top_5):
        with cols[i]:
            st.metric(label=dep_top['nome'], value=f"R$ {dep_top['total']:,.2f}")
            if st.button(f"Ver Detalhes", key=f"btn_{dep_top['id']}"):
                st.session_state.dep_id = dep_top['id']
                st.session_state.dep_nome = dep_top['nome']

st.markdown("---")

# 4. BUSCA MANUAL (Sua ferramenta original)
st.subheader("🕵️ Busca Manual por Estado")

@st.cache_data
def get_all_deps():
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    return pd.DataFrame(requests.get(url).json()['dados'])

df_all = get_all_deps()
df_all['Busca'] = df_all['nome'] + " - " + df_all['siglaPartido'] + "/" + df_all['siglaUf']

col1, col2 = st.columns(2)
with col1:
    uf = st.selectbox("Estado:", ["Todos"] + sorted(list(df_all['siglaUf'].unique())))
with col2:
    lista_final = df_all if uf == "Todos" else df_all[df_all['siglaUf'] == uf]
    selecionado = st.selectbox("Político:", ["Selecione..."] + list(lista_final['Busca']))

# 5. MOSTRAR TABELA
dep_id_final = None
if selecionado != "Selecione...":
    dep_id_final = df_all[df_all['Busca'] == selecionado]['id'].values[0]
elif 'dep_id' in st.session_state:
    dep_id_final = st.session_state.dep_id

if dep_id_final:
    url_despesas = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{dep_id_final}/despesas?ordem=DESC&itens=100"
    res_d = requests.get(url_despesas).json()
    if res_d['dados']:
        df_d = pd.DataFrame(res_d['dados'])[['dataDocumento', 'tipoDespesa', 'nomeFornecedor', 'valorDocumento', 'urlDocumento']]
        df_d.columns = ['Data', 'Tipo', 'Fornecedor', 'Valor (R$)', 'Nota Fiscal']
        st.dataframe(df_d.sort_values(by="Valor (R$)", ascending=False), use_container_width=True)

# BARRA LATERAL
st.sidebar.header("🚀 Apoie o Projeto")
st.sidebar.write("Ajude a manter a fiscalização e a preparar a chegada do bebê! 👶")
if os.path.exists("pix.jpeg"):
    st.sidebar.image("pix.jpeg", use_container_width=True)
st.sidebar.code("mzoiqcorp@gmail.com", language="text")
