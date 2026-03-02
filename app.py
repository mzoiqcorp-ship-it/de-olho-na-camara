import streamlit as st
import requests
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="De Olho na Câmara", 
    page_icon="🔎", 
    layout="wide"
)

# Estilização básica para melhorar o visual
st.title("🔎 De Olho na Câmara")
st.markdown("### Monitor de Gastos dos Deputados Federais (Dados Oficiais)")
st.write("Fiscalização em tempo real das notas fiscais e reembolsos parlamentares.")

# 2. FUNÇÕES DE PESQUISA (API DA CÂMARA)
@st.cache_data 
def buscar_todos_deputados():
    """Puxa a lista de todos os 513 deputados federais."""
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    resposta = requests.get(url).json()
    return pd.DataFrame(resposta['dados'])

@st.cache_data(ttl=3600) 
def buscar_despesas(id_deputado):
    """Puxa os últimos 100 gastos registados pelo deputado."""
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas?ordem=DESC&ordenarPor=dataDocumento&itens=100"
    resposta = requests.get(url).json()
    if resposta['dados']:
        return pd.DataFrame(resposta['dados'])
    return pd.DataFrame()

# 3. CARREGAMENTO DOS DADOS
try:
    df_deputados = buscar_todos_deputados()
    # Cria uma coluna amigável para a busca
    df_deputados['Busca'] = df_deputados['nome'] + " - " + df_deputados['siglaPartido'] + "/" + df_deputados['siglaUf']
except Exception as e:
    st.error(f"Erro ao conectar com a API da Câmara: {e}")
    st.stop()

# 4. INTERFACE DE FILTROS
st.subheader("🕵️ Escolha o político para fiscalizar")
col1, col2 = st.columns(2)

with col1:
    lista_estados = sorted(df_deputados['siglaUf'].unique())
    estado_escolhido = st.selectbox("📍 Filtrar por Estado (UF):", ["Todos"] + list(lista_estados))

with col2:
    # Filtra a lista de nomes baseada no estado escolhido
    df_filtrado = df_deputados
    if estado_escolhido != "Todos":
        df_filtrado = df_deputados[df_deputados['siglaUf'] == estado_escolhido]
    
    deputado_selecionado = st.selectbox("🔍 Nome do Político:", ["Selecione..."] + list(df_filtrado['Busca']))

# 5. EXIBIÇÃO DOS GASTOS
if deputado_selecionado != "Selecione...":
    # Captura o ID do deputado escolhido
    id_escolhido = df_deputados[df_deputados['Busca'] == deputado_selecionado]['id'].values[0]
    
    with st.spinner(f"A carregar as últimas 100 notas de {deputado_selecionado.split(' - ')[0]}..."):
        df_despesas = buscar_despesas(id_escolhido)
        
        if not df_despesas.empty:
            st.markdown("---")
            st.subheader(f"💸 Gastos mais recentes")

            # Tratamento da tabela para o utilizador
            df_mostrar = df_despesas[['dataDocumento', 'tipoDespesa', 'nomeFornecedor', 'valorDocumento', 'urlDocumento']]
            df_mostrar.columns = ['Data', 'Categoria', 'Fornecedor', 'Valor (R$)', 'Link da Nota']
            
            # Ordenar pelo valor mais alto no topo
            df_mostrar = df_mostrar.sort_values(by='Valor (R$)', ascending=False)
            
            # Exibição da tabela interativa
            st.dataframe(
                df_mostrar, 
                use_container_width=True,
                column_config={
                    "Link da Nota": st.column_config.LinkColumn("Ver Recibo Original")
                }
            )
            st.info("💡 Dica: Clique no cabeçalho das colunas para ordenar por data ou valor.")
        else:
            st.warning("Nenhuma despesa declarada nos últimos meses.")

# 6. BARRA LATERAL (DOAÇÕES E PIX)
st.sidebar.header("🚀 De Olho na Câmara")
st.sidebar.write("Projeto independente focado em transparência pública.")
st.sidebar.markdown("---")

st.sidebar.subheader("💰 Apoie o Projeto")
st.sidebar.write("As doações ajudam a manter o sistema online e a preparar a chegada do novo membro da família! 👶")

# Lógica para mostrar o QR Code se o ficheiro existir
caminho_imagem = "pix.jpeg"
if os.path.exists(caminho_imagem):
    st.sidebar.image(caminho_imagem, caption="Aponte a câmara do seu banco", use_container_width=True)
else:
    st.sidebar.warning("⚠️ QR Code (pix.jpeg) não encontrado na pasta.")

st.sidebar.write("**Chave Pix (Copia e Cola):**")
# Chave Pix atualizada
st.sidebar.code("mzoiqcorp@gmail.com", language="text")

st.sidebar.markdown("---")
st.sidebar.caption("Dados extraídos diretamente da API da Câmara dos Deputados.")
