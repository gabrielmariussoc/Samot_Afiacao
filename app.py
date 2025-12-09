import pandas as pd
import streamlit as st
from datetime import datetime
import re
import io
import chardet

# ----------------------
# SISTEMA DE LOGIN SIMPLES
# ----------------------
def autenticar():
    st.markdown("### 🔐 Login necessário")

    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")

    if st.button("Entrar"):
        if usuario == "afiacao" and senha == "123@abc":
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# Se não estiver logado, chama tela de login
if "logado" not in st.session_state or not st.session_state["logado"]:
    autenticar()
    st.stop()

# ----------------------
# TÍTULO
# ----------------------
st.title("📦 Consolidador de Relatórios Matrix")

st.write("""
Este sistema permite:
1. Carregar o **CSV consolidado anterior**
2. Carregar o **novo relatório Excel** do Matrix
3. Validar a data do relatório (segunda linha do arquivo)
4. Juntar tudo e baixar o novo CSV consolidado
""")

# -----------------------------
# MAPA DE RENOMEAÇÃO DE COLUNAS
# -----------------------------
mapa_colunas = {
    "Chave  do": "Chave",
    "Caracteristi cas": "Caracteristicas",
    "Código do  item": "Código do item",
    "Código item  adicional": "Código item adicional",
    "Taman hoPac": "Tamanho pacote",
    "Tipo de  embalagem.": "Tipo de embalagem",
    "Descrição completa do  item": "Descrição completa do item",
    "Nome da  aplicação": "Nome da aplicação",
    "Família  principal": "Família principal",
    "Unidade  de": "Unidade",
    "Nível de  gerenciamento": "Nível de gerenciamento",
    "QDE do  pedido": "Qtd pedido",
    "Fornecedor  principal": "Fornecedor principal",
    "Código do item  do fornecedor": "Código do item do fornecedor",
    "Grupo de  autorização": "Grupo de autorização",
    "Preço do  item": "Preço do item",
    "Preço do  retrabalho": "Preço do retrabalho",
    "Custo  médio": "Custo médio",
    "Preço Liq. do  fornecedor": "Preço líquido do fornecedor",
    "Preço do  fornecedor": "Preço do fornecedor",
    "Numero de  fornecedores": "Número de fornecedores",
    "Média de  consumo": "Média de consumo",
    "Ignorar Limite  de Centro de": "Ignorar limite de centro",
    "Adicional Item  1": "Adicional item 1",
    "Adicional Item  2": "Adicional item 2",
    "Adicional Item  3": "Adicional item 3",
    "Adicional Item  4": "Adicional item 4",
    "Adicional Item  5": "Adicional item 5",
}

# ----------------------
# FUNÇÃO DE TRATAMENTO DO EXCEL
# ----------------------
def tratar_relatorio_matrix(arquivo_excel):

    # Lê o arquivo bruto (para pegar a data)
    df_raw = pd.read_excel(arquivo_excel, header=None)

    # Linha 2 (índice 1), exemplo:
    # "Produzido em : 02/12/2025 08:14:27, Por: Andre"
    linha_data = str(df_raw.iloc[1, 0]).strip()

    match = re.search(r"(\d{2}/\d{2}/\d{4})", linha_data)

    if not match:
        st.error(f"❌ Não foi possível localizar data válida na segunda linha.\nTexto: {linha_data}")
        st.stop()

    data_str = match.group(1)

    try:
        data_relatorio = datetime.strptime(data_str, "%d/%m/%Y")
    except:
        st.error("❌ A data encontrada não pôde ser convertida: " + data_str)
        st.stop()

    # Verifica se é o relatório do dia
    hoje = datetime.now().date()
    if data_relatorio.date() != hoje:
        st.error(f"❌ O relatório enviado é do dia **{data_relatorio.date()}**, mas hoje é **{hoje}**.\n"
                 "Gere o relatório atualizado no Matrix.")
        st.stop()

    # Lê o arquivo correto com cabeçalho na linha 3
    df = pd.read_excel(arquivo_excel, header=2)

    # Remove colunas Unnamed
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Renomeia colunas
    colunas_novas = {}
    for col in df.columns:
        col_limpa = col.strip()
        if col_limpa in mapa_colunas:
            colunas_novas[col] = mapa_colunas[col_limpa]
        else:
            colunas_novas[col] = col_limpa

    df = df.rename(columns=colunas_novas)

    # Remove linhas vazias
    df = df.dropna(how="all")

    # Cria coluna Data relatorio
    df["Data relatorio"] = data_relatorio.date()

    return df

# ----------------------
# UPLOAD DO CSV ANTIGO
# ----------------------
csv_antigo = st.file_uploader("📁 Envie o CSV consolidado anterior", type=["csv"])

# ----------------------
# UPLOAD DO EXCEL NOVO
# ----------------------
excel_novo = st.file_uploader("📄 Envie o novo relatório Excel do Matrix", type=["xlsx"])


# ----------------------
# PROCESSAMENTO GERAL
# ----------------------
if csv_antigo and excel_novo:

    st.success("Arquivos carregados! Processando...")

    # Função para ler CSV com fallback de encoding
    def ler_csv_com_encoding(streamlit_file):
        raw_bytes = streamlit_file.read()

        # Detecta encoding
        det = chardet.detect(raw_bytes)
        encoding_detectado = det.get("encoding", "latin1")

        try:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding_detectado, sep=";")
        except:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding="latin1", sep=";")

    # Lê o CSV antigo
    df_antigo = ler_csv_com_encoding(csv_antigo)

    # ---------------------------------------------------
    # 🔍 VALIDAÇÃO DAS COLUNAS OBRIGATÓRIAS DO CSV ANTIGO
    # ---------------------------------------------------
    colunas_obrigatorias = [
        "Chave","Caracteristicas","Grupo","Código do item","Código item adicional",
        "Descrição do item","Tamanho pacote","Tipo de embalagem","Tipo de item",
        "Descrição completa do item","Nome da aplicação","Família principal","Sub família",
        "Unidade","Nível de gerenciamento","Estoque","Qtd pedido","Fornecedor principal",
        "Código do item do fornecedor","Grupo de autorização","Preço do item",
        "Preço do retrabalho","Custo médio","Preço líquido do fornecedor",
        "Preço do fornecedor","Consignação","Código de barras","Especial","Série",
        "Número de fornecedores","Notas","Média de consumo","Ignorar limite de centro",
        "Adicional item 1","Adicional item 2","Adicional item 3","Adicional item 4",
        "Adicional item 5","Data relatorio"
    ]

    colunas_csv = df_antigo.columns.tolist()
    faltando = [c for c in colunas_obrigatorias if c not in colunas_csv]

    if faltando:
        st.error(
            "❌ O arquivo CSV enviado é inválido!\n\n"
            "As seguintes colunas obrigatórias NÃO foram encontradas:\n\n"
            + "\n".join(f"- {c}" for c in faltando)
            + "\n\nPor favor, envie o CSV consolidado correto."
        )
        st.stop()

    # Lê e trata o Excel novo
    df_novo = tratar_relatorio_matrix(excel_novo)

    # Concatena
    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)

    st.write("### 🔍 Prévia dos dados tratados:")
    st.dataframe(df_final.head())

    csv_final = df_final.to_csv(index=False, sep=";").encode("utf-8")

    st.download_button(
        label="⬇ Baixar novo CSV consolidado",
        data=csv_final,
        file_name="consolidado_matrix.csv",
        mime="text/csv"
    )

else:
    st.info("Envie os dois arquivos para continuar.")
