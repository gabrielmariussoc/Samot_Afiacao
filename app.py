import pandas as pd
import streamlit as st

st.title("📦 Consolidador de Relatórios Matrix")

st.write("""
Este sistema permite:
1. Carregar o **CSV consolidado anterior**
2. Carregar o **novo relatório Excel** do Matrix
3. Tratar o Excel automaticamente (linha 3 como cabeçalho)
4. Juntar tudo e baixar o novo CSV consolidado
""")

# ----------------------
# FUNÇÃO DE TRATAMENTO
# ----------------------
def tratar_relatorio_matrix(arquivo_excel):
    # Lê usando linha 3 como cabeçalho
    df = pd.read_excel(arquivo_excel, header=2)

    # Remove colunas vazias
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Padroniza nomes das colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
        .str.replace(' ', '_')
    )

    # Remove linhas totalmente vazias
    df = df.dropna(how='all')

    return df


# ----------------------
# UPLOAD DO CSV ANTIGO
# ----------------------
csv_antigo = st.file_uploader("📁 Envie o CSV consolidado anterior", type=["csv"])

# ----------------------
# UPLOAD DO EXCEL NOVO
# ----------------------
excel_novo = st.file_uploader("📄 Envie o novo relatório Excel do Matrix", type=["xlsx"])


if csv_antigo and excel_novo:
    st.success("Arquivos carregados! Agora vamos processar.")

    # Lê o CSV antigo
    df_antigo = pd.read_csv(csv_antigo)

    # Trata o Excel novo
    df_novo = tratar_relatorio_matrix(excel_novo)

    # Junta os dois
    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)

    st.write("### 🔍 Prévia dos dados tratados:")
    st.dataframe(df_final.head())

    # Botão para baixar o novo consolidado
    csv_final = df_final.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Baixar novo CSV consolidado",
        data=csv_final,
        file_name="consolidado_matrix.csv",
        mime="text/csv"
    )

else:
    st.info("Envie os dois arquivos para continuar.")
