import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistema Explore - Cloud", layout="wide")

st.title("💡 Sistema de Orçamentos - Explore Iluminação")

# URL da sua planilha (https://docs.google.com/spreadsheets/d/1HgvtSwXxjnKAhEKvbscz4QXoi3CFz7Y1wjWbKIREgHc/edit?gid=0#gid=0)
url_planilha = "COLE_O_LINK_DA_SUA_PLANILHA_AQUI"

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados
def buscar_dados():
    return conn.read(spreadsheet=url_planilha, usecols=[0,1,2,3,4], ttl=0)

# 1. Carregar dados atuais
if 'dados' not in st.session_state:
    try:
        st.session_state.dados = buscar_dados()
    except:
        st.session_state.dados = pd.DataFrame(columns=["descricao", "qnt", "preco_venda", "preco_custo", "foto"])

st.subheader("📦 Gestão de Produtos (Sincronizado com Google Sheets)")

# 2. Tabela Editável
df_editavel = st.data_editor(
    st.session_state.dados,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_google"
)

# 3. Botão de Salvar
if st.button("☁️ Sincronizar e Salvar na Nuvem"):
    try:
        conn.update(spreadsheet=url_planilha, data=df_editavel)
        st.success("Dados salvos na Planilha Google!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}. Verifique se a planilha está como 'Editor'.")

st.divider()
st.info("Esta ferramenta agora salva os dados online. A outra pessoa poderá acessar assim que fizermos o link!")