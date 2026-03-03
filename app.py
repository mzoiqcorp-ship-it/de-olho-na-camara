import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="De Olho na Câmara", page_icon="🔎", layout="wide")

# Estilização básica
st.title("🔎 De Olho na Câmara")
st.markdown("### O monitor de gastos oficial do cidadão brasileiro")

# 2. LISTA DE IDs DE DEPUTADOS PARA MONITORAMENTO DO TOP 5
# Selecionamos 20 que costumam usar a cota de forma intensa para o ranking ser veloz
LISTA_ALVOS = [
    178887, 204528, 74328, 204507, 141450, 160511, 178957, 178901, 133439, 178881,
    204554, 204421, 178996, 178927, 178937, 178882, 204454, 204465, 204471, 178909
]

# 3. FUNÇÕES DE DADOS (COM CACHE PARA VELOCIDADE)
@st.cache_data(ttl=3600)
def buscar_ranking_automatico():
    ranking = []
    agora = datetime.now()
    # Lógica: Se for antes do dia 10, olhamos o mês anterior (dados mais completos)
    if agora.day < 10:
        if agora.month == 1:
            mes_busca, ano_busca = 12, agora.year - 1
        else:
            mes_busca, ano_busca = agora.month - 1, agora.year
    else:
        mes_busca, ano_busca = agora.month, agora.year

    # Busca nomes para o dicionário
    url_deps = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    res_deps = requests.get(url_deps).json()['dados']
    dict_nomes = {d['id']: d['nome'] for d in res_deps if d['id'] in LISTA_ALVOS}

    for id_dep in LISTA_ALVOS:
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}/despesas?ano={ano_busca}&mes={mes_busca}&ordem=DESC"
        try:
            res = requests.get(url).json()
            if res['dados']:
                total = sum(d['valorDocumento'] for d in res['dados'])
                ranking.append({"nome": dict_nomes.get(id_dep, "Deputado"), "total": total, "id": id_dep, "mes": mes_busca})
        except:
            continue
    
    return sorted(ranking, key=lambda x: x['total'], reverse=True)[:5]

@st.cache_data
def get_lista_completa():
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    df = pd.DataFrame(requests.get(url).json()['dados'])
    df['Busca'] = df['nome'] + " - " + df['siglaPartido'] + "/" + df['siglaUf']
    return df

# 4. EXIBIÇÃO DO TOP 5 (DASHBOARD)
st.subheader("🔥 Top 5 Maiores Gastos (Mês de Referência)")

with st.spinner("Minerando dados da Câmara..."):
    top_5 = buscar_ranking_automatico()

if top_5:
    mes_ref = top_5[0]['mes']
    st.caption(f"Dados consolidados referentes ao mês {mes_ref}/2026")
    cols = st.columns(5)
    for i, dep_top in enumerate(top_5):
        with cols[i]:
            st.metric(label=dep_top['nome'], value=f"R$ {dep_top['total']:,.2f}")
            if st.button(f"🔎 Fiscalizar", key=f"btn_{dep_top['id']}"):
                st.session_state.id_manual = dep_top['id']
                st.session_state.nome_manual = dep_top['nome']

st.markdown("---")

# 5. BUSCA MANUAL POR ESTADO
st.subheader("🕵️ Busca Detalhada por Político")
df_all = get_lista_completa()

col1, col2 = st.columns(2)
with col1:
    lista_ufs = ["Todos"] + sorted(list(df_all['siglaUf'].unique()))
    uf_sel = st.selectbox("Filtrar por Estado:", lista_ufs)

with col2:
    df_filtrado = df_all if uf_sel == "Todos" else df_all[df_all['siglaUf'] == uf_sel]
    lista_deps = ["Selecione..."] + list(df_filtrado['Busca'])
    dep_sel = st.selectbox("Escolha o Deputado:", lista_deps)

# 6. MOSTRAR TABELA DE GASTOS
id_final = None
if dep_sel != "Selecione...":
    id_final = df_all[df_all['Busca'] == dep_sel]['id'].values[0]
elif 'id_manual' in st.session_state:
    id_final = st.session_state.id_manual

if id_final:
    url_final = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_final}/despesas?ordem=DESC&itens=100"
    dados_finais = requests.get(url_final).json()['dados']
    
    if dados_finais:
        df_f = pd.DataFrame(dados_finais)[['dataDocumento', 'tipoDespesa', 'nomeFornecedor', 'valorDocumento', 'urlDocumento']]
        df_f.columns = ['Data', 'Tipo de Gasto', 'Fornecedor', 'Valor (R$)', 'Link da Nota']
        st.write(f"### Exibindo últimas notas fiscais")
        st.dataframe(df_f.sort_values(by="Valor (R$)", ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado de despesa encontrado para este parlamentar.")

# 7. BARRA LATERAL (APOIO)
st.sidebar.header("🚀 Apoie o Monitor")
st.sidebar.write("Ajude um desenvolvedor independente de Goiânia a manter este servidor e preparar o enxoval do bebê! 👶")
if os.path.exists("pix.jpeg"):
    st.sidebar.image("pix.jpeg", use_container_width=True)
st.sidebar.write("**Chave Pix:**")
st.sidebar.code("mzoiqcorp@gmail.com", language="text")
st.sidebar.markdown("---")
st.sidebar.caption("v2.0 - Dados Abertos Câmara")
