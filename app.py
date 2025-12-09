import pandas as pd
import streamlit as st
from datetime import datetime
import re
import io
import chardet
import unicodedata
from io import StringIO

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
# MAPA DE RENOMEAÇÃO DE COLUNAS (seu mapa existente)
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
# FUNÇÕES AUXILIARES
# ----------------------
def normalizar_coluna(nome):
    """Normaliza nome de coluna para comparação: lower, remove acento, underscores, espaços extras."""
    if not isinstance(nome, str):
        return ""
    s = nome.strip().lower()
    s = s.replace("_", " ").replace("-", " ")
    s = " ".join(s.split())  # remove múltiplos espaços
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s

def detectar_delimitador(sample_text):
    """Escolhe delimitador mais provável a partir de uma amostra: compara counts de ; , \t |."""
    counts = {
        ';': sample_text.count(';'),
        ',': sample_text.count(','),
        '\t': sample_text.count('\t'),
        '|': sample_text.count('|')
    }
    # retorna o mais frequente (mínimo 1 ocorrência)
    delim = max(counts, key=counts.get)
    if counts[delim] == 0:
        return ','  # fallback
    return delim

def ler_csv_bytes_robusto(uploaded_file_bytes):
    """
    Tenta decodificar e ler um CSV a partir de bytes. Tenta várias codificações e
    detecta delimitador automaticamente.
    Retorna (df, encoding_used, delim_used)
    """
    # detecta encoding com chardet
    det = chardet.detect(uploaded_file_bytes)
    prov = det.get('encoding')
    encodings_testar = [prov, 'utf-8', 'latin-1', 'cp1252']
    encodings_testar = [e for e in encodings_testar if e is not None]

    # pega uma amostra decodificada para detectar delim
    for enc in encodings_testar:
        try:
            sample = uploaded_file_bytes.decode(enc, errors='replace')
            delim = detectar_delimitador(sample[:5000])
            # tenta ler com pandas a partir da string (mais robusto)
            df = pd.read_csv(StringIO(sample), sep=delim, engine='python')
            return df, enc, delim
        except Exception:
            continue

    # fallback final: usar latin-1 e ; e tentativa com engine python
    try:
        sample = uploaded_file_bytes.decode('latin-1', errors='replace')
        delim = detectar_delimitador(sample[:5000])
        df = pd.read_csv(StringIO(sample), sep=delim, engine='python')
        return df, 'latin-1', delim
    except Exception as e:
        # último recurso: raise com mensagem mais clara
        raise RuntimeError("Não foi possível ler o CSV com as tentativas de encoding/delimitador.") from e

# ----------------------
# FUNÇÃO DE TRATAMENTO DO EXCEL
# ----------------------
def tratar_relatorio_matrix(arquivo_excel):
    df_raw = pd.read_excel(arquivo_excel, header=None)
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

    hoje = datetime.now().date()
    if data_relatorio.date() != hoje:
        st.error(f"❌ O relatório enviado é do dia **{data_relatorio.date()}**, mas hoje é **{hoje}**.\nGere o relatório atualizado no Matrix.")
        st.stop()

    df = pd.read_excel(arquivo_excel, header=2)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Renomeia colunas conforme mapa
    colunas_novas = {}
    for col in df.columns:
        col_limpa = col.strip()
        if col_limpa in mapa_colunas:
            colunas_novas[col] = mapa_colunas[col_limpa]
        else:
            colunas_novas[col] = col_limpa
    df = df.rename(columns=colunas_novas)

    df = df.dropna(how="all")
    df["Data relatorio"] = data_relatorio.date()
    return df

# ----------------------
# UPLOADS
# ----------------------
csv_antigo = st.file_uploader("📁 Envie o CSV consolidado anterior", type=["csv"])
excel_novo = st.file_uploader("📄 Envie o novo relatório Excel do Matrix", type=["xlsx"])

# ----------------------
# PROCESSAMENTO
# ----------------------
if csv_antigo and excel_novo:
    st.success("Arquivos carregados! Processando...")

    # Lê CSV de forma robusta a partir dos bytes
    try:
        raw_bytes = csv_antigo.read()
        df_antigo, enc_used, delim_used = ler_csv_bytes_robusto(raw_bytes)
    except Exception as e:
        st.error("❌ Falha ao ler o CSV. Detalhe: " + str(e))
        st.stop()

    # Debug: mostrar encoding e delimitador detectados e colunas lidas
    # st.info(f"Encoding detectado: {enc_used}  —  Delimitador detectado: '{delim_used}'")
    # st.write("Colunas detectadas no CSV:", df_antigo.columns.tolist())

    # ---------------------------------------------------
    # 🔍 VALIDAÇÃO FLEXÍVEL DAS COLUNAS OBRIGATÓRIAS DO CSV ANTIGO
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

    # normaliza colunas do CSV (remove acento, espaços, lower)
    colunas_csv_normalizadas = [normalizar_coluna(c) for c in df_antigo.columns.tolist()]
    obrig_norm = [normalizar_coluna(c) for c in colunas_obrigatorias]

    # mapeia quais obrigatórias não aparecem
    faltando_idx = [i for i, on in enumerate(obrig_norm) if on not in colunas_csv_normalizadas]
    faltando = [colunas_obrigatorias[i] for i in faltando_idx]

    if faltando:
        st.error(
            "❌ O arquivo CSV enviado é inválido!\n\n"
            "As seguintes colunas obrigatórias NÃO foram encontradas:\n\n"
            + "\n".join(f"- {c}" for c in faltando)
            + "\n\nDicas:\n- Confirme que o arquivo tem delimitador correto (ex: ponto e vírgula ';')\n- Verifique codificação (salve como UTF-8 ou ANSI) e reaplique o upload"
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
