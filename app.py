import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Explore Iluminação", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS (CORRIGIDO COM ASPAS) ---
url_planilha = "https://docs.google.com/spreadsheets/d/1HgvtSwXxjnKAhEKvbscz4QXoi3CFz7Y1wjWbKIREgHc/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def buscar_dados():
    # ttl=0 garante que ele sempre pegue o dado mais atual da planilha
    return conn.read(spreadsheet=url_planilha, ttl=0)

# Inicializar dados na sessão
if 'dados' not in st.session_state:
    try:
        st.session_state.dados = buscar_dados()
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        st.session_state.dados = pd.DataFrame(columns=["descricao", "qnt", "preco_venda", "preco_custo", "foto"])

st.title("💡 Sistema de Orçamentos - Explore")

# --- ABA DE GESTÃO ---
st.subheader("📦 Banco de Dados Online")
df_editavel = st.data_editor(
    st.session_state.dados,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_principal"
)

if st.button("☁️ Sincronizar com Google Sheets"):
    try:
        conn.update(spreadsheet=url_planilha, data=df_editavel)
        st.success("Dados salvos na nuvem com sucesso!")
        st.session_state.dados = df_editavel
    except Exception as e:
        st.error(f"Erro ao salvar: {e}. Verifique se a planilha está compartilhada como EDITOR.")

st.divider()

# --- GERADOR DE PDF ---
st.subheader("📑 Criar Orçamento para Cliente")
# Verifica se a coluna 'descricao' existe antes de listar
if not df_editavel.empty and "descricao" in df_editavel.columns:
    produtos_pdf = st.multiselect("Selecione os produtos para o orçamento:", df_editavel["descricao"].unique())

    if produtos_pdf:
        itens_selecionados = df_editavel[df_editavel["descricao"].isin(produtos_pdf)]
        st.write("### Prévia do Orçamento")
        # Exibe apenas o que interessa ao cliente
        colunas_cliente = [c for c in ["descricao", "qnt", "preco_venda"] if c in itens_selecionados.columns]
        st.table(itens_selecionados[colunas_cliente])

        if st.button("🖨️ Baixar Orçamento em PDF"):
            try:
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
                    pdf.cell(100, 10, str(row.get('descricao', '')))
                    pdf.cell(30, 10, str(row.get('qnt', 0)))
                    preco = row.get('preco_venda', 0)
                    pdf.cell(40, 10, f"R$ {float(preco):.2f}")
                    pdf.ln()
                    total_geral += (int(row.get('qnt', 0)) * float(preco))
                    
                pdf.ln(10)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(200, 10, f"TOTAL GERAL: R$ {total_geral:.2f}", ln=True, align="R")
                
                # Gera o PDF em modo binário
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("Clique aqui para baixar o PDF", data=pdf_output, file_name="orcamento.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
else:
    st.warning("Adicione produtos na tabela acima primeiro.")
