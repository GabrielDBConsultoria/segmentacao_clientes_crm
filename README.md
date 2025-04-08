# 📦 Versão 1.0

## 📘 Documentação de Referência para o Processo de Segmentação e Atualização de Classificação de Clientes

---

## 🎯 Objetivo

O objetivo deste processo é segmentar os clientes com base no volume médio mensal de compras (em KG) e atualizar suas classificações no sistema.  
Além disso, gerar um relatório de alterações para monitorar **upgrades** e **downgrades** nas classificações.

---

## 🏷️ Estrutura da Hierarquia de Classificação

A classificação segue a seguinte hierarquia, onde **CLIENTE A** é o mais alto e **CLIENTE E** é o mais baixo:

1. 🥇 **CLIENTE A** (`clc_codigo = 4`)
2. 🥈 **CLIENTE B** (`clc_codigo = 1`)
3. 🥉 **CLIENTE C** (`clc_codigo = 2`)
4. 🏅 **CLIENTE D** (`clc_codigo = 3`)
5. 🎗️ **CLIENTE E** (`clc_codigo = 5`)

---

## 📊 Critérios de Classificação

A classificação é definida com base na média mensal de peso comprado pelos clientes:

- 🟢 **CLIENTE A:** > 599 KG
- 🔵 **CLIENTE B:** 400 a 599 KG
- 🟡 **CLIENTE C:** 200 a 399 KG
- 🟠 **CLIENTE D:** 80 a 199 KG
- 🔴 **CLIENTE E:** > 0 e < 80 KG

---

## 🔁 Passos do Processo

### 1️⃣ Coleta de Dados

**🔍 Consulta SQL:**

- Extrair os dados necessários das tabelas `pessoa`, `pedidos`, `cliente` e `carteiracli`
- Filtros aplicados:
  - Naturezas de operação: `ped_natcodigo IN ('VEN', 'VES', 'VIN', 'VIS')`
  - Excluir cliente padrão: `ped_pescodigo <> 1`
  - Status do pedido: `ped_stpcodigo = 6`

```sql
SELECT 
    ped.ped_pescodigo, 
    ped.ped_dtemissao, 
    pes.pes_razao, 
    pes.pes_fantasia, 
    ped.ped_pesobruto, 
    pes.pes_clccodigo, 
    cli.cli_cclcodigo, 
    ccl.ccl_desc AS carteira_cliente 
FROM pedidos ped 
JOIN pessoa pes ON ped.ped_pescodigo = pes.pes_codigo 
JOIN cliente cli ON pes.pes_codigo = cli.cli_pescodigo 
LEFT JOIN carteiracli ccl ON cli.cli_cclcodigo = ccl.ccl_codigo 
WHERE 
    ped.ped_natcodigo IN ('VEN', 'VES', 'VIN', 'VIS') 
    AND ped.ped_pescodigo <> 1 
    AND ped.ped_stpcodigo = 6 
    AND ped.ped_dtemissao >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH);
```

---

### 2️⃣ Cálculo da Média Mensal

- 📅 Transformar a data de emissão (`ped_dtemissao`) para o formato `YYYY-MM` a fim de agrupar os dados por mês
- ⚖️ Somar o peso bruto (`ped_pesobruto`) de todos os pedidos por **mês/cliente**
- 🧮 Calcular a média mensal de peso por cliente

---

### 3️⃣ Classificação dos Clientes

- 🧠 Aplicar a lógica de classificação com base nos critérios acima
- 🗂️ Mapear a classificação para o código correspondente na tabela `classificapes`

---

### 4️⃣ Geração de Relatório

- 🔎 Comparar a nova classificação calculada com a classificação atual (`pes_clccodigo`)
- 📈 Identificar:
  - ⬆️ **Upgrade**: Quando o cliente passa para um nível mais alto
  - ⬇️ **Downgrade**: Quando o cliente passa para um nível mais baixo
- 🧾 Gerar um arquivo CSV com:
  - Código do cliente
  - Razão social e nome fantasia
  - Classificação anterior (descrição)
  - Classificação atual (descrição)
  - Tipo de mudança (Upgrade/Downgrade)

---

### 5️⃣ Geração do Script SQL

Criar um arquivo `.sql` contendo os comandos `UPDATE` para atualizar as classificações no banco de dados:

```sql
UPDATE pessoa 
SET pes_clccodigo = <nova_clc_codigo> 
WHERE pes_codigo = <ped_pescodigo>;
```

---

## 📁 Arquivos Gerados

### 📄 1. Relatório CSV (`Relatorio_Alteracoes_Classificacao.xlsx`)

Contém clientes cuja classificação foi alterada.  
Colunas:

- `ped_pescodigo`: Código do cliente
- `pes_razao`: Razão social
- `pes_fantasia`: Nome fantasia
- `desc_clc_atual`: Descrição da classificação anterior
- `desc_clc_nova`: Descrição da nova classificação
- `mudanca`: Tipo de mudança (Upgrade/Downgrade)

### 💾 2. Script SQL (`atualizar_classificacao.sql`)

Comandos para atualizar as classificações no banco de dados.

---

## 🔄 Fluxo do Processo

1. ▶️ Execute o código Python para:
   - Realizar a segmentação
   - Gerar o relatório e o script SQL
2. 🧐 Analise o arquivo `Relatorio_Alteracoes_Classificacao.xlsx` para verificar as mudanças de classificação
3. 🛠️ Execute o arquivo `atualizar_classificacao.sql` no MySQL Administrator para aplicar as alterações no banco de dados

---

## 📝 Considerações Finais

- 📆 **Periodicidade:** Este processo deve ser executado mensalmente
- ✅ **Validação:** Sempre validar o relatório gerado antes de executar o script SQL
- 🧰 **Manutenção:** Caso a hierarquia ou os critérios de classificação mudem, ajuste o código Python correspondente

---

## 👥 Responsáveis

- 🧑‍💻 Execução do processo: [Nome do responsável atual]
- 📊 Validação de dados: [Nome do validador]
- 🛠️ Manutenção do código: Gabriel Delucca Barros Consultoria

---

## ⚙️ Recursos Necessários

### 💻 Ambiente

- Python instalado com bibliotecas: `pandas`, `pyodbc`, `openpyxl`
- Banco de dados MySQL com acesso às tabelas `pessoa`, `pedidos` e `classificapes`

### 🔌 DSN configurado

- Nome do DSN: `segvojoana`

---

## 📚 Referências

### 📁 Tabela `classificapes`

- Contém a hierarquia de classificação
- Campos principais:
  - `clc_codigo`: Código da classificação
  - `clc_desc`: Descrição da classificação

### 📁 Tabela `pessoa`

- Contém as classificações atuais dos clientes
- Campos principais:
  - `pes_clccodigo`: Classificação atual do cliente
  - `pes_codigo`: Código do cliente

### 📁 Tabela `cliente`

- Contém os códigos de clientes e carteiras atuais dos clientes
- Campos principais:
  - `cli_cclcodigo`: Código da carteira do cliente
  - `cli_pescodigo`: Código do cliente

### 📁 Tabela `carteiracli`

- Contém as carteiras atuais dos clientes
- Campos principais:
  - `ccl_codigo`: Código da carteira do cliente
  - `ccl_desc`: Descrição da carteira do cliente

