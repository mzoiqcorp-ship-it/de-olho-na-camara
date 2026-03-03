import streamlit as st
import requests
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="De Olho na Câmara", page_icon="🔎", layout="wide")

# Estilização
st.title("🔎 De Olho na Câmara")
st.markdown("### Monitor de Gastos dos Deputados Federais")

# 2. FUNÇÕES DE BUSCA (API)
@st.cache_data 
def buscar_todos_deputados():
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    res = requests.get(url).json()
    return pd.DataFrame(res['dados'])

@st.cache_data(ttl=3600) 
def buscar_despesas(id_deputado):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas?ordem=DESC&ordenarPor=dataDocumento&itens=100"
    res = requests.get(url).json()
    return pd.DataFrame(res['dados']) if res['dados'] else pd.DataFrame()

# Carregamento Inicial
df_deputados = buscar_todos_deputados()
df_deputados['Busca'] = df_deputados['nome'] + " - " + df_deputados['siglaPartido'] + "/" + df_deputados['siglaUf']

# -------------------------------------------------------------------
# 🚀 NOVA SEÇÃO: TOP 5 / FISCALIZAÇÃO EM DESTAQUE
# -------------------------------------------------------------------
st.subheader("🔥 Fiscalização em Destaque (Casos que chamam a atenção)")
st.info("Clique nos botões abaixo para ver os gastos suspeitos encontrados pela nossa comunidade.")

col_dest1, col_dest2, col_dest3 = st.columns(3)

# Destaque 1: Acácio Favacho
with col_dest1:
    if st.button("🚨 Acácio Favacho (R$ 30k em 1 dia)"):
        st.session_state.deputado_selecionado = "Acácio Favacho - MDB/AP"
        st.session_state.uf_selecionada = "AP"

# Destaque 2: General Girão
with col_dest2:
    if st.button("📱 General Girão (Marketing Sem Fim)"):
        st.session_state.deputado_selecionado = "General Girão - PL/RN"
        st.session_state.uf_selecionada = "RN"

# Destaque 3: Gustavo Gayer
with col_dest3:
    if st.button("📍 Gustavo Gayer (Destaque Goiás)"):
        st.session_state.deputado_selecionado = "Gustavo Gayer - PL/GO"
        st.session_state.uf_selecionada = "GO"

st.markdown("---")

# -------------------------------------------------------------------
# 3. INTERFACE DE BUSCA MANUAL
# -------------------------------------------------------------------
st.subheader("🕵️ Escolha o político para fiscalizar")

# Gerenciamento de estado para os botões funcionarem
if 'uf_selecionada' not in st.session_state: st.session_state.uf_selecionada = "Todos"
if 'deputado_selecionado' not in st.session_state: st.session_state.deputado_selecionado = "Selecione..."

col1, col2 = st.columns(2)

with col1:
    lista_ufs = ["Todos"] + sorted(list(df_deputados['siglaUf'].unique()))
    uf = st.selectbox("📍 Filtrar por Estado (UF):", lista_ufs, 
                      index=lista_ufs.index(st.session_state.uf_selecionada), key="uf_box")
    st.session_state.uf_selecionada = uf

with col2:
    df_filtrado = df_deputados if uf == "Todos" else df_deputados[df_deputados['siglaUf'] == uf]
    lista_deps = ["Selecione..."] + list(df_filtrado['Busca'])
    
    # Verifica se o deputado do destaque está na lista filtrada
    default_index = 0
    if st.session_state.deputado_selecionado in lista_deps:
        default_index = lista_deps.index(st.session_state.deputado_selecionado)
        
    dep = st.selectbox("🔍 Nome do Político:", lista_deps, index=default_index, key="dep_box")
    st.session_state.deputado_selecionado = dep

# 4. EXIBIÇÃO DOS DADOS
if st.session_state.deputado_selecionado != "Selecione...":
    id_escolhido = df_deputados[df_deputados['Busca'] == st.session_state.deputado_selecionado]['id'].values[0]
    df_despesas = buscar_despesas(id_escolhido)
    
    if not df_despesas.empty:
        st.markdown(f"#### 💸 Últimas 100 notas de {st.session_state.deputado_selecionado}")
        df_mostrar = df_despesas[['dataDocumento', 'tipoDespesa', 'nomeFornecedor', 'valorDocumento', 'urlDocumento']]
        df_mostrar.columns = ['Data', 'Categoria', 'Fornecedor', 'Valor (R$)', 'Link']
        st.dataframe(df_mostrar.sort_values(by='Valor (R$)', ascending=False), use_container_width=True)
    else:
        st.warning("Nenhuma despesa recente encontrada.")

# 5. BARRA LATERAL (APOIO)
st.sidebar.header("🚀 Apoie o Projeto")
st.sidebar.write("Ajude a manter a fiscalização e a preparar a chegada do bebê! 👶")
if os.path.exists("pix.jpeg"):
    st.sidebar.image("pix.jpeg", caption="Aponte a câmera do seu banco", use_container_width=True)
st.sidebar.write("**Chave Pix (Copia e Cola):**")
st.sidebar.code("mzoiqcorp@gmail.com", language="text")
st.sidebar.markdown("---")
st.sidebar.caption("Dados Oficiais - API Câmara dos Deputados")
