import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Sistema Explore Iluminação", layout="wide")

# 1. CONEXÃO COM GOOGLE SHEETS
# Substitua pelo link da sua planilha (compartilhada como "Editor")
url_planilha = https://docs.google.com/spreadsheets/d/1HgvtSwXxjnKAhEKvbscz4QXoi3CFz7Y1wjWbKIREgHc/edit?gid=0#gid=0

conn = st.connection("gsheets", type=GSheetsConnection)

def buscar_dados():
    return conn.read(spreadsheet=url_planilha, usecols=[0,1,2,3,4], ttl=0)

# Inicializar dados
if 'dados' not in st.session_state:
    try:
        st.session_state.dados = buscar_dados()
    except:
        st.session_state.dados = pd.DataFrame(columns=["descricao", "qnt", "preco_venda", "preco_custo", "foto"])

st.title("💡 Sistema de Orçamentos - Explore")

# 2. ÁREA DE GESTÃO (BANCO DE DATA)
st.subheader("📦 Banco de Dados Online")
df_editavel = st.data_editor(
    st.session_state.dados,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_principal"
)

if st.button("☁️ Sincronizar com Google Sheets"):
    conn.update(spreadsheet=url_planilha, data=df_editavel)
    st.success("Dados salvos na nuvem com sucesso!")
    st.session_state.dados = df_editavel

st.divider()

# 3. GERADOR DE PDF
st.subheader("📑 Criar Orçamento para Cliente")
produtos_pdf = st.multiselect("Selecione os produtos para o orçamento:", df_editavel["descricao"].unique())

if produtos_pdf:
    itens_selecionados = df_editavel[df_editavel["descricao"].isin(produtos_pdf)]
    st.write("### Prévia do Orçamento")
    # Mostra apenas o que o cliente deve ver (esconde o custo)
    st.table(itens_selecionados[["descricao", "qnt", "preco_venda"]])

    if st.button("🖨️ Baixar Orçamento em PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "EXPLORE ILUMINAÇÃO - ORÇAMENTO", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(100, 10, "Descricao")
        pdf.cell(30, 10, "Qtd")
        pdf.cell(40, 10, "Preco Unit.")
        pdf.ln()
        
        pdf.set_font("Arial", "", 12)
        total_geral = 0
        for index, row in itens_selecionados.iterrows():
            pdf.cell(100, 10, str(row['descricao']))
            pdf.cell(30, 10, str(row['qnt']))
            pdf.cell(40, 10, f"R$ {row['preco_venda']:.2f}")
            pdf.ln()
            total_geral += (row['qnt'] * row['preco_venda'])
            
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"TOTAL GERAL: R$ {total_geral:.2f}", ln=True, align="R")
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("Clique aqui para baixar o PDF", data=pdf_output, file_name="orcamento.pdf", mime="application/pdf")
