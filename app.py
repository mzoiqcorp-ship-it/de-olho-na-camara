import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Interface Limpa)
st.set_page_config(page_title="De Olho na Câmara", page_icon="🔎", layout="wide")

# CSS para ajustar margens no celular
st.markdown("""
    <style>
    .stApp { margin-bottom: 50px; }
    div.stButton > button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔎 De Olho na Câmara")
st.markdown("### O monitor de gastos oficial do cidadão brasileiro")

# 2. LISTA DE DEPUTADOS (Para o Top 5 ser rápido)
LISTA_ALVOS = [
    178887, 204528, 74328, 204507, 141450, 160511, 178957, 178901, 133439, 178881,
    204554, 204421, 178996, 178927, 178937, 178882, 204454, 204465, 204471, 178909
]

# 3. FUNÇÕES DE DADOS (Com Cache para não travar)
@st.cache_data(ttl=3600)
def buscar_ranking_automatico():
    ranking = []
    agora = datetime.now()
    
    # Lógica Inteligente: Se for antes do dia 10, pega o mês anterior (dados consolidados)
    if agora.day < 10:
        if agora.month == 1:
            mes_busca, ano_busca = 12, agora.year - 1
        else:
            mes_busca, ano_busca = agora.month - 1, agora.year
    else:
        mes_busca, ano_busca = agora.month, agora.year

    url_deps = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    try:
        res_deps = requests.get(url_deps).json()['dados']
        dict_nomes = {d['id']: d['nome'] for d in res_deps if d['id'] in LISTA_ALVOS}

        for id_dep in LISTA_ALVOS:
            url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}/despesas?ano={ano_busca}&mes={mes_busca}&ordem=DESC"
            res = requests.get(url).json()
            if res['dados']:
                total = sum(d['valorDocumento'] for d in res['dados'])
                ranking.append({"nome": dict_nomes.get(id_dep, "Deputado"), "total": total, "id": id_dep, "mes": mes_busca})
    except:
        return []
    
    return sorted(ranking, key=lambda x: x['total'], reverse=True)[:5]

@st.cache_data
def get_lista_completa():
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    try:
        df = pd.DataFrame(requests.get(url).json()['dados'])
        df['Busca'] = df['nome'] + " - " + df['siglaPartido'] + "/" + df['siglaUf']
        return df
    except:
        return pd.DataFrame()

# 4. EXIBIÇÃO DO TOP 5 (DASHBOARD)
st.subheader("🔥 Ranking de Gastos (Automático)")

with st.spinner("Analisando dados oficiais da Câmara..."):
    top_5 = buscar_ranking_automatico()

if top_5:
    mes_ref = top_5[0]['mes']
    st.caption(f"📅 Dados referentes ao mês {mes_ref}/{datetime.now().year}")
    cols = st.columns(5)
    for i, dep_top in enumerate(top_5):
        with cols[i]:
            st.metric(label=dep_top['nome'], value=f"R$ {dep_top['total']:,.2f}")
            if st.button(f"🔎 Ver Detalhes", key=f"btn_{dep_top['id']}"):
                st.session_state.id_manual = dep_top['id']
                st.session_state.nome_manual = dep_top['nome']
else:
    st.info("Ainda processando dados deste mês. Tente a busca manual abaixo.")

st.markdown("---")

# 5. BUSCA MANUAL (Filtros)
st.subheader("🕵️ Fiscalize seu Deputado")
df_all = get_lista_completa()

if not df_all.empty:
    col1, col2 = st.columns(2)
    with col1:
        lista_ufs = ["Todos"] + sorted(list(df_all['siglaUf'].unique()))
        uf_sel = st.selectbox("Filtrar por Estado:", lista_ufs)

    with col2:
        df_filtrado = df_all if uf_sel == "Todos" else df_all[df_all['siglaUf'] == uf_sel]
        lista_deps = ["Selecione..."] + list(df_filtrado['Busca'])
        dep_sel = st.selectbox("Escolha o Parlamentar:", lista_deps)

    # Lógica de seleção (Botão do Top 5 ou Selectbox)
    id_final = None
    if dep_sel != "Selecione...":
        id_final = df_all[df_all['Busca'] == dep_sel]['id'].values[0]
        # Limpa o estado do botão se o usuário usou o selectbox
        if 'id_manual' in st.session_state:
            del st.session_state['id_manual']
    elif 'id_manual' in st.session_state:
        id_final = st.session_state.id_manual
        st.write(f"### 📋 Extrato de: {st.session_state.nome_manual}")

    # 6. TABELA DE RESULTADOS
    if id_final:
        url_final = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_final}/despesas?ordem=DESC&itens=50"
        try:
            dados_finais = requests.get(url_final).json()['dados']
            if dados_finais:
                df_f = pd.DataFrame(dados_finais)[['dataDocumento', 'tipoDespesa', 'nomeFornecedor', 'valorDocumento', 'urlDocumento']]
                df_f.columns = ['Data', 'Tipo', 'Fornecedor', 'Valor (R$)', 'Nota Fiscal']
                st.dataframe(df_f, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhuma despesa recente encontrada.")
        except:
            st.error("Erro ao buscar detalhes. A API da Câmara pode estar instável.")

# -------------------------------------------------------------------
# 📱 ÁREA DE DOAÇÃO (NO FINAL DA PÁGINA)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("☕ Apoie este Projeto Independente")
st.write("Sou um desenvolvedor de Goiânia e criei este monitor nas horas vagas (entre os turnos da madrugada) para trazer transparência ao Brasil.")
st.write("Se o site foi útil pra você, qualquer ajuda para manter o servidor e o enxoval do meu bebê é bem-vinda! 👶💙")

col_pix_img, col_pix_info = st.columns([1, 2])

with col_pix_img:
    # Se você tiver a imagem 'pix.jpeg' na pasta, ela aparece aqui
    if os.path.exists("pix.jpeg"):
        st.image("pix.jpeg", caption="Escaneie no App do Banco", use_container_width=True)
    else:
        st.info("📷 QR Code")

with col_pix_info:
    st.success("Chave Pix (E-mail):")
    st.code("mzoiqcorp@gmail.com", language="text")
    st.caption("👆 Clique no ícone ao lado para copiar a chave.")
    
st.markdown("---")
st.caption("Desenvolvido por Matheus 'Boladão' | Dados Oficiais da Câmara dos Deputados")
