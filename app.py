import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Explore Iluminação", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Verifique se o link abaixo está entre aspas
url_planilha = "https://docs.google.com/spreadsheets/d/1HgvtSwXxjnKAhEKvbscz4QXoi3CFz7Y1wjWbKIREgHc/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def buscar_dados():
    return conn.read(spreadsheet=url_planilha, ttl=0)

if 'dados' not in st.session_state:
    try:
        st.session_state.dados = buscar_dados()
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        st.session_state.dados = pd.DataFrame(columns=["descricao", "qnt", "preco_venda", "preco_custo", "foto"])

st.title("💡 Sistema de Orçamentos - Explore")

# --- ABA DE GESTÃO COM COLUNA TOTAL AUTOMÁTICA ---
st.subheader("📦 Banco de Dados Online")

# Prepara os dados para exibição com a conta do Total
df_visualizacao = st.session_state.dados.copy()
df_visualizacao['qnt'] = pd.to_numeric(df_visualizacao['qnt'], errors='coerce').fillna(0)
df_visualizacao['preco_venda'] = pd.to_numeric(df_visualizacao['preco_venda'], errors='coerce').fillna(0)
df_visualizacao['VALOR TOTAL'] = df_visualizacao['qnt'] * df_visualizacao['preco_venda']

# Tabela interativa
df_editavel = st.data_editor(
    df_visualizacao,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_principal",
    column_config={
        "VALOR TOTAL": st.column_config.NumberColumn("Total (R$)", format="R$ %.2f", disabled=True),
        "preco_venda": st.column_config.NumberColumn("Preço Venda", format="R$ %.2f"),
        "preco_custo": st.column_config.NumberColumn("Preço Custo", format="R$ %.2f"),
    }
)

if st.button("☁️ Sincronizar com Google Sheets"):
    try:
        # Removemos a coluna calculada antes de salvar para não sujar a planilha
        dados_para_salvar = df_editavel.drop(columns=['VALOR TOTAL'])
        conn.update(spreadsheet=url_planilha, data=dados_para_salvar)
        st.success("Dados salvos com sucesso!")
        st.session_state.dados = dados_para_salvar
    except Exception as e:
        st.error(f"Erro ao salvar: {e}. Verifique as permissões da planilha.")

st.divider()

# --- GERADOR DE PDF ---
st.subheader("📑 Criar Orçamento para Cliente")
if not df_editavel.empty and "descricao" in df_editavel.columns:
    produtos_pdf = st.multiselect("Selecione os produtos para o orçamento:", df_editavel["descricao"].unique())

    if produtos_pdf:
        itens_selecionados = df_editavel[df_editavel["descricao"].isin(produtos_pdf)]
        st.write("### Prévia do Orçamento")
        st.table(itens_selecionados[["descricao", "qnt", "preco_venda", "VALOR TOTAL"]])

        if st.button("🖨️ Baixar Orçamento em PDF"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(200, 10, "EXPLORE ILUMINACAO - ORCAMENTO", ln=True, align="C")
                pdf.ln(10)
                
                # Cabeçalho da Tabela no PDF
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(90, 10, "Descricao", border=1)
                pdf.cell(25, 10, "Qtd", border=1, align="C")
                pdf.cell(35, 10, "Unit. (R$)", border=1, align="C")
                pdf.cell(35, 10, "Total (R$)", border=1, align="C")
                pdf.ln()
                
                pdf.set_font("Helvetica", "", 10)
                total_geral = 0
                for index, row in itens_selecionados.iterrows():
                    desc = str(row.get('descricao', 'Sem nome'))[:40]
                    qtd = int(row.get('qnt', 0))
                    preco = float(row.get('preco_venda', 0))
                    subtotal = qtd * preco
                    total_geral += subtotal
                    
                    pdf.cell(90, 10, desc, border=1)
                    pdf.cell(25, 10, str(qtd), border=1, align="C")
                    pdf.cell(35, 10, f"{preco:,.2f}", border=1, align="C")
                    pdf.cell(35, 10, f"{subtotal:,.2f}", border=1, align="C")
                    pdf.ln()
                
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(150, 10, "TOTAL GERAL:", align="R")
                pdf.cell(35, 10, f"R$ {total_geral:,.2f}", align="C")
                
                pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button("📥 Baixar PDF", data=pdf_output, file_name="orcamento.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro no PDF: {e}")
