# 📦 Consolidador de Relatórios Matrix  
Aplicação desenvolvida em **Python + Streamlit** para automatizar o tratamento e consolidação diária dos relatórios gerados pelo sistema Matrix (controle de estoque).

---

## 🚀 Sobre o projeto
O objetivo desta aplicação é facilitar o processo de consolidação dos relatórios diários exportados do Matrix.  
Antes, era necessário copiar e colar manualmente os dados em uma planilha única — agora o processo é totalmente automatizado.

Com a aplicação, o usuário:

- Faz upload do **CSV consolidado anterior**
- Envia o **novo relatório Excel do Matrix**
- O sistema:
  - Lê o cabeçalho correto (linha 3)
  - Remove colunas “Unnamed”
  - Padroniza nomes das colunas
  - Limpa linhas vazias
  - Junta os dados automaticamente
- E disponibiliza um **novo CSV consolidado** para download

Ideal para alimentar um **Power BI** que dependa de dados históricos de estoque.

---

## 🛠 Tecnologias utilizadas
- **Python 3**
- **Streamlit**
- **Pandas**
- **OpenPyXL**

---

## 📂 Estrutura do projeto
